"""Tests for VisionAgent with different model compositions"""

import pytest
from PIL import Image as PILImage

from askui.agent import VisionAgent
from askui.locators import Text
from askui.locators.locators import DEFAULT_SIMILARITY_THRESHOLD
from askui.models import ModelComposition, ModelDefinition


@pytest.mark.parametrize(
    "model",
    [
        ModelComposition(
            [
                ModelDefinition(
                    task="e2e_ocr",
                    architecture="easy_ocr",
                    version="1",
                    interface="online_learning",
                )
            ]
        ),
        ModelComposition(
            [
                ModelDefinition(
                    task="e2e_ocr",
                    architecture="easy_ocr",
                    version="1",
                    interface="online_learning",
                    use_case="fb3b9a7b_3aea_41f7_ba02_e55fd66d1c1e",
                    tags=["trained"],
                )
            ]
        ),
    ],
)
class TestSimpleOcrModel:
    """Test class for simple OCR model compositions."""

    def test_locate_with_simple_ocr(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: ModelComposition,
    ) -> None:
        """Test locating elements using simple OCR model."""
        x, y = vision_agent.locate("Sign in", github_login_screenshot, model=model)
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert 0 <= x <= github_login_screenshot.width
        assert 0 <= y <= github_login_screenshot.height


@pytest.mark.parametrize(
    "model",
    [
        ModelComposition(
            [
                ModelDefinition(
                    task="e2e_ocr",
                    architecture="easy_ocr",
                    version="1",
                    interface="online_learning",
                    tags=["word_level"],
                )
            ]
        ),
        ModelComposition(
            [
                ModelDefinition(
                    task="e2e_ocr",
                    architecture="easy_ocr",
                    version="1",
                    interface="online_learning",
                    use_case="fb3b9a7b_3aea_41f7_ba02_e55fd66d1c1e",
                    tags=["trained", "word_level"],
                )
            ]
        ),
    ],
)
class TestWordLevelOcrModel:
    """Test class for word-level OCR model compositions."""

    def test_locate_with_word_level_ocr(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: ModelComposition,
    ) -> None:
        """Test locating elements using word-level OCR model."""
        x, y = vision_agent.locate("Sign", github_login_screenshot, model=model)
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert 0 <= x <= github_login_screenshot.width
        assert 0 <= y <= github_login_screenshot.height

    def test_locate_with_trained_word_level_ocr_with_non_default_text_raises(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: ModelComposition,
    ) -> None:
        if any("trained" not in m.tags for m in model):
            pytest.skip("Skipping test for non-trained model")
        with pytest.raises(Exception):  # noqa: B017
            vision_agent.locate(
                Text("Sign in", match_type="exact"),
                github_login_screenshot,
                model=model,
            )
            vision_agent.locate(
                Text("Sign in", match_type="regex"),
                github_login_screenshot,
                model=model,
            )
            vision_agent.locate(
                Text("Sign in", match_type="contains"),
                github_login_screenshot,
                model=model,
            )
            assert DEFAULT_SIMILARITY_THRESHOLD != 80
            vision_agent.locate(
                Text("Sign in", similarity_threshold=80),
                github_login_screenshot,
                model=model,
            )
