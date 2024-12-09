from dataclasses import dataclass
import enum
import io
import mimetypes
from pathlib import Path


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


def load_files(paths: list[str], recursive: bool = False) -> list[ValidatedFile]:
    validated_files = []
    for path in paths:
        path_obj = Path(path)
        if not path_obj.exists():
            continue
            
        if path_obj.is_file():
            mime_type = _get_mime_type(str(path_obj))
            if mime_type and _is_supported_content_type(mime_type):
                with open(path_obj, 'rb') as f:
                    validated_files.append(ValidatedFile(
                        content_type=ContentTypeSupported(mime_type),
                        file=f,
                        filename=path_obj.name
                    ))
        elif path_obj.is_dir():
            pattern = '**/*' if recursive else '*'
            for file_path in path_obj.glob(pattern):
                if file_path.is_file():
                    mime_type = _get_mime_type(str(file_path))
                    if mime_type and _is_supported_content_type(mime_type):
                        with open(file_path, 'rb') as f:
                            validated_files.append(ValidatedFile(
                                content_type=ContentTypeSupported(mime_type),
                                file=f,
                                filename=file_path.name
                            ))        
    return validated_files
