from dataclasses import dataclass
from typing import Literal
import pytest

from askui.locators import Class, Description, Locator, Text
from askui.locators.relatable import RelationBase
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer


@pytest.fixture
def askui_serializer() -> AskUiLocatorSerializer:
    return AskUiLocatorSerializer()


@pytest.fixture
def vlm_serializer() -> VlmLocatorSerializer:
    return VlmLocatorSerializer()


class TestAskUiLocatorSerializer:
    def test_serialize_text_similar(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello", match_type="similar", similarity_threshold=80)
        result = askui_serializer.serialize(text)
        assert result == 'text with text <|string|>hello<|string|> that matches to 80 %'

    def test_serialize_text_exact(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello", match_type="exact")
        result = askui_serializer.serialize(text)
        assert result == 'text equals text <|string|>hello<|string|>'

    def test_serialize_text_contains(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello", match_type="contains")
        result = askui_serializer.serialize(text)
        assert result == 'text contain text <|string|>hello<|string|>'

    def test_serialize_text_regex(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("h.*o", match_type="regex")
        result = askui_serializer.serialize(text)
        assert result == 'text match regex pattern <|string|>h.*o<|string|>'

    def test_serialize_class_no_name(self, askui_serializer: AskUiLocatorSerializer) -> None:
        class_ = Class()
        result = askui_serializer.serialize(class_)
        assert result == 'element'

    def test_serialize_description(self, askui_serializer: AskUiLocatorSerializer) -> None:
        desc = Description("a big red button")
        result = askui_serializer.serialize(desc)
        assert result == 'pta <|string|>a big red button<|string|>'

    def test_serialize_above_relation(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello")
        text.above_of(Text("world"), index=1, reference_point="center")
        result = askui_serializer.serialize(text)
        assert result == 'text with text <|string|>hello<|string|> that matches to 70 % index 1 above intersection_area element_center_line text with text <|string|>world<|string|> that matches to 70 %'

    def test_serialize_below_relation(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello")
        text.below_of(Text("world"))
        result = askui_serializer.serialize(text)
        assert result == 'text with text <|string|>hello<|string|> that matches to 70 % index 0 below intersection_area element_edge_area text with text <|string|>world<|string|> that matches to 70 %'

    def test_serialize_right_relation(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello")
        text.right_of(Text("world"))
        result = askui_serializer.serialize(text)
        assert result == 'text with text <|string|>hello<|string|> that matches to 70 % index 0 right of intersection_area element_edge_area text with text <|string|>world<|string|> that matches to 70 %'

    def test_serialize_left_relation(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello")
        text.left_of(Text("world"))
        result = askui_serializer.serialize(text)
        assert result == 'text with text <|string|>hello<|string|> that matches to 70 % index 0 left of intersection_area element_edge_area text with text <|string|>world<|string|> that matches to 70 %'

    def test_serialize_containing_relation(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello")
        text.containing(Text("world"))
        result = askui_serializer.serialize(text)
        assert result == 'text with text <|string|>hello<|string|> that matches to 70 % contains text with text <|string|>world<|string|> that matches to 70 %'

    def test_serialize_inside_relation(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello")
        text.inside_of(Text("world"))
        result = askui_serializer.serialize(text)
        assert result == 'text with text <|string|>hello<|string|> that matches to 70 % in text with text <|string|>world<|string|> that matches to 70 %'

    def test_serialize_nearest_to_relation(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello")
        text.nearest_to(Text("world"))
        result = askui_serializer.serialize(text)
        assert result == 'text with text <|string|>hello<|string|> that matches to 70 % nearest to text with text <|string|>world<|string|> that matches to 70 %'

    def test_serialize_and_relation(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello")
        text.and_(Text("world"))
        result = askui_serializer.serialize(text)
        assert result == 'text with text <|string|>hello<|string|> that matches to 70 % and text with text <|string|>world<|string|> that matches to 70 %'

    def test_serialize_or_relation(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello")
        text.or_(Text("world"))
        result = askui_serializer.serialize(text)
        assert result == 'text with text <|string|>hello<|string|> that matches to 70 % or text with text <|string|>world<|string|> that matches to 70 %'

    def test_serialize_multiple_relations_raises(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello")
        text.above_of(Text("world"))
        text.below_of(Text("earth"))
        with pytest.raises(NotImplementedError, match="Serializing locators with multiple relations is not yet supported by AskUI"):
            askui_serializer.serialize(text)

    def test_serialize_relations_chain(self, askui_serializer: AskUiLocatorSerializer) -> None:
        text = Text("hello")
        text.above_of(Text("world").below_of(Text("earth")))
        result = askui_serializer.serialize(text)
        assert result == 'text with text <|string|>hello<|string|> that matches to 70 % index 0 above intersection_area element_edge_area text with text <|string|>world<|string|> that matches to 70 % index 0 below intersection_area element_edge_area text with text <|string|>earth<|string|> that matches to 70 %'

    def test_serialize_unsupported_locator_type(self, askui_serializer: AskUiLocatorSerializer) -> None:
        class UnsupportedLocator(Locator):
            pass
        
        with pytest.raises(ValueError, match="Unsupported locator type:.*"):
            askui_serializer.serialize(UnsupportedLocator())

    def test_serialize_unsupported_relation_type(self, askui_serializer: AskUiLocatorSerializer) -> None:
        @dataclass(kw_only=True)
        class UnsupportedRelation(RelationBase):
            type: Literal["unsupported"]
        
        text = Text("hello")
        text.relations.append(UnsupportedRelation(type="unsupported", other_locator=Text("world")))
        
        with pytest.raises(ValueError, match="Unsupported relation type: \"unsupported\""):
            askui_serializer.serialize(text)


class TestVlmLocatorSerializer:
    def test_serialize_text_similar(self, vlm_serializer: VlmLocatorSerializer) -> None:
        text = Text("hello", match_type="similar", similarity_threshold=80)
        result = vlm_serializer.serialize(text)
        assert result == 'text similar to "hello"'

    def test_serialize_text_exact(self, vlm_serializer: VlmLocatorSerializer) -> None:
        text = Text("hello", match_type="exact")
        result = vlm_serializer.serialize(text)
        assert result == 'text "hello"'

    def test_serialize_text_contains(self, vlm_serializer: VlmLocatorSerializer) -> None:
        text = Text("hello", match_type="contains")
        result = vlm_serializer.serialize(text)
        assert result == 'text containing text "hello"'

    def test_serialize_text_regex(self, vlm_serializer: VlmLocatorSerializer) -> None:
        text = Text("h.*o", match_type="regex")
        result = vlm_serializer.serialize(text)
        assert result == 'text matching regex "h.*o"'

    def test_serialize_class(self, vlm_serializer: VlmLocatorSerializer) -> None:
        class_ = Class("textfield")
        result = vlm_serializer.serialize(class_)
        assert result == 'an arbitrary textfield shown'

    def test_serialize_class_no_name(self, vlm_serializer: VlmLocatorSerializer) -> None:
        class_ = Class()
        result = vlm_serializer.serialize(class_)
        assert result == 'an arbitrary ui element (e.g., text, button, textfield, etc.)'

    def test_serialize_description(self, vlm_serializer: VlmLocatorSerializer) -> None:
        desc = Description("a big red button")
        result = vlm_serializer.serialize(desc)
        assert result == 'a big red button'

    def test_serialize_with_relation_raises(self, vlm_serializer: VlmLocatorSerializer) -> None:
        text = Text("hello")
        text.above_of(Text("world"))
        with pytest.raises(NotImplementedError, match="Serializing locators with relations is not yet supported for VLMs"):
            vlm_serializer.serialize(text)

    def test_serialize_unsupported_locator_type(self, vlm_serializer: VlmLocatorSerializer) -> None:
        class UnsupportedLocator(Locator):
            pass
        
        with pytest.raises(ValueError, match="Unsupported locator type:.*"):
            vlm_serializer.serialize(UnsupportedLocator())


class TestLocatorStringRepresentation:
    def test_text_similar_str(self) -> None:
        text = Text("hello", match_type="similar", similarity_threshold=80)
        assert str(text) == 'text similar to "hello" (similarity >= 80%)'

    def test_text_exact_str(self) -> None:
        text = Text("hello", match_type="exact")
        assert str(text) == 'text "hello"'

    def test_text_contains_str(self) -> None:
        text = Text("hello", match_type="contains")
        assert str(text) == 'text containing text "hello"'

    def test_text_regex_str(self) -> None:
        text = Text("h.*o", match_type="regex")
        assert str(text) == 'text matching regex "h.*o"'

    def test_class_with_name_str(self) -> None:
        class_ = Class("textfield")
        assert str(class_) == 'element with class "textfield"'

    def test_class_without_name_str(self) -> None:
        class_ = Class()
        assert str(class_) == 'element that has a class'

    def test_description_str(self) -> None:
        desc = Description("a big red button")
        assert str(desc) == 'element with description "a big red button"'

    def test_text_with_above_relation_str(self) -> None:
        text = Text("hello")
        text.above_of(Text("world"), index=1, reference_point="center")
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. above of center of the 2nd text similar to "world" (similarity >= 70%)'

    def test_text_with_below_relation_str(self) -> None:
        text = Text("hello")
        text.below_of(Text("world"))
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. below of boundary of the 1st text similar to "world" (similarity >= 70%)'

    def test_text_with_right_relation_str(self) -> None:
        text = Text("hello")
        text.right_of(Text("world"))
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. right of boundary of the 1st text similar to "world" (similarity >= 70%)'

    def test_text_with_left_relation_str(self) -> None:
        text = Text("hello")
        text.left_of(Text("world"))
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. left of boundary of the 1st text similar to "world" (similarity >= 70%)'

    def test_text_with_containing_relation_str(self) -> None:
        text = Text("hello")
        text.containing(Text("world"))
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. containing text similar to "world" (similarity >= 70%)'

    def test_text_with_inside_relation_str(self) -> None:
        text = Text("hello")
        text.inside_of(Text("world"))
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. inside of text similar to "world" (similarity >= 70%)'

    def test_text_with_nearest_to_relation_str(self) -> None:
        text = Text("hello")
        text.nearest_to(Text("world"))
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. nearest to text similar to "world" (similarity >= 70%)'

    def test_text_with_and_relation_str(self) -> None:
        text = Text("hello")
        text.and_(Text("world"))
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. and text similar to "world" (similarity >= 70%)'

    def test_text_with_or_relation_str(self) -> None:
        text = Text("hello")
        text.or_(Text("world"))
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. or text similar to "world" (similarity >= 70%)'

    def test_text_with_multiple_relations_str(self) -> None:
        text = Text("hello")
        text.above_of(Text("world"))
        text.below_of(Text("earth"))
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. above of boundary of the 1st text similar to "world" (similarity >= 70%)\n  2. below of boundary of the 1st text similar to "earth" (similarity >= 70%)'

    def test_text_with_chained_relations_str(self) -> None:
        text = Text("hello")
        text.above_of(Text("world").below_of(Text("earth")))
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. above of boundary of the 1st text similar to "world" (similarity >= 70%)\n    1. below of boundary of the 1st text similar to "earth" (similarity >= 70%)'

    def test_mixed_locator_types_with_relations_str(self) -> None:
        text = Text("hello")
        text.above_of(Class("textfield"))
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. above of boundary of the 1st element with class "textfield"'

    def test_description_with_relation_str(self) -> None:
        desc = Description("button")
        desc.above_of(Description("input"))
        assert str(desc) == 'element with description "button"\n  1. above of boundary of the 1st element with description "input"'

    def test_complex_relation_chain_str(self) -> None:
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
        assert str(text) == 'text similar to "hello" (similarity >= 70%)\n  1. above of boundary of the 1st element with class "textfield"\n    1. right of boundary of the 1st text "world"\n    2. and element with description "input"\n      1. below of boundary of the 1st text containing text "earth"\n      2. nearest to element with class "textfield"'
