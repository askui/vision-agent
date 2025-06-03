import abc
import io
import uuid
from pathlib import Path
from typing import Any

from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch
from typing_extensions import override


class ChangeDetector(abc.ABC):
    """Protocol for change detection between images.

    A change detector is initialized with a reference image and then
    can be used to detect changes in subsequent images.
    """

    @abc.abstractmethod
    def detect_change(self, image: Image.Image) -> bool:
        """Detect if the given image has changed compared to the reference image.

        Args:
            image (Image.Image): The image to compare against the reference image.

        Returns:
            `True` if the image has changed significantly, `False` otherwise.
        """
        raise NotImplementedError


# TODO Add the most simple change detector that just says that there is always a change for testing purposes.


class PixelMatchChangeDetector(ChangeDetector):
    """Change detector that compares images pixel by pixel.

    Args:
        max_diff (int, optional): The maximum number of pixels that can differ.
            Defaults to `10`.
    """

    def __init__(
        self,
        # TODO Is this a good default threshold? How can I debug this? Is there a better default across resolutions, platforms etc.? We can also play with the parameters of the pixelmatch library.
        max_diff: int = 10,
    ) -> None:
        self._max_diff = max_diff
        self._previous_image: Image.Image | None = None
        self._diff_dir = Path("./diffs")
        self._diff_dir.mkdir(exist_ok=True)

    def __getstate__(self) -> dict[str, Any]:
        """Get state for pickling.

        Returns:
            dict[str, Any]: State dictionary with serialized image data.
        """
        state = self.__dict__.copy()
        if state["_previous_image"] is not None:
            buffer = io.BytesIO()
            state["_previous_image"].save(buffer, format="PNG")
            state["_previous_image"] = buffer.getvalue()
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore state from pickle.

        Args:
            state (dict[str, Any]): State dictionary with serialized image data.
        """
        if state["_previous_image"] is not None:
            buffer = io.BytesIO(bytes(state["_previous_image"]))
            state["_previous_image"] = Image.open(buffer)
        self.__dict__.update(state)

    @override
    def detect_change(self, image: Image.Image) -> bool:
        if self._previous_image is None:
            self._previous_image = image
            return True

        img_diff = Image.new("RGBA", image.size)

        result = pixelmatch(self._previous_image, image, img_diff)
        img_diff.save(f"./diffs/{uuid.uuid4()}.png", format="PNG")
        self._previous_image = image
        return result > self._max_diff
