import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from PIL import Image
from pydantic import UUID4, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from askui.chat.exceptions import AnnotationError

Coordinate = Tuple[int, int]


class Rectangle(BaseModel):
    xmin: int
    ymin: int
    xmax: int
    ymax: int

    @property
    def center(self) -> Coordinate:
        x = (self.xmin + self.xmax) // 2
        y = (self.ymin + self.ymax) // 2
        return (x, y)


class Annotation(BaseModel):
    id: UUID4
    rectangle: Rectangle


class Size(BaseModel):
    width: int
    height: int


class AskUIImage(BaseModel):
    size: Size


class AnnoationContainer(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda field_name: to_camel(field_name),
    )

    version: int
    id: UUID4
    creation_date_time: datetime
    image: AskUIImage
    annotations: List[Annotation]


class AskUiSnippingTool:
    def __init__(self) -> None:
        self.process = None

    def __find_remote_device_controller(self) -> str:
        if sys.platform == "darwin":
            return f"{os.environ['ASKUI_INSTALLATION_DIRECTORY']}/DependencyCache/AskUIRemoteDeviceSnippingTool-0.2.0/AskuiRemoteDeviceSnippingTool"
        error_msg = "Snipping tool not supported on this platform, yet, as the path was unknown at the time of writing"
        raise NotImplementedError(error_msg)

    def __start_process(self, binary_path: str, output_directory: str) -> None:
        self.process = subprocess.check_output(
            (binary_path, "-Annotate", "-OneShot", "-OutDirectory", output_directory)
        )

    def annotate(self) -> Tuple[Image.Image, AnnoationContainer]:
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_path = Path(tempdir)
            self.__start_process(self.__find_remote_device_controller(), tempdir)

            json_files = list(tempdir_path.glob("*.json"))
            png_files = list(tempdir_path.glob("*.png"))

            if len(json_files) != 1 or len(png_files) != 1:
                raise AnnotationError
            json_file = json_files[0]
            annotation = None
            with Path.open(json_file) as json_data:
                annotation = AnnoationContainer(**json.load(json_data))

            return Image.open(png_files[0]).copy(), annotation


class ClickRecorder:
    def __init__(self) -> None:
        self.snipping_tool = AskUiSnippingTool()

    def record(self) -> Tuple[Image.Image, Coordinate]:
        image, annotation_container = self.snipping_tool.annotate()
        assert (
            annotation_container.annotations is not None
            and len(annotation_container.annotations) == 1
        )
        annotation = annotation_container.annotations[0]
        center = annotation.rectangle.center
        return image, center
