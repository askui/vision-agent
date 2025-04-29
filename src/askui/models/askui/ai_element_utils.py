from datetime import datetime
import os
import pathlib
from typing import List, Optional
from pydantic import UUID4, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from PIL import Image
from askui.logger import logger



class Rectangle(BaseModel):
    xmin: int
    ymin: int
    ymax: int
    ymax: int

class Annotation(BaseModel):
    id: UUID4
    rectangle: Rectangle

class Size(BaseModel):
    width: int
    height: int

class AskUIImageMetadata(BaseModel):
    size: Size

class AiElementMetadata(BaseModel):    
    model_config = ConfigDict(
        alias_generator=to_camel,
        serialization_alias=to_camel,
    )

    version: int
    id: UUID4
    name: str
    creation_date_time: datetime
    image_metadata: AskUIImageMetadata = Field(alias="image")

class AiElement():
    image_path: pathlib.Path
    image: Image.Image
    json_path: pathlib.Path
    metadata: AiElementMetadata

    def __init__(self, image_path: pathlib.Path, image: Image.Image, metadata_path: pathlib.Path, metadata: AiElementMetadata):
        self.image_path = image_path
        self.image = image
        self.metadata_path = metadata_path
        self.metadata = metadata

    @classmethod
    def from_json_file(cls, json_file_path: pathlib.Path) -> "AiElement":
            image_path = json_file_path.parent /  (json_file_path.stem + ".png")
            with open(json_file_path) as f:
                return cls(
                    metadata_path= json_file_path,
                    image_path= image_path,
                    metadata = AiElementMetadata.model_validate_json(f.read()),
                    image = Image.open(image_path))


class AiElementNotFound(ValueError):
    """Exception raised when an AI element is not found.
    
    Args:
        name (str): The name of the AI element that was not found.
        locations (list[pathlib.Path]): The locations that were searched for the AI element.
    """
    def __init__(self, name: str, locations: list[pathlib.Path]):
        self.name = name
        self.locations = locations
        locations_str = ", ".join([str(location) for location in locations])
        super().__init__(
            f'AI element "{name}" not found in {locations_str}\n'
            'Solutions:\n'
            '1. Verify the element exists in these locations and try again if you are sure it is present\n'
            '2. Add location to ASKUI_AI_ELEMENT_LOCATIONS env var (paths, comma separated)\n'
            '3. Create new AI element (see https://docs.askui.com/02-api-reference/02-askui-suite/02-askui-suite/AskUIRemoteDeviceSnippingTool/Public/AskUI-NewAIElement)'
        )


class AiElementCollection:
    def __init__(self, additional_ai_element_locations: Optional[List[pathlib.Path]] = None):
        additional_ai_element_locations = additional_ai_element_locations or []

        workspace_id = os.getenv("ASKUI_WORKSPACE_ID")
        if workspace_id is None:
            raise ValueError("ASKUI_WORKSPACE_ID is not set")
        
        locations_from_env: list[pathlib.Path] = []
        if locations_env := os.getenv("ASKUI_AI_ELEMENT_LOCATIONS"):
            locations_from_env = [pathlib.Path(loc) for loc in locations_env.split(",")]
        
        self._ai_element_locations = [
            pathlib.Path.home() / ".askui" / "SnippingTool" / "AIElement" / workspace_id,
            *locations_from_env,
            *additional_ai_element_locations
        ]

        logger.debug("AI Element locations: %s", self._ai_element_locations)

    def find(self, name: str) -> list[AiElement]:
        ai_elements: list[AiElement] = []
        for location in self._ai_element_locations:
            path = pathlib.Path(location)
            json_files = list(path.glob("*.json"))
            for json_file in json_files:
                ai_element = AiElement.from_json_file(json_file)
                if ai_element.metadata.name == name:
                    ai_elements.append(ai_element)
        if len(ai_elements) == 0:
            raise AiElementNotFound(name=name, locations=self._ai_element_locations)
        return ai_elements
