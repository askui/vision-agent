import base64
import os
from typing import Optional, Union
from urllib.parse import urlencode, urljoin
from uuid import UUID

from askui.tools.askui.askui_workspaces.models.extract_data_command import ExtractDataCommand
from askui.tools.askui.askui_workspaces.models.extract_data_response import ExtractDataResponse

from .askui_workspaces import (
    AgentsApi,
    AgentExecutionsApi,
    SchedulesApi,
    ToolsApi,
    AgentExecutionUpdateCommand,
    Agent,
    AgentExecution,
    AgentExecutionStateCanceled,
    AgentExecutionStateConfirmed,
    AgentExecutionStateDeliveredToDestinationInput,
    AgentExecutionStatePendingReview,
    ApiClient,
    Configuration,
    CreateScheduleRequestDto,
    CreateScheduleResponseDto,
    State1,
)
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class AskUIHubSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ASKUI_",
    )
    workspace_id: str | None = Field(default=None)
    token: str | None = Field(default=None)
    workspaces_endpoint: HttpUrl | None = Field(default=HttpUrl("https://workspaces.askui.com"))
    
    @property
    def workspaces_host(self) -> str:
        if self.workspaces_endpoint is None:
            raise ValueError("Workspaces endpoint is not set")
        return self.workspaces_endpoint.unicode_string().rstrip("/")

    @property
    def authenticated(self) -> bool:
        return self.workspace_id is not None and self.token is not None
    
    @property
    def token_base64(self) -> str:
        if self.token is None:
            raise ValueError("Token is not set")
        return base64.b64encode(self.token.encode()).decode()
    
    @property
    def files_base_url(self) -> str:
        return urljoin(self.workspaces_host, "/api/v1/files")
    
    @property
    def authorization_header_value(self) -> str:
        return f"Basic {self.token_base64}"
    
    

ScheduleRunCommand = CreateScheduleRequestDto
ScheduleRunResponse = CreateScheduleResponseDto


class FileDto(BaseModel):
    name: str
    path: str
    url: str


class FilesListResponseDto(BaseModel):
    data: list[FileDto]
    next_continuation_token: Optional[str] = Field(default=None)


REQUEST_TIMEOUT_IN_S=60
UPLOAD_REQUEST_TIMEOUT_IN_S=3600 # allows for uploading large files
EXTRACT_DATA_REQUEST_TIMEOUT_IN_S=300.0


class AskUIHub:
    def __init__(self):
        self._settings = AskUIHubSettings()
        self.disabled = False
        if not self._settings.authenticated:
            self.disabled = True
            return
        
        api_client_config = Configuration(
            host=self._settings.workspaces_host,
            api_key={"Basic": self._settings.authorization_header_value},
        )
        api_client = ApiClient(api_client_config)
        self._agents_api = AgentsApi(api_client)
        self._agent_executions_api = AgentExecutionsApi(api_client)
        self._schedules_api = SchedulesApi(api_client)
        self._tools_api = ToolsApi(api_client)

    def retrieve_agent(self, agent_id: UUID | str) -> Agent:
        response = self._agents_api.list_agents_api_v1_agents_get(
            agent_id=[str(agent_id)]
        )
        if not response.data:
            raise ValueError(f"Agent {agent_id} not found")
        return response.data[0]

    def retrieve_agent_execution(self, agent_execution_id: UUID | str) -> AgentExecution:
        response = self._agent_executions_api.list_agent_executions_api_v1_agent_executions_get(
            agent_execution_id=[str(agent_execution_id)]
        )
        if not response.data:
            raise ValueError(f"Agent execution {agent_execution_id} not found")
        return response.data[0]

    def update_agent_execution(
        self,
        agent_execution_id: UUID | str,
        state: Union[
            AgentExecutionStateCanceled,
            AgentExecutionStateConfirmed,
            AgentExecutionStatePendingReview,
            AgentExecutionStateDeliveredToDestinationInput,
        ],
    ) -> AgentExecution:
        command = AgentExecutionUpdateCommand(state=State1(state.model_dump()))  # type: ignore
        return self._agent_executions_api.update_agent_execution_api_v1_agent_executions_agent_execution_id_patch(
            agent_execution_id=str(agent_execution_id),
            agent_execution_update_command=command,
        )

    def schedule_run(self, command: ScheduleRunCommand) -> ScheduleRunResponse:
        return self._schedules_api.create_schedule_api_v1_workspaces_workspace_id_schedules_post(
            workspace_id=self._settings.workspace_id,
            create_schedule_request_dto=command,
        )
        
    def extract_data(self, command: ExtractDataCommand) -> ExtractDataResponse:
        return self._tools_api.extract_data_api_v1_tools_extract_data_post(
            extract_data_command=command,
            _request_timeout=EXTRACT_DATA_REQUEST_TIMEOUT_IN_S,
        )

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(), reraise=True
    )
    def _upload_file(
        self, local_file_path: str, remote_file_path: str
    ) -> None:
        with open(local_file_path, "rb") as f:
            url = urljoin(
                base=self._settings.files_base_url,
                url=remote_file_path,
            )
            with requests.put(
                url,
                files={"file": f},
                headers=self._settings.authorization_header_value,
                timeout=UPLOAD_REQUEST_TIMEOUT_IN_S,
                stream=True,
            ) as response:
                if response.status_code != 200:
                    response.raise_for_status()

    def _upload_dir(self, local_dir_path: str, remote_dir_path: str) -> None:
        for root, _, files in os.walk(local_dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_file_path = os.path.relpath(file_path, start=local_dir_path, )
                remote_file_path = (
                    remote_dir_path
                    + ("/" if remote_dir_path != "" else "")
                    + ("/".join(relative_file_path.split(os.sep)))
                )
                self._upload_file(file_path, remote_file_path)

    def upload(self, local_path: str, remote_dir_path: str = "") -> None:
        r_dir_path = remote_dir_path.rstrip("/")
        if os.path.isdir(local_path):
            self._upload_dir(local_path, r_dir_path)
        else:
            self._upload_file(local_path, f"{r_dir_path}/{os.path.basename(local_path)}")

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(), reraise=True
    )
    def _download_file(
        self, url: str, local_file_path: str
    ) -> None: 
        response = requests.get(
            url,
            headers=self._settings.authorization_header_value,
            timeout=REQUEST_TIMEOUT_IN_S,
            stream=True,
        )
        if response.status_code != 200:
            response.raise_for_status()
        with open(local_file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(), reraise=True)
    def _list_objects(
        self, prefix: str, continuation_token: str | None = None
    ) -> FilesListResponseDto:
        params = {"prefix": prefix, "limit": 100, "expand": "url"}
        if continuation_token is not None:
            params["continuation_token"] = continuation_token
        list_url = f"{self._settings.files_base_url}?{urlencode(params)}"
        response = requests.get(list_url, headers=self._settings.authorization_header_value, timeout=REQUEST_TIMEOUT_IN_S)
        if response.status_code != 200:
            response.raise_for_status()
        return FilesListResponseDto(**response.json())

    def download(self, local_dir_path: str, remote_path: str = "") -> None:
        continuation_token = None
        prefix = remote_path.lstrip("/")
        while True:
            list_objects_response = self._list_objects(prefix, continuation_token)
            for content in list_objects_response.data:    
                if prefix == content.path: # is a file
                    relative_remote_path = content.name
                else: # is a prefix, e.g., folder
                    relative_remote_path = content.path[len(prefix) :].lstrip("/")
                local_file_path = os.path.join(
                    local_dir_path, *relative_remote_path.split("/")
                )
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                self._download_file(content.url, local_file_path)
            continuation_token = list_objects_response.next_continuation_token
            if continuation_token is None:
                break
