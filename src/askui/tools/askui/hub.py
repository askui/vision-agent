import base64
import io
from typing import Any
from loguru import logger
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_core.language_models import BaseChatModel
from PIL import Image
from pdf2image import convert_from_path, convert_from_bytes
from typing import Generator
import tempfile

from askui.tools.askui.files import ContentTypeSupported, ValidatedFile


def image_to_data_url(image: Image.Image, format: str = "PNG", quality: int = 85) -> str:
    """
    Converts a PIL Image to a data URL.

    Args:
        image (Image.Image): The PIL Image to be converted.
        format (str): The format to save the image in (e.g., "JPEG", "PNG"). Default is "PNG".
        quality (int): The quality for JPEG compression (1-95). Default is 85. Ignored for formats like PNG.

    Returns:
        str: The data URL representing the image.
    """
    buffered = io.BytesIO()
    if format.upper() == "JPEG":
        image = image.convert("RGB")
        image.save(buffered, format=format, quality=quality)
    else:
        image.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    data_url = f"data:image/{format.lower()};base64,{img_str}"
    return data_url


def pdf_to_images(pdf: str | bytes, dpi: int = 300) -> Generator[Image.Image, None, None]:
    """
    Converts each page of a PDF to an image and yields them one by one.

    Args:
        pdf (str | bytes): The path to the PDF file or the PDF file as bytes.
        dpi (int): The resolution of the output images in DPI (default: 300).

    Yields:
        PIL.Image.Image: A PIL Image object for each page in the PDF.

    Raises:
        ValueError: If the PDF cannot be processed due to .
        Exception: For other general errors.
    """
    try:
        with tempfile.TemporaryDirectory() as output_folder:
            if isinstance(pdf, str):
                images = convert_from_path(pdf, dpi=dpi, output_folder=output_folder)
            elif isinstance(pdf, bytes):
                images = convert_from_bytes(pdf, dpi=dpi, output_folder=output_folder)
            else:
                raise ValueError("Invalid input: 'pdf' must be a file path or a file-like object.")
            for img in images:
                yield img
    except ValueError as value_error:
        raise value_error
    except Exception as exception:
        raise Exception(f"An error occurred during PDF to image conversion: {str(exception)}") from exception


class Hub:
    def __init__(
        self,
        chat_model: BaseChatModel,
    ) -> None:
        self.chat_model = chat_model

    def _create_file_content_map(self, input_files: list[ValidatedFile]) -> dict[str, list[dict[str, Any]]]:
        result = {}
        for file in input_files:
            content: list[dict[str, Any]] = []
            if file.content_type == ContentTypeSupported.APPLICATION_PDF:
                content.append({"type": "text", "text": f'Pages of PDF file "{file.filename}":'})
                for i, img in enumerate(pdf_to_images(file.file.read())):
                    content.append({"type": "text", "text": f'Page {i+1} of PDF file "{file.filename}":'})
                    content.append({"type": "image_url", "image_url": {"url": image_to_data_url(img)}})
            elif (
                file.content_type == ContentTypeSupported.MESSAGE_RFC822
                or file.content_type == ContentTypeSupported.TEXT_PLAIN
            ):
                content.append({"type": "text", "text": f'Content of text file or email "{file.filename}":'})
                content.append({"type": "text", "text": file.file.read().decode("utf-8")})
            else:
                content.append({"type": "text", "text": f'Image file "{file.filename}":'})
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": image_to_data_url(Image.open(io.BytesIO(file.file.read())))},
                    }
                )
            result[file.filename] = content
        return result
    
    def extract_data(self, input_files: list[ValidatedFile], data_schema: dict[str, Any]) -> dict[str, Any]:
        file_content_map = self._create_file_content_map(input_files)
        root_properties: dict[str, Any] = data_schema["properties"]
        file_root_properties: dict[str, Any] = {}
        non_file_root_properties: dict[str, Any] = {}
        for prop_key, prop_value in root_properties.items():
            if prop_value.get("x-is-file-class"):
                file_root_properties[prop_key] = prop_value
            else:
                non_file_root_properties[prop_key] = prop_value
        file_root_property_keys = list(file_root_properties.keys())
        result: dict[str, list[str | dict[str, Any]]] = {}
        if not file_root_properties:
            logger.info("No file root properties found. Skipping file classification...")
        else:
            classification_schema = {
                "title": "FileClassification",
                "description": "",
                "type": "object",
                "properties": {
                    "classes": {
                        "type": "array",
                        "items": {
                            "oneOf": [
                                {
                                    "type": "string",
                                    "const": file_root_property_key,
                                    "title": file_root_properties[file_root_property_key].get(
                                        "title", file_root_property_key
                                    ),
                                    "description": file_root_properties[file_root_property_key].get("description", ""),
                                }
                                for file_root_property_key in file_root_property_keys
                            ],
                        },
                        "uniqueItems": True,
                    },
                },
                "required": ["classes"],
            }
            logger.info(classification_schema)
            classification_llm = self.chat_model.with_structured_output(
                schema=classification_schema,
                include_raw=False,
            )
            classification_map: dict[str, list[str]] = {
                file_root_property_key: [] for file_root_property_key in file_root_property_keys
            }
            for file in input_files:
                classification = classification_llm.invoke(
                    [
                        SystemMessage(
                            content="You are a file classifier. Your task is to classify a file based on information given into none, one or more classes."
                        ),
                        HumanMessage(
                            content=file.filename,
                        ),
                    ],
                )
                for file_root_property_key in classification["classes"]:
                    classification_map[file_root_property_key].append(file.filename)
            logger.info(f"File classification results: {classification_map}")
            logger.info("Extracting data from file root properties...")
            for file_root_property_key, file_names in classification_map.items():
                is_required = file_root_property_key in data_schema["required"]
                content: list[str | dict[str, Any]] = []
                if file_names:
                    for file_name in file_names:
                        content.extend(file_content_map[file_name])
                else:
                    if is_required:
                        logger.info(
                            f"No files found for (required) file root property key: {file_root_property_key}. Extracting data from all files..."
                        )
                    else:
                        logger.info(
                            f"No files found for (optional) file root property key: {file_root_property_key}. Skipping data extraction..."
                        )
                        continue
                    for file_content in file_content_map.values():
                        content.extend(file_content)
                sub_data_schema = {
                    **data_schema,
                    "properties": {file_root_property_key: file_root_properties[file_root_property_key]},
                    "required": [file_root_property_key] if is_required else [],
                }
                structured_llm: Runnable[LanguageModelInput, Any] = self.chat_model.with_structured_output(
                    schema=sub_data_schema,
                    include_raw=False,
                )
                llm_output = structured_llm.invoke(
                    [
                        HumanMessage(
                            content=content,
                        )
                    ],
                )
                result[file_root_property_key] = llm_output[file_root_property_key]
        if not non_file_root_properties:
            logger.info("No non-file root properties found. Skipping data extraction...")
        else:
            logger.info("Extracting data from non-file root properties from all files...")
            content: list[str | dict[str, Any]] = []  # type: ignore
            for file_content in file_content_map.values():
                content.extend(file_content)
            sub_data_schema = {
                **data_schema,
                "properties": non_file_root_properties,
                "required": [
                    required for required in data_schema.get("required", []) if required in non_file_root_properties
                ],
            }
            structured_llm: Runnable[LanguageModelInput, Any] = self.chat_model.with_structured_output(  # type: ignore
                schema=sub_data_schema,
                include_raw=False,
            )
            llm_output = structured_llm.invoke(
                [
                    HumanMessage(
                        content=content,
                    )
                ],
            )
            result.update(llm_output)
        return result
