from dataclasses import dataclass
import enum
import io
import mimetypes
from pathlib import Path
import os
import re
from typing import Optional
from urllib.parse import urlencode, urljoin

import requests
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential


class ValidatedFilesContext:
            def __init__(self, paths: list[str], recursive: bool = False):
                self.paths = paths
                self.recursive = recursive
                self.validated_files: list[ValidatedFile] = []
            
            def __enter__(self):
                for path in self.paths:
                    path_obj = Path(path)
                    if not path_obj.exists():
                        continue
                        
                    if path_obj.is_file():
                        mime_type = _get_mime_type(str(path_obj))
                        if mime_type and _is_supported_content_type(mime_type):
                            f = open(path_obj, 'rb')
                            self.validated_files.append(ValidatedFile(
                                content_type=ContentTypeSupported(mime_type),
                                file=f,
                                filename=path_obj.name
                            ))
                    elif path_obj.is_dir():
                        pattern = '**/*' if self.recursive else '*'
                        for file_path in path_obj.glob(pattern):
                            if file_path.is_file():
                                mime_type = _get_mime_type(str(file_path))
                                if mime_type and _is_supported_content_type(mime_type):
                                    f = open(file_path, 'rb')
                                    self.validated_files.append(ValidatedFile(
                                        content_type=ContentTypeSupported(mime_type),
                                        file=f,
                                        filename=file_path.name
                                    ))        
                return self.validated_files
            
            def __exit__(self, exc_type, exc_value, traceback):
                for file in self.validated_files:
                    file.file.close()
                self.validated_files = []


class ContentTypeSupported(str, enum.Enum):
    APPLICATION_PDF = "application/pdf"
    IMAGE_GIF = "image/gif"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_JPG = "image/jpg"
    IMAGE_PNG = "image/png"
    IMAGE_WEBP = "image/webp"
    MESSAGE_RFC822 = "message/rfc822"
    TEXT_PLAIN = "text/plain"


@dataclass
class ValidatedFile:
    content_type: ContentTypeSupported
    file: io.BufferedIOBase
    filename: str


def _is_supported_content_type(mime_type: str) -> bool:
    return mime_type in [e.value for e in ContentTypeSupported]


def _get_mime_type(file_path: str) -> str | None:
    return mimetypes.guess_type(file_path)[0]


class FileDto(BaseModel):
    name: str
    path: str
    url: str


class FilesListResponseDto(BaseModel):
    data: list[FileDto]
    next_continuation_token: Optional[str] = Field(default=None)


REQUEST_TIMEOUT_IN_S=60
UPLOAD_REQUEST_TIMEOUT_IN_S=3600 # allows for uploading large files


class AskUiFilesService:
    HIDDEN_FILES_PATTERNS = [
        r"^workspaces/[^/]+/test-cases/\.askui/.+$",
    ]
    
    def __init__(self, base_url: str, headers: dict[str, str]):
        self.disabled = base_url == ""
        self.base_url = base_url.rstrip("/")
        self.headers = headers

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(), reraise=True
    )
    def _upload_file(
        self, local_file_path: str, remote_file_path: str
    ) -> None:
        with open(local_file_path, "rb") as f:
            url = urljoin(
                base=self.base_url + "/",
                url=remote_file_path,
            )
            with requests.put(
                url,
                files={"file": f},
                headers=self.headers,
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
        if self.disabled:
            return
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
            headers=self.headers,
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
        list_url = f"{self.base_url}?{urlencode(params)}"
        response = requests.get(list_url, headers=self.headers, timeout=REQUEST_TIMEOUT_IN_S)
        if response.status_code != 200:
            response.raise_for_status()
        return FilesListResponseDto(**response.json())

    def download(self, local_dir_path: str, remote_path: str = "") -> None:
        """Download files from S3.
        
        Args:
            local_dir_path (str): The local directory to download the files to.
            remote_path (str, optional): The remote path to a directory to download the files from or a single file to download. Defaults to "". If you pass a a prefix of a directory or file, the `remote_path` prefix is going to be stripped from the file paths when creating the local paths to the files.
        """
        if self.disabled:
            return
        continuation_token = None
        prefix = remote_path.lstrip("/")
        while True:
            list_objects_response = self._list_objects(prefix, continuation_token)
            for content in list_objects_response.data:    
                if any(re.match(pattern, content.path) is not None for pattern in self.HIDDEN_FILES_PATTERNS):
                    continue

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

    def load_files_from_disk(self, paths: list[str], recursive: bool = False) -> ValidatedFilesContext:
        return ValidatedFilesContext(paths, recursive)
