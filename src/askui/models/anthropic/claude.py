import os
import anthropic
from PIL import Image

from ...logging import logger
from ...utils import AutomationError
from ..utils import scale_image_with_padding, scale_coordinates_back, extract_click_coordinates, image_to_base64


class ClaudeHandler:
    def __init__(self, log_level):
        self.model_name = "claude-3-5-sonnet-20241022"
        self.client = anthropic.Anthropic()
        self.resolution = (1280, 800)
        self.log_level = log_level
        self.authenticated = True
        if os.getenv("ANTHROPIC_API_KEY") is None:
            self.authenticated = False

    def inference(self, base64_image, prompt, system_prompt):
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=1000,
            temperature=0,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        return message.content
    
    def click_inference(self, image: Image.Image, instruction: str):
        prompt = f"Click on {instruction}"
        screen_width, screen_height = self.resolution[0], self.resolution[1]
        system_prompt = f"Use a mouse and keyboard to interact with a computer, and take screenshots.\n* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.\n* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try taking another screenshot.\n* The screen's resolution is {screen_width}x{screen_height}.\n* The display number is 0\n* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.\n* If you tried clicking on a program or link but it failed to load, even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.\n* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.\n"
        scaled_image = scale_image_with_padding(image, screen_width, screen_height)
        response = self.inference(image_to_base64(scaled_image), prompt, system_prompt)
        response = response[0].text
        logger.debug("ClaudeHandler received instruction: %s", response)
        try:
            scaled_x, scaled_y = extract_click_coordinates(response)
        except Exception as e:
            raise AutomationError(f"Couldn't locate '{instruction}' on the screen.")
        x, y = scale_coordinates_back(scaled_x, scaled_y, image.width, image.height, screen_width, screen_height)
        return int(x), int(y)

    def get_inference(self, image: Image.Image, instruction: str):
        scaled_image = scale_image_with_padding(image, self.resolution[0], self.resolution[1])
        system_prompt = "You are an agent to process screenshots and answer questions about things on the screen or extract information from it. Answer only with the response to the question and keep it short and precise."
        response = self.inference(image_to_base64(scaled_image), instruction, system_prompt)
        response = response[0].text
        return response
