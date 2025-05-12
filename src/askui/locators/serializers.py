from typing_extensions import NotRequired, TypedDict

from askui.models.askui.ai_element_utils import AiElementCollection
from askui.reporting import Reporter
from askui.utils.image_utils import ImageSource

from .locators import (
    DEFAULT_SIMILARITY_THRESHOLD,
    DEFAULT_TEXT_MATCH_TYPE,
    Element,
    Image,
    ImageBase,
    Prompt,
    Text,
)
from .locators import (
    AiElement as AiElementLocator,
)
from .relatable import (
    BoundingRelation,
    LogicalRelation,
    NearestToRelation,
    NeighborRelation,
    ReferencePoint,
    Relatable,
    Relation,
)


class VlmLocatorSerializer:
    def serialize(self, locator: Relatable) -> str:
        locator.raise_if_cycle()
        if len(locator._relations) > 0:
            error_msg = (
                "Serializing locators with relations is not yet supported for VLMs"
            )
            raise NotImplementedError(error_msg)

        if isinstance(locator, Text):
            return self._serialize_text(locator)
        if isinstance(locator, Element):
            return self._serialize_class(locator)
        if isinstance(locator, Prompt):
            return self._serialize_prompt(locator)
        if isinstance(locator, Image):
            error_msg = "Serializing image locators is not yet supported for VLMs"
            raise NotImplementedError(error_msg)
        if isinstance(locator, AiElementLocator):
            error_msg = "Serializing AI element locators is not yet supported for VLMs"
            raise NotImplementedError(error_msg)
        error_msg = f"Unsupported locator type: {type(locator)}"
        raise ValueError(error_msg)

    def _serialize_class(self, class_: Element) -> str:
        if class_._class_name:
            return f"an arbitrary {class_._class_name} shown"
        return "an arbitrary ui element (e.g., text, button, textfield, etc.)"

    def _serialize_prompt(self, prompt: Prompt) -> str:
        return prompt._prompt

    def _serialize_text(self, text: Text) -> str:
        if text._match_type == "similar":
            return f'text similar to "{text._text}"'

        return str(text)


class CustomElement(TypedDict):
    threshold: NotRequired[float]
    stopThreshold: NotRequired[float]
    customImage: str
    mask: NotRequired[list[tuple[float, float]]]
    rotationDegreePerStep: NotRequired[int]
    imageCompareFormat: NotRequired[str]
    name: NotRequired[str]


class AskUiSerializedLocator(TypedDict):
    instruction: str
    customElements: list[CustomElement]


class AskUiLocatorSerializer:
    _TEXT_DELIMITER = "<|string|>"
    _RP_TO_INTERSECTION_AREA_MAPPING: dict[ReferencePoint, str] = {
        "center": "element_center_line",
        "boundary": "element_edge_area",
        "any": "display_edge_area",
    }
    _RELATION_TYPE_MAPPING: dict[str, str] = {
        "above_of": "above",
        "below_of": "below",
        "right_of": "right of",
        "left_of": "left of",
        "containing": "contains",
        "inside_of": "in",
        "nearest_to": "nearest to",
        "and": "and",
        "or": "or",
    }

    def __init__(self, ai_element_collection: AiElementCollection, reporter: Reporter):
        self._ai_element_collection = ai_element_collection
        self._reporter = reporter

    def serialize(self, locator: Relatable) -> AskUiSerializedLocator:
        locator.raise_if_cycle()
        if len(locator._relations) > 1:
            # If we lift this constraint, we also have to make sure that custom element
            # references are still working + we need, e.g., some symbol or a structured
            # format to indicate precedence
            error_msg = "Serializing locators with multiple relations is not yet supported by AskUI"
            raise NotImplementedError(error_msg)

        result = AskUiSerializedLocator(instruction="", customElements=[])
        if isinstance(locator, Text):
            result["instruction"] = self._serialize_text(locator)
        elif isinstance(locator, Element):
            result["instruction"] = self._serialize_class(locator)
        elif isinstance(locator, Prompt):
            result["instruction"] = self._serialize_prompt(locator)
        elif isinstance(locator, Image):
            result = self._serialize_image(locator)
        elif isinstance(locator, AiElementLocator):
            result = self._serialize_ai_element(locator)
        else:
            error_msg = f'Unsupported locator type: "{type(locator)}"'
            raise TypeError(error_msg)

        if len(locator._relations) == 0:
            return result

        serialized_relation = self._serialize_relation(locator._relations[0])
        result["instruction"] += f" {serialized_relation['instruction']}"
        result["customElements"] += serialized_relation["customElements"]
        return result

    def _serialize_class(self, class_: Element) -> str:
        return class_._class_name or "element"

    def _serialize_prompt(self, prompt: Prompt) -> str:
        return f"pta {self._TEXT_DELIMITER}{prompt._prompt}{self._TEXT_DELIMITER}"

    def _serialize_text(self, text: Text) -> str:
        if text._text is None:
            return "text"

        match text._match_type:
            case "similar":
                if (
                    text._similarity_threshold == DEFAULT_SIMILARITY_THRESHOLD
                    and text._match_type == DEFAULT_TEXT_MATCH_TYPE
                ):
                    # Necessary so that we can use wordlevel ocr for these texts
                    return (
                        f"text {self._TEXT_DELIMITER}{text._text}{self._TEXT_DELIMITER}"
                    )
                return f"text with text {self._TEXT_DELIMITER}{text._text}{self._TEXT_DELIMITER} that matches to {text._similarity_threshold} %"  # noqa: E501
            case "exact":
                return f"text equals text {self._TEXT_DELIMITER}{text._text}{self._TEXT_DELIMITER}"  # noqa: E501
            case "contains":
                return f"text contain text {self._TEXT_DELIMITER}{text._text}{self._TEXT_DELIMITER}"  # noqa: E501
            case "regex":
                return f"text match regex pattern {self._TEXT_DELIMITER}{text._text}{self._TEXT_DELIMITER}"  # noqa: E501

    def _serialize_relation(self, relation: Relation) -> AskUiSerializedLocator:
        match relation.type:
            case "above_of" | "below_of" | "right_of" | "left_of":
                assert isinstance(relation, NeighborRelation)
                return self._serialize_neighbor_relation(relation)
            case "containing" | "inside_of" | "nearest_to" | "and" | "or":
                assert isinstance(
                    relation, LogicalRelation | BoundingRelation | NearestToRelation
                )
                return self._serialize_non_neighbor_relation(relation)

    def _serialize_neighbor_relation(
        self, relation: NeighborRelation
    ) -> AskUiSerializedLocator:
        serialized_other_locator = self.serialize(relation.other_locator)
        return AskUiSerializedLocator(
            instruction=f"index {relation.index} {self._RELATION_TYPE_MAPPING[relation.type]} intersection_area {self._RP_TO_INTERSECTION_AREA_MAPPING[relation.reference_point]} {serialized_other_locator['instruction']}",  # noqa: E501
            customElements=serialized_other_locator["customElements"],
        )

    def _serialize_non_neighbor_relation(
        self, relation: LogicalRelation | BoundingRelation | NearestToRelation
    ) -> AskUiSerializedLocator:
        serialized_other_locator = self.serialize(relation.other_locator)
        return AskUiSerializedLocator(
            instruction=f"{self._RELATION_TYPE_MAPPING[relation.type]} {serialized_other_locator['instruction']}",  # noqa: E501
            customElements=serialized_other_locator["customElements"],
        )

    def _serialize_image_to_custom_element(
        self,
        image_locator: ImageBase,
        image_source: ImageSource,
    ) -> CustomElement:
        custom_element: CustomElement = CustomElement(
            customImage=image_source.to_data_url(),
            threshold=image_locator._threshold,
            stopThreshold=image_locator._stop_threshold,
            rotationDegreePerStep=image_locator._rotation_degree_per_step,
            imageCompareFormat=image_locator._image_compare_format,
            name=image_locator._name,
        )
        if image_locator._mask:
            custom_element["mask"] = image_locator._mask
        return custom_element

    def _serialize_image_base(
        self,
        image_locator: ImageBase,
        image_sources: list[ImageSource],
    ) -> AskUiSerializedLocator:
        custom_elements: list[CustomElement] = [
            self._serialize_image_to_custom_element(
                image_locator=image_locator,
                image_source=image_source,
            )
            for image_source in image_sources
        ]
        return AskUiSerializedLocator(
            instruction=f"custom element with text {self._TEXT_DELIMITER}{image_locator._name}{self._TEXT_DELIMITER}",  # noqa: E501
            customElements=custom_elements,
        )

    def _serialize_image(
        self,
        image: Image,
    ) -> AskUiSerializedLocator:
        self._reporter.add_message(
            "AskUiLocatorSerializer",
            f"Image locator: {image}",
            image=image._image.root,
        )
        return self._serialize_image_base(
            image_locator=image,
            image_sources=[image._image],
        )

    def _serialize_ai_element(
        self, ai_element_locator: AiElementLocator
    ) -> AskUiSerializedLocator:
        ai_elements = self._ai_element_collection.find(ai_element_locator._name)
        self._reporter.add_message(
            "AskUiLocatorSerializer",
            f"Found {len(ai_elements)} ai elements named {ai_element_locator._name}",
            image=[ai_element.image for ai_element in ai_elements],
        )
        return self._serialize_image_base(
            image_locator=ai_element_locator,
            image_sources=[
                ImageSource.model_construct(root=ai_element.image)
                for ai_element in ai_elements
            ],
        )
