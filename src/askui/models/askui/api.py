import os
import base64
import pathlib
import requests

from PIL import Image
from typing import Dict, Union
from askui.utils import image_to_base64
from askui.logging import logger


class AskUIHandler:
    def __init__(self):
        self.inference_endpoint = os.getenv("ASKUI_INFERENCE_ENDPOINT", "https://inference.askui.com")
        self.workspace_id = os.getenv("ASKUI_WORKSPACE_ID")
        self.token = os.getenv("ASKUI_TOKEN")

        self.authenticated = True
        if self.workspace_id is None or self.token is None:
            logger.warning("ASKUI_WORKSPACE_ID or ASKUI_TOKEN missing.")
            self.authenticated = False

    def __build_askui_token_auth_header(self, bearer_token: str = None) -> Dict[str, str]:
        if bearer_token != None:
            return {"Authorization": f"Bearer {bearer_token}"}
        token_base64 = base64.b64encode(self.token.encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {token_base64}"}
    
    def __build_model_composition(self):
        return {}
    
    def __build_base_url(self, endpoint: str = "inference") -> str:
        return f"{self.inference_endpoint}/api/v3/workspaces/{self.workspace_id}/{endpoint}"

    def predict(self, image: Union[pathlib.Path, Image.Image], instruction: str):
        response = requests.post(
            self.__build_base_url(),
            json={
                "image": f",{image_to_base64(image)}",
                **({"instruction": instruction} if instruction is not None else {}),
                **self.__build_model_composition(),
            },
            headers={"Content-Type": "application/json", **self.__build_askui_token_auth_header()},
            timeout=30,
        )
        if response.status_code != 200:
            raise Exception(f"{response.status_code}: Unknown Status Code\n", response.text)

        content = response.json()
        assert content["type"] == "COMMANDS", f"Received unknown content type {content['type']}"
        actions = [el for el in content["data"]["actions"] if el["inputEvent"] == "MOUSE_MOVE"]
        if len(actions) == 0:
            return None, None
        position = actions[0]["position"]

        return int(position["x"]), int(position["y"])
    
    def click_pta_prediction(self, image: Union[pathlib.Path, Image.Image], instruction: str):
        askui_instruction = f'Click on pta "{instruction}"'
        return self.predict(image, askui_instruction)
    
    def click_ocr_prediction(self, image: Union[pathlib.Path, Image.Image], instruction: str):
        askui_instruction = f'Click on with text "{instruction}"'
        return self.predict(image, askui_instruction)

