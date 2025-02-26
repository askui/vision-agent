from datetime import datetime
import os
import pathlib
from typing import List, Optional
from pydantic import UUID4, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from PIL import Image
from askui.logging import logger



class Recangel(BaseModel):
    xmin: int
    ymin: int
    ymax: int
    ymax: int

class Annotation(BaseModel):
    id: UUID4
    rectangle: Recangel

class Size(BaseModel):
    width: int
    height: int

class AskUIImageMetaData(BaseModel):
    size: Size

class AiElementJson(BaseModel):    
    model_config = ConfigDict(
        alias_generator=lambda field_name: to_camel(field_name),
        serialization_alias=lambda field_name: to_camel(field_name),
    )

    version: int
    id: UUID4
    name: str
    creation_date_time: datetime
    image_meta_data: AskUIImageMetaData = Field(alias="image")

class AiElement():
    image_path: pathlib.Path
    image: Image.Image
    json_path: pathlib.Path
    metadata: AiElementJson

    def __init__(self, image_path: pathlib.Path, image: Image.Image, metadata_path: pathlib.Path, metadata: AiElementJson):
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
                    metadata = AiElementJson.model_validate_json(f.read()),
                    image = Image.open(image_path))


class AiElementNotFound(Exception):
    pass


class AiElementCollection:

    def __init__(self, additional_ai_element_locations: Optional[List[pathlib.Path]] = None):
        workspace_id = os.getenv("ASKUI_WORKSPACE_ID")
        if workspace_id is None:
            raise ValueError("ASKUI_WORKSPACE_ID is not set")
        
        if additional_ai_element_locations is None:
            additional_ai_element_locations = []
        
        addional_ai_element_from_env = []
        if os.getenv("ASKUI_AI_ELEMENT_LOCATIONS", "") != "":
            addional_ai_element_from_env = [pathlib.Path(ai_element_loc) for ai_element_loc in os.getenv("ASKUI_AI_ELEMENT_LOCATIONS", "").split(",")],
        
        self.ai_element_locations = [
            pathlib.Path.home() / ".askui" / "SnippingTool" / "AIElement" / workspace_id,
            *addional_ai_element_from_env,
            *additional_ai_element_locations
        ]

        logger.warning("AI Element locations: %s", self.ai_element_locations)

    def find(self, name: str):
        ai_elements = []

        for location in self.ai_element_locations:
            path = pathlib.Path(location)
            
            json_files = list(path.glob("*.json"))
            
            if not json_files:
                logger.warning(f"No JSON files found in: {location}")
                continue
                
            for json_file in json_files:
                ai_element = AiElement.from_json_file(json_file)

                if ai_element.metadata.name == name:
                    ai_elements.append(ai_element)

        return ai_elements