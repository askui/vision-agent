import os
import base64
import pathlib
import requests

from PIL import Image
from typing import List, Union
from askui.models.askui.ai_element_utils import AiElement, AiElementCollection
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

        self.ai_element_collection = AiElementCollection()



    def __build_askui_token_auth_header(self, bearer_token: str | None = None) -> dict[str, str]:
        if bearer_token is not None:
            return {"Authorization": f"Bearer {bearer_token}"}
        token_base64 = base64.b64encode(self.token.encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {token_base64}"}
    
    def _build_custom_elements(self, ai_elements: List[AiElement] | None):
        """
        Converts AiElements to the CustomElementDto format expected by the backend.
        
        Args:
            ai_elements (List[AiElement]): List of AI elements to convert
            
        Returns:
            dict: Custom elements in the format expected by the backend
        """
        if not ai_elements:
            return {}
        
        custom_elements = []
        for element in ai_elements:
            custom_element = {
                "customImage": "," + image_to_base64(element.image),            
                "imageCompareFormat": "grayscale",
                "name": element.metadata.name
            }
            custom_elements.append(custom_element)
        
        return {
            "customElements": custom_elements
        }  
    def __build_model_composition(self):
        return {}
    
    def __build_base_url(self, endpoint: str = "inference") -> str:
        return f"{self.inference_endpoint}/api/v3/workspaces/{self.workspace_id}/{endpoint}"

    def predict(self, image: Union[pathlib.Path, Image.Image], locator: str, ai_elements: List[pathlib.Path] = None) -> tuple[int | None, int | None]:
        response = requests.post(
            self.__build_base_url(),
            json={
                "image": f",{image_to_base64(image)}",
                **({"instruction": locator} if locator is not None else {}),
                **self.__build_model_composition(),
                **self._build_custom_elements(ai_elements)
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
    
    def locate_pta_prediction(self, image: Union[pathlib.Path, Image.Image], locator: str) -> tuple[int | None, int | None]:
        askui_locator = f'Click on pta "{locator}"'
        return self.predict(image, askui_locator)
    
    def locate_ocr_prediction(self, image: Union[pathlib.Path, Image.Image], locator: str) -> tuple[int | None, int | None]:
        askui_locator = f'Click on with text "{locator}"'
        return self.predict(image, askui_locator)
    
    def locate_ai_element_prediction(self, image: Union[pathlib.Path, Image.Image], locator: str) -> tuple[int | None, int | None]:
        ai_elements = self.ai_element_collection.find(instruction)

        if len(ai_elements) == 0:
            raise AiElementNotFound(f"Could not locate AI element with name '{locator}'")
        
        askui_instruction = f'Click on custom element with text "{locator}"'
        return self.predict(image, askui_instruction, ai_elements=ai_elements)
