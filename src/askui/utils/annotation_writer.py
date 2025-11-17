from datetime import datetime, timezone
from html import escape
from pathlib import Path

from askui.models.models import DetectedElement
from askui.utils.source_utils import InputSource, load_image_source


class AnnotationWriter:
    """
    A writer that generates an interactive HTML file with annotated image elements.

    The generated HTML file displays an image with bounding boxes around detected
    elements. Users can hover over elements to see their names and click to copy
    their text values to the clipboard.

    Args:
        image (InputSource): The image source to annotate. Can be a path to an
            image file, a PIL Image object, or a data URL.
        elements (list[DetectedElement]): A list of detected elements to annotate
            on the image. Each element should have a name, text, and bounding box.
    """

    def __init__(
        self,
        image: InputSource,
        elements: list[DetectedElement],
    ):
        self._encoded_image = load_image_source(image).to_data_url()
        self._elements = elements

    def _get_style(self) -> str:
        """
        Generate the CSS styles for the annotation HTML.

        Returns:
            str: CSS styles as a string for styling bounding boxes, tooltips,
                and the copy message.
        """
        return """
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                }

                #container {
                    position: relative;
                    display: inline-block;
                }

                #base-image {
                    display: block;
                }

                .bbox {
                    position: absolute;
                    border: 2px solid rgb(111, 0, 255);
                    cursor: pointer;
                    box-sizing: border-box;
                }

                .bbox:hover {
                    border-color: lime;
                }

                .tooltip {
                    position: absolute;
                    background: rgba(0,0,0,0.75);
                    color: white;
                    padding: 3px 6px;
                    font-size: 12px;
                    border-radius: 4px;
                    white-space: nowrap;
                    pointer-events: none;
                    display: none;
                    z-index: 50;
                }

                .bbox:hover .tooltip {
                    display: block;
                }

                #copy-message {
                    position: fixed;
                    background: #333;
                    color: #fff;
                    padding: 10px 15px;
                    border-radius: 6px;
                    font-size: 14px;
                    display: none;
                    z-index: 500;
                }
            </style>
        """

    def _get_script(self) -> str:
        """
        Generate the JavaScript code for interactive features.

        Returns:
            str: JavaScript code as a string for handling copy-to-clipboard
                functionality, tooltip positioning, and copy message display.
        """
        return """
            <script>
            function copyTextFromBox(box) {
                const value = box.dataset.rawtext;
                if (value !== null && value !== undefined && value !== "") {
                    navigator.clipboard.writeText(value).then(function() {
                        showCopyMessage();
                    });
                }
            }

            function showCopyMessage() {
                const msg = document.getElementById("copy-message");
                msg.style.position = "fixed";
                msg.style.left = "50%";
                msg.style.top = "50%";
                msg.style.transform = "translate(-50%, -50%)";
                msg.style.display = "block";
                setTimeout(() => {
                    msg.style.display = "none";
                }, 700);
            }

            function positionTooltip(box) {
                const tooltip = box.querySelector(".tooltip");
                const boxRect = box.getBoundingClientRect();
                const baseImage = document.getElementById("base-image");
                const imgRect = baseImage.getBoundingClientRect();

                const tooltipHeight = 25;
                const margin = 4;

                if (boxRect.top - imgRect.top < tooltipHeight + margin) {
                    tooltip.style.top = boxRect.height + margin + "px";
                } else {
                    tooltip.style.top = -(tooltipHeight + margin) + "px";
                }

                tooltip.style.left = (boxRect.width / 2) + "px";
                tooltip.style.transform = "translateX(-50%)";

                const tooltipRect = tooltip.getBoundingClientRect();

                if (tooltipRect.left < imgRect.left) {
                    tooltip.style.left = "0px";
                    tooltip.style.transform = "none";
                }

                if (tooltipRect.right > imgRect.right) {
                    tooltip.style.left = boxRect.width + "px";
                    tooltip.style.transform = "translateX(-100%)";
                }
            }
        </script>
        """

    def _get_elements_html(self) -> str:
        """
        Generate HTML for all detected elements.

        Returns:
            str: Concatenated HTML string for all bounding box elements.
        """
        return "".join(self._get_box_html(element) for element in self._elements)

    def _get_box_html(self, element: DetectedElement) -> str:
        """
        Generate HTML for a single detected element's bounding box.

        Args:
            element (DetectedElement): The detected element to generate HTML for.

        Returns:
            str: HTML string for a single bounding box with tooltip and click
                handler.
        """
        bbox = element.bounding_box

        escaped_text = escape(element.text or "")
        escaped_name = escape(element.name or "")

        # safe HTML text for tooltips
        tooltip_text = escaped_name
        if escaped_text:
            tooltip_text += f": {escaped_text}"

        style = (
            f"left:{bbox.xmin}px; "
            f"top:{bbox.ymin}px; "
            f"width:{bbox.width}px; "
            f"height:{bbox.height}px;"
        )

        return f"""
        <div
            class="bbox"
            style="{style}"
            data-rawtext="{escaped_text}"
            onclick="copyTextFromBox(this)"
            onmouseover="positionTooltip(this)"
        >
            <span class="tooltip">{tooltip_text}</span>
        </div>
        """

    def _get_full_html(self) -> str:
        """
        Generate the complete HTML document with all annotations.

        Returns:
            str: Complete HTML document as a string including DOCTYPE, head,
                styles, scripts, and body with annotated image.
        """
        return f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="UTF-8">
            <title>Image Annotated By AskUI</title>

            {self._get_style()}

            {self._get_script()}

            </head>
            <body>

            <div id="copy-message"> 📋 Copied to clipboard! </div>

            <div id="container">
                <img id="base-image" src="{self._encoded_image}">
                {self._get_elements_html()}
            </div>

            </body>
            </html>
            """

    def write_to_file(self, output_directory: Path | str) -> Path:
        """
        Write the annotated HTML file to the output directory.

        Creates the output directory if it doesn't exist and generates a
        timestamped filename for the HTML file.

        Args:
            output_directory (Path | str, optional): The directory where the
                HTML file will be saved. Defaults to "annotated_images".

        Returns:
            Path: The path to the written HTML file.
        """
        if isinstance(output_directory, str):
            output_directory = Path(output_directory)
        if not output_directory.exists():
            output_directory.mkdir(parents=True, exist_ok=True)

        current_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        file_name = f"annotated_image_{current_timestamp}.html"
        file_path = output_directory / file_name
        html_content = self._get_full_html()

        with file_path.open("w", encoding="utf-8") as f:
            f.write(html_content)

        return file_path
