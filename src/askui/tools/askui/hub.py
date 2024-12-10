import base64
import time
from typing import Any, Union
from uuid import UUID

import askui_workspaces
from askui_workspaces.api.agents_api import AgentsApi
from askui_workspaces.api.agent_executions_api import AgentExecutionsApi
from askui_workspaces.api.schedules_api import SchedulesApi
from askui_workspaces.models import (
    AgentExecutionUpdateCommand,
    Agent,
    AgentExecution,
    AgentExecutionStateCanceled,
    AgentExecutionStateConfirmed,
    AgentExecutionStateDeliveredToDestinationInput,
    AgentExecutionStatePendingReview,
    CreateScheduleRequestDto,
    RunnerHost,
    State1,
)
from enum import Enum

from loguru import logger
from pydantic import BaseModel



class AgentExecutionStatus(str, Enum):
    """Status of an agent execution."""
    PENDING_INPUTS = "PENDING_INPUTS"
    PENDING_DATA_EXTRACTION = "PENDING_DATA_EXTRACTION"
    PENDING_REVIEW = "PENDING_REVIEW"
    CANCELED = "CANCELED"
    CONFIRMED = "CONFIRMED"
    DELIVERED_TO_DESTINATION = "DELIVERED_TO_DESTINATION"


class HubSettings(BaseModel):
    workspace_id: str
    access_token: str
    host: str
    

class ScheduleRunCommand(BaseModel):
    host: RunnerHost
    tags: list[str]
    workflows: list[str]
    data: dict[str, Any]


class Hub:
    """Client for interacting with the AskUI Hub API."""

    def __init__(self, settings: HubSettings):
        """Initialize the Hub client.

        Args:
            host (str): Host URL of the AskUI Hub API.
            access_token (str): Access token for authentication.
        """
        self._workspace_id = settings.workspace_id
        configuration = askui_workspaces.Configuration(
            host=settings.host,
        )
        configuration.api_key['Basic'] = f"Basic {base64.b64encode(settings.access_token.encode()).decode()}"
        self._api_client = askui_workspaces.ApiClient(configuration)
        self._agents_api = AgentsApi(self._api_client)
        self._agent_executions_api = AgentExecutionsApi(self._api_client)
        self._schedules_api = SchedulesApi(self._api_client)

    def get_agent(self, agent_id: UUID) -> Agent:
        """Get an agent by its ID.

        Args:
            agent_id (UUID): The ID of the agent to retrieve.

        Returns:
            Optional[Agent]: The agent data or None if disabled/not found.

        Raises:
            ApiException: If the API request fails.
        """ 
        response = self._agents_api.list_agents_api_v1_agents_get(
            agent_id=[str(agent_id)]
        )
        if not response.data:
            raise ValueError(f"Agent {agent_id} not found")
        return response.data[0]
    
    def get_agent_execution(self, agent_execution_id: UUID) -> AgentExecution:
        response = self._agent_executions_api.list_agent_executions_api_v1_agent_executions_get(
            agent_execution_id=[str(agent_execution_id)]
        )
        if not response.data:
            raise ValueError(f"Agent execution {agent_execution_id} not found")
        return response.data[0]

    def update_agent_execution(
        self, 
        agent_execution_id: UUID, 
        state: Union[AgentExecutionStateCanceled, AgentExecutionStateConfirmed, AgentExecutionStatePendingReview, AgentExecutionStateDeliveredToDestinationInput]
    ) -> AgentExecution:
        """Update an agent execution.

        Args:
            agent_execution_id (UUID): The ID of the agent execution to update.
            state (Union[AgentExecutionStateCanceled, AgentExecutionStateConfirmed, AgentExecutionStatePendingReview]): 
                The new state of the agent execution.

        Returns:
            Optional[AgentExecution]: The updated agent execution data or None if disabled.

        Raises:
            ApiException: If the API request fails.
        """
        command = AgentExecutionUpdateCommand(state=State1(state.model_dump())) # type: ignore
        return self._agent_executions_api.update_agent_execution_api_v1_agent_executions_agent_execution_id_patch(
            agent_execution_id=str(agent_execution_id),
            agent_execution_update_command=command
        )

    def wait_for_agent_execution_status(
        self, 
        agent_execution_id: UUID, 
        target_status: set[AgentExecutionStatus], 
        timeout: int = 3600, 
        interval: int = 30
    ) -> AgentExecution:
        """Wait for an agent execution to enter a specific status.

        Args:
            agent_execution_id (UUID): The ID of the agent execution to wait for.
            target_status (AgentExecutionStatus): The target status to wait for.
            timeout (int, optional): Maximum time to wait in seconds. Defaults to 300.
            interval (int, optional): Time between checks in seconds. Defaults to 5.

        Returns:
            Optional[AgentExecution]: The agent execution data once it reaches the target status or None if disabled.

        Raises:
            TimeoutError: If the agent execution doesn't reach the target status within the timeout.
            ApiException: If the API request fails.
        """
        start_time = time.time()
        while True:
            response = self._agent_executions_api.list_agent_executions_api_v1_agent_executions_get(
                agent_execution_id=[str(agent_execution_id)]
            )
            if not response.data:
                raise ValueError(f"Agent execution {agent_execution_id} not found")
            
            execution = response.data[0]
            execution_state = execution.state.actual_instance
            logger.debug(f"Agent execution {agent_execution_id} is in state {execution_state.status if execution_state else 'None'}")
            if execution_state and execution_state.status in target_status:
                return execution

            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout waiting for agent execution {agent_execution_id} to reach status {target_status}")

            time.sleep(interval)

    def schedule_run(self, command: ScheduleRunCommand) -> str:
        request_dto = CreateScheduleRequestDto(
            host=command.host,
            tags=command.tags,
            workflows=command.workflows,
            data=command.data,
        )
        response = self._schedules_api.create_schedule_api_v1_workspaces_workspace_id_schedules_post(
            workspace_id=self._workspace_id,
            create_schedule_request_dto=request_dto
        )
        return response.id # type: ignore
