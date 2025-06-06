"""Tests for VisionAgent.locate() with different locator types and models"""

import pathlib

import pytest
from PIL import Image as PILImage

from askui.agent import VisionAgent
from askui.locators import Element, Image, Prompt, Text
from askui.locators.locators import AiElement
from askui.models.exceptions import ElementNotFoundError


@pytest.mark.parametrize(
    "model",
    [
        "askui",
    ],
)
class TestVisionAgentLocateWithRelations:
    """Test class for VisionAgent.locate() method with relations."""

    def test_locate_with_above_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using above_of relation."""
        locator = Text("Forgot password?").above_of(Element("textfield"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_below_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using below_of relation."""
        locator = Text("Forgot password?").below_of(Element("textfield"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_right_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using right_of relation."""
        locator = Text("Forgot password?").right_of(Text("Password"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_left_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using left_of relation."""
        locator = Text("Password").left_of(Text("Forgot password?"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 450
        assert 190 <= y <= 260

    def test_locate_with_containing_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using containing relation."""
        locator = Element("textfield").containing(Text("github.com/login"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 50 <= x <= 860
        assert 0 <= y <= 80

    def test_locate_with_inside_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using inside_of relation."""
        locator = Text("github.com/login").inside_of(Element("textfield"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 70 <= x <= 200
        assert 10 <= y <= 75

    def test_locate_with_nearest_to_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using nearest_to relation."""
        locator = Element("textfield").nearest_to(Text("Password"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 210 <= y <= 280

    @pytest.mark.skip("Skipping tests for now because it is failing for unknown reason")
    def test_locate_with_and_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using and_ relation."""
        locator = Text("Forgot password?").and_(Element("text"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_or_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using or_ relation."""
        locator = Element("textfield").nearest_to(
            Text("Password").or_(Text("Username or email address"))
        )
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 160 <= y <= 280

    def test_locate_with_relation_index(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using relation with index."""
        locator = Element("textfield").below_of(
            Text("Username or email address"), index=0
        )
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 160 <= y <= 230

    def test_locate_with_relation_index_greater_0(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using relation with index."""
        locator = Element("textfield").below_of(Element("textfield"), index=1)
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 210 <= y <= 280

    @pytest.mark.skip("Skipping tests for now because it is failing for unknown reason")
    def test_locate_with_relation_index_greater_1(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using relation with index."""
        locator = Text("Sign in").below_of(Text(), index=4, reference_point="any")
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 420 <= x <= 500
        assert 250 <= y <= 310

    def test_locate_with_relation_reference_point_center(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using relation with center reference point."""
        locator = Text("Forgot password?").right_of(
            Text("Password"), reference_point="center"
        )
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_relation_reference_point_center_raises_when_element_cannot_be_located(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using relation with center reference point."""
        locator = Text("Sign in").below_of(Text("Password"), reference_point="center")
        with pytest.raises(ElementNotFoundError):
            vision_agent.locate(locator, github_login_screenshot, model=model)

    def test_locate_with_relation_reference_point_boundary(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using relation with boundary reference point."""
        locator = Text("Forgot password?").right_of(
            Text("Password"), reference_point="boundary"
        )
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_relation_reference_point_boundary_raises_when_element_cannot_be_located(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using relation with boundary reference point."""
        locator = Text("Sign in").below_of(Text("Password"), reference_point="boundary")
        with pytest.raises(ElementNotFoundError):
            vision_agent.locate(locator, github_login_screenshot, model=model)

    def test_locate_with_relation_reference_point_any(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using relation with any reference point."""
        locator = Text("Sign in").below_of(Text("Password"), reference_point="any")
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 420 <= x <= 500
        assert 250 <= y <= 310

    def test_locate_with_multiple_relations_with_same_locator_raises(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using multiple relations with same locator which is not supported by AskUI."""
        locator = (
            Text("Forgot password?")
            .below_of(Element("textfield"))
            .below_of(Element("textfield"))
        )
        with pytest.raises(NotImplementedError):
            vision_agent.locate(locator, github_login_screenshot, model=model)

    def test_locate_with_chained_relations(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using chained relations."""
        locator = Text("Sign in").below_of(
            Text("Password").below_of(Text("Username or email address")),
            reference_point="any",
        )
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 420 <= x <= 500
        assert 250 <= y <= 310

    def test_locate_with_relation_different_locator_types(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using relation with different locator types."""
        locator = Text("Sign in").below_of(
            Element("textfield").below_of(Text("Username or email address")),
            reference_point="center",
        )
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 420 <= x <= 500
        assert 250 <= y <= 310

    def test_locate_with_description_and_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using description with relation."""
        locator = Prompt("Sign in button").below_of(Prompt("Password field"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    @pytest.mark.skip("Skipping tests for now because it is failing for unknown reason")
    def test_locate_with_description_and_complex_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using description with relation."""
        locator = Prompt("Sign in button").below_of(
            Element("textfield").below_of(Text("Password"))
        )
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    def test_locate_with_image_and_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
        path_fixtures: pathlib.Path,
    ) -> None:
        """Test locating elements using image locator with relation."""
        image_path = path_fixtures / "images" / "github_com__signin__button.png"
        image = PILImage.open(image_path)
        locator = Image(image=image).containing(Text("Sign in"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    def test_locate_with_image_in_relation_to_other_image(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
        path_fixtures: pathlib.Path,
    ) -> None:
        """Test locating elements using image locator with relation."""
        github_icon_image_path = path_fixtures / "images" / "github_com__icon.png"
        signin_button_image_path = (
            path_fixtures / "images" / "github_com__signin__button.png"
        )
        github_icon_image = PILImage.open(github_icon_image_path)
        signin_button_image = PILImage.open(signin_button_image_path)
        github_icon = Image(image=github_icon_image)
        signin_button = Image(image=signin_button_image).below_of(github_icon)
        x, y = vision_agent.locate(signin_button, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    def test_locate_with_image_and_complex_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
        path_fixtures: pathlib.Path,
    ) -> None:
        """Test locating elements using image locator with complex relation."""
        image_path = path_fixtures / "images" / "github_com__signin__button.png"
        image = PILImage.open(image_path)
        locator = Image(image=image).below_of(
            Element("textfield").below_of(Text("Password"))
        )
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    def test_locate_with_ai_element_locator_relation(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using an AI element locator with relation."""
        icon_locator = AiElement("github_com__icon")
        signin_locator = AiElement("github_com__signin__button")
        x, y = vision_agent.locate(
            signin_locator.below_of(icon_locator), github_login_screenshot, model=model
        )
        assert 350 <= x <= 570
        assert 240 <= y <= 320
