from collections.abc import Iterator
from enum import Enum
import re
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, RootModel


class ModelName(str, Enum):
    ANTHROPIC__CLAUDE__3_5__SONNET__20241022 = "anthropic-claude-3-5-sonnet-20241022"
    ANTHROPIC = "anthropic"
    ASKUI = "askui"
    ASKUI__AI_ELEMENT = "askui-ai-element"
    ASKUI__COMBO = "askui-combo"
    ASKUI__OCR = "askui-ocr"
    ASKUI__PTA = "askui-pta"
    TARS = "tars"


MODEL_DEFINITION_PROPERTY_REGEX_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


ModelDefinitionProperty = Annotated[
    str, Field(pattern=MODEL_DEFINITION_PROPERTY_REGEX_PATTERN)
]


class ModelDefinition(BaseModel):
    """
    A definition of a model.
    """
    model_config = ConfigDict(
        populate_by_name=True,
    )
    task: ModelDefinitionProperty = Field(
        description="The task the model is trained for, e.g., end-to-end OCR (e2e_ocr) or object detection (od)",
        examples=["e2e_ocr", "od"],
    )
    architecture: ModelDefinitionProperty = Field(
        description="The architecture of the model", examples=["easy_ocr", "yolo"]
    )
    version: str = Field(pattern=r"^[0-9]{1,6}$")
    interface: ModelDefinitionProperty = Field(
        description="The interface the model is trained for",
        examples=["online_learning", "offline_learning"],
    )
    use_case: ModelDefinitionProperty = Field(
        description='The use case the model is trained for. In the case of workspace specific AskUI models, this is often the workspace id but with "-" replaced by "_"',
        examples=[
            "fb3b9a7b_3aea_41f7_ba02_e55fd66d1c1e",
            "00000000_0000_0000_0000_000000000000",
        ],
        default="00000000_0000_0000_0000_000000000000",
        serialization_alias="useCase",
    )
    tags: list[ModelDefinitionProperty] = Field(
        default_factory=list,
        description="Tags for identifying the model that cannot be represented by other properties",
        examples=["trained", "word_level"],
    )

    @property
    def model_name(self) -> str:
        return (
            "-".join(
                [
                    self.task,
                    self.architecture,
                    self.interface,
                    self.use_case,
                    self.version,
                    *self.tags,
                ]
            )
        )


class ModelComposition(RootModel[list[ModelDefinition]]):
    """
    A composition of models.
    """

    def __iter__(self):
        return iter(self.root)
    
    def __getitem__(self, index: int) -> ModelDefinition:
        return self.root[index]
