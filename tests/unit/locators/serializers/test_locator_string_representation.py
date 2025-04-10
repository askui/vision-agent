import re
from askui.locators import Class, Description, Text, Image
from PIL import Image as PILImage


TEST_IMAGE = PILImage.new("RGB", (100, 100), color="red")


def test_text_similar_str() -> None:
    text = Text("hello", match_type="similar", similarity_threshold=80)
    assert str(text) == 'text similar to "hello" (similarity >= 80%)'


def test_text_exact_str() -> None:
    text = Text("hello", match_type="exact")
    assert str(text) == 'text "hello"'


def test_text_contains_str() -> None:
    text = Text("hello", match_type="contains")
    assert str(text) == 'text containing text "hello"'


def test_text_regex_str() -> None:
    text = Text("h.*o", match_type="regex")
    assert str(text) == 'text matching regex "h.*o"'


def test_class_with_name_str() -> None:
    class_ = Class("textfield")
    assert str(class_) == 'element with class "textfield"'


def test_class_without_name_str() -> None:
    class_ = Class()
    assert str(class_) == "element that has a class"


def test_description_str() -> None:
    desc = Description("a big red button")
    assert str(desc) == 'element with description "a big red button"'


def test_text_with_above_relation_str() -> None:
    text = Text("hello")
    text.above_of(Text("world"), index=1, reference_point="center")
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. above of center of the 2nd text similar to "world" (similarity >= 70%)'
    )


def test_text_with_below_relation_str() -> None:
    text = Text("hello")
    text.below_of(Text("world"))
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. below of boundary of the 1st text similar to "world" (similarity >= 70%)'
    )


def test_text_with_right_relation_str() -> None:
    text = Text("hello")
    text.right_of(Text("world"))
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. right of boundary of the 1st text similar to "world" (similarity >= 70%)'
    )


def test_text_with_left_relation_str() -> None:
    text = Text("hello")
    text.left_of(Text("world"))
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. left of boundary of the 1st text similar to "world" (similarity >= 70%)'
    )


def test_text_with_containing_relation_str() -> None:
    text = Text("hello")
    text.containing(Text("world"))
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. containing text similar to "world" (similarity >= 70%)'
    )


def test_text_with_inside_relation_str() -> None:
    text = Text("hello")
    text.inside_of(Text("world"))
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. inside of text similar to "world" (similarity >= 70%)'
    )


def test_text_with_nearest_to_relation_str() -> None:
    text = Text("hello")
    text.nearest_to(Text("world"))
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. nearest to text similar to "world" (similarity >= 70%)'
    )


def test_text_with_and_relation_str() -> None:
    text = Text("hello")
    text.and_(Text("world"))
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. and text similar to "world" (similarity >= 70%)'
    )


def test_text_with_or_relation_str() -> None:
    text = Text("hello")
    text.or_(Text("world"))
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. or text similar to "world" (similarity >= 70%)'
    )


def test_text_with_multiple_relations_str() -> None:
    text = Text("hello")
    text.above_of(Text("world"))
    text.below_of(Text("earth"))
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. above of boundary of the 1st text similar to "world" (similarity >= 70%)\n  2. below of boundary of the 1st text similar to "earth" (similarity >= 70%)'
    )


def test_text_with_chained_relations_str() -> None:
    text = Text("hello")
    text.above_of(Text("world").below_of(Text("earth")))
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. above of boundary of the 1st text similar to "world" (similarity >= 70%)\n    1. below of boundary of the 1st text similar to "earth" (similarity >= 70%)'
    )


def test_mixed_locator_types_with_relations_str() -> None:
    text = Text("hello")
    text.above_of(Class("textfield"))
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. above of boundary of the 1st element with class "textfield"'
    )


def test_description_with_relation_str() -> None:
    desc = Description("button")
    desc.above_of(Description("input"))
    assert (
        str(desc)
        == 'element with description "button"\n  1. above of boundary of the 1st element with description "input"'
    )


def test_complex_relation_chain_str() -> None:
    text = Text("hello")
    text.above_of(
        Class("textfield")
        .right_of(Text("world", match_type="exact"))
        .and_(
            Description("input")
            .below_of(Text("earth", match_type="contains"))
            .nearest_to(Class("textfield"))
        )
    )
    assert (
        str(text)
        == 'text similar to "hello" (similarity >= 70%)\n  1. above of boundary of the 1st element with class "textfield"\n    1. right of boundary of the 1st text "world"\n    2. and element with description "input"\n      1. below of boundary of the 1st text containing text "earth"\n      2. nearest to element with class "textfield"'
    )


IMAGE_STR_PATTERN = re.compile(r'^element ".*" located by image$')


def test_image_str() -> None:
    image = Image(TEST_IMAGE)
    assert re.match(IMAGE_STR_PATTERN, str(image))


def test_image_with_name_str() -> None:
    image = Image(TEST_IMAGE, name="test_image")
    assert str(image) == 'element "test_image" located by image'


def test_image_with_relation_str() -> None:
    image = Image(TEST_IMAGE, name="image")
    image.above_of(Text("hello"))
    lines = str(image).split("\n")
    assert lines[0] == 'element "image" located by image'
    assert lines[1] == '  1. above of boundary of the 1st text similar to "hello" (similarity >= 70%)'
