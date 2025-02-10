import re
import os
import pathlib
from typing import Union
from openai import OpenAI
from askui.utils import image_to_base64
from PIL import Image
from .prompts import PROMPT, PROMPT_QA


class UITarsAPIHandler:
    def __init__(self):
        if os.getenv("TARS_URL") is None or os.getenv("TARS_API_KEY") is None:
            self.authenticated = False
        else:
            self.client = OpenAI(
                base_url=os.getenv("TARS_URL"), 
                api_key=os.getenv("TARS_API_KEY")
            )

    def predict(self, screenshot, instruction: str, prompt: str):
        chat_completion = self.client.chat.completions.create(
        model="tgi",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_to_base64(screenshot)}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt + instruction
                    }
                ]
            }
        ],
            top_p=None,
            temperature=None,
            max_tokens=150,
            stream=False,
            seed=None,
            stop=None,
            frequency_penalty=None,
            presence_penalty=None
        )

        return chat_completion.choices[0].message.content

    def click_pta_prediction(self, image: Union[pathlib.Path, Image.Image], instruction: str) -> tuple[int | None, int | None]:
        askui_instruction = f'Click on "{instruction}"'
        prediction = self.predict(image, askui_instruction, PROMPT)
        pattern = r"click\(start_box='(\(\d+,\d+\))'\)"
        match = re.search(pattern, prediction)
        if match:
            x, y = match.group(1).strip("()").split(",")
            x, y = int(x), int(y)
            if isinstance(image, pathlib.Path):
                image = Image.open(image)
            width, height = image.size
            x = (x * width) // 1000
            y = (y * height) // 1000
            return x, y
        return None, None

    def get_prediction(self, image: Image.Image, instruction: str) -> str:
        return self.predict(image, instruction, PROMPT_QA)
