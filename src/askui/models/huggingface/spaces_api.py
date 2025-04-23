import json
import tempfile

from gradio_client import Client, handle_file
from askui.exceptions import AutomationError


class HFSpacesHandler:
    def __init__(self):
        self.clients = {}
        self.spaces = {
            "AskUI/PTA-1": self.predict_askui_pta1,
            "Qwen/Qwen2-VL-7B-Instruct": self.predict_qwen2_vl,
            "Qwen/Qwen2-VL-2B-Instruct": self.predict_qwen2_vl,
            "OS-Copilot/OS-Atlas-Base-7B": self.predict_os_atlas,
            "showlab/ShowUI-2B": self.predict_showui
        }

    def get_spaces_names(self):
        return list(self.spaces.keys())
    
    def get_space_client(self, space_name: str):
        if space_name in list(self.clients.keys()):
            return self.clients[space_name]
        self.clients[space_name] = Client(space_name)
        return self.clients[space_name]
    
    @staticmethod
    def rescale_bounding_boxes(bounding_boxes, original_width, original_height, scaled_width=1000, scaled_height=1000):
        x_scale = original_width / scaled_width
        y_scale = original_height / scaled_height
        rescaled_boxes = []
        for box in bounding_boxes:
            xmin, ymin, xmax, ymax = box
            rescaled_box = [
                xmin * x_scale,
                ymin * y_scale,
                xmax * x_scale,
                ymax * y_scale
            ]
            rescaled_boxes.append(rescaled_box)
        return rescaled_boxes

    def predict(self, screenshot, locator: str, model_name: str = "AskUI/PTA-1"):
        try:
            return self.spaces[model_name](screenshot, locator, model_name)
        except Exception as e:
            raise AutomationError(f"Hugging Face Spaces Exception: {e}")

    def predict_askui_pta1(self, screenshot, locator: str, model_name: str = None):
        client = self.get_space_client("AskUI/PTA-1")
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot.save(temp_file, format='PNG')
            temp_file_path = temp_file.name
            result = client.predict(
                image=handle_file(temp_file_path),
                text_input=locator,
                model_id=model_name,
                api_name="/run_example"
            )
        target_box = json.loads(result[0])
        assert len(target_box) == 4, f"Malformed box: {target_box}"
        x1, y1, x2, y2 = target_box
        x = int((x1 + x2) / 2)
        y = int((y1 + y2) / 2)
        return x, y
    
    def predict_os_atlas(self, screenshot, locator: str, model_name: str = None):
        client = self.get_space_client("maxiw/OS-ATLAS")
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot.save(temp_file, format='PNG')
            temp_file_path = temp_file.name
            result = client.predict(
                image=handle_file(temp_file_path),
                text_input=locator,
                model_id=model_name,
                api_name="/run_example"
            )
        target_box = json.loads(result[1])[0]
        assert len(target_box) == 4, f"Malformed box: {target_box}"
        x1, y1, x2, y2 = target_box
        x = int((x1 + x2) / 2)
        y = int((y1 + y2) / 2)
        return x, y
    
    def predict_qwen2_vl(self, screenshot, locator: str, model_name: str = None):
        client = self.get_space_client("maxiw/Qwen2-VL-Detection")
        system_prompt = "You are a helpfull assistant to detect objects in images. When asked to detect elements based on a description you return bounding boxes for all elements in the form of [xmin, ymin, xmax, ymax] whith the values beeing scaled to 1000 by 1000 pixels. When there are more than one result, answer with a list of bounding boxes in the form of [[xmin, ymin, xmax, ymax], [xmin, ymin, xmax, ymax], ...]."
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot.save(temp_file, format='PNG')
            temp_file_path = temp_file.name
            result = client.predict(
                image=handle_file(temp_file_path),
                text_input=locator,
                system_prompt=system_prompt,
                model_id=model_name,
                api_name="/run_example"
            )
        target_box = json.loads(result[1])
        target_box = self.rescale_bounding_boxes(target_box, screenshot.width, screenshot.height)[0]
        assert len(target_box) == 4, f"Malformed box: {target_box}"
        x1, y1, x2, y2 = target_box
        x = int((x1 + x2) / 2)
        y = int((y1 + y2) / 2)
        return x, y
    
    def predict_showui(self, screenshot, locator: str, model_name: str = None):
        client = self.get_space_client("showlab/ShowUI")
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot.save(temp_file, format='PNG')
            temp_file_path = temp_file.name
            result = client.predict(
                image=handle_file(temp_file_path),
                query=locator,
                api_name="/on_submit"
            )
            output_value = json.loads(result[1])
            relative_x, relative_y = output_value
            x = int(relative_x * screenshot.width)
            y = int(relative_y * screenshot.height)
            return x, y
