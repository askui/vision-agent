import json
import tempfile

from gradio_client import Client, handle_file


class HFSpacesHandler:
    def __init__(self):
        self.client = Client("AskUI/PTA-1")

    def predict(self, screenshot, instruction: str, model_name: str = "AskUI/PTA-1"):
        if model_name == "AskUI/PTA-1":
            return self.predict_askui_pta1(screenshot, instruction)

    def predict_askui_pta1(self, screenshot, instruction: str):
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot.save(temp_file, format='PNG')
            temp_file_path = temp_file.name
            result = self.client.predict(
                image=handle_file(temp_file_path),
                text_input=instruction,
                model_id="AskUI/PTA-1",
                api_name="/run_example"
            )
        target_box = json.loads(result[0])
        assert len(target_box) == 4, f"Malformed box: {target_box}"
        x1, y1, x2, y2 = target_box
        x = int((x1 + x2) / 2)
        y = int((y1 + y2) / 2)
        return x, y
