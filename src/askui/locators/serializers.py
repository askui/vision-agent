from typing_extensions import NotRequired, TypedDict

from askui.locators.image_utils import ImageSource
from askui.models.askui.ai_element_utils import AiElementCollection, AiElementNotFound
from .locators import (
    ImageMetadata,
    AiElement as AiElementLocator,
    Class,
    Description,
    Image,
    Text,
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
        if len(locator.relations) > 0:
            raise NotImplementedError(
                "Serializing locators with relations is not yet supported for VLMs"
            )

        if isinstance(locator, Text):
            return self._serialize_text(locator)
        elif isinstance(locator, Class):
            return self._serialize_class(locator)
        elif isinstance(locator, Description):
            return self._serialize_description(locator)
        elif isinstance(locator, Image):
            raise NotImplementedError(
                "Serializing image locators is not yet supported for VLMs"
            )
        else:
            raise ValueError(f"Unsupported locator type: {type(locator)}")

    def _serialize_class(self, class_: Class) -> str:
        if class_.class_name:
            return f"an arbitrary {class_.class_name} shown"
        else:
            return "an arbitrary ui element (e.g., text, button, textfield, etc.)"

    def _serialize_description(self, description: Description) -> str:
        return description.description

    def _serialize_text(self, text: Text) -> str:
        if text.match_type == "similar":
            return f'text similar to "{text.text}"'

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

    def __init__(self, ai_element_collection: AiElementCollection):
        self._ai_element_collection = ai_element_collection

    def serialize(self, locator: Relatable) -> AskUiSerializedLocator:
        locator.raise_if_cycle()
        if len(locator.relations) > 1:
            # If we lift this constraint, we also have to make sure that custom element references are still working + we need, e.g., some symbol or a structured format to indicate precedence
            raise NotImplementedError(
                "Serializing locators with multiple relations is not yet supported by AskUI"
            )

        result = AskUiSerializedLocator(instruction="", customElements=[])
        if isinstance(locator, Text):
            result["instruction"] = self._serialize_text(locator)
        elif isinstance(locator, Class):
            result["instruction"] = self._serialize_class(locator)
        elif isinstance(locator, Description):
            result["instruction"] = self._serialize_description(locator)
        elif isinstance(locator, Image):
            result = self._serialize_image(
                image_metadata=locator,
                image_sources=[locator.image],
            )
        elif isinstance(locator, AiElementLocator):
            result = self._serialize_ai_element(locator)
        else:
            raise ValueError(f'Unsupported locator type: "{type(locator)}"')

        if len(locator.relations) == 0:
            return result

        serialized_relation = self._serialize_relation(locator.relations[0])
        result["instruction"] += f" {serialized_relation['instruction']}"
        result["customElements"] += serialized_relation["customElements"]
        return result

    def _serialize_class(self, class_: Class) -> str:
        return class_.class_name or "element"

    def _serialize_description(self, description: Description) -> str:
        return (
            f"pta {self._TEXT_DELIMITER}{description.description}{self._TEXT_DELIMITER}"
        )

    def _serialize_text(self, text: Text) -> str:
        match text.match_type:
            case "similar":
                return f"text with text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER} that matches to {text.similarity_threshold} %"
            case "exact":
                return f"text equals text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}"
            case "contains":
                return f"text contain text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}"
            case "regex":
                return f"text match regex pattern {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}"
            case _:
                raise ValueError(f'Unsupported text match type: "{text.match_type}"')

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
            case _:
                raise ValueError(f'Unsupported relation type: "{relation.type}"')

    def _serialize_neighbor_relation(
        self, relation: NeighborRelation
    ) -> AskUiSerializedLocator:
        serialized_other_locator = self.serialize(relation.other_locator)
        return AskUiSerializedLocator(
            instruction=f"index {relation.index} {self._RELATION_TYPE_MAPPING[relation.type]} intersection_area {self._RP_TO_INTERSECTION_AREA_MAPPING[relation.reference_point]} {serialized_other_locator['instruction']}",
            customElements=serialized_other_locator["customElements"],
        )

    def _serialize_non_neighbor_relation(
        self, relation: LogicalRelation | BoundingRelation | NearestToRelation
    ) -> AskUiSerializedLocator:
        serialized_other_locator = self.serialize(relation.other_locator)
        return AskUiSerializedLocator(
            instruction=f"{self._RELATION_TYPE_MAPPING[relation.type]} {serialized_other_locator['instruction']}",
            customElements=serialized_other_locator["customElements"],
        )

    def _serialize_image_to_custom_element(
        self,
        image_metadata: ImageMetadata,
        image_source: ImageSource,
    ) -> CustomElement:
        custom_element: CustomElement = CustomElement(
            customImage=image_source.to_data_url(),
            threshold=image_metadata.threshold,
            stopThreshold=image_metadata.stop_threshold,
            rotationDegreePerStep=image_metadata.rotation_degree_per_step,
            imageCompareFormat=image_metadata.image_compare_format,
            name=image_metadata.name,
        )
        if image_metadata.mask:
            custom_element["mask"] = image_metadata.mask
        return custom_element

    def _serialize_image(
        self,
        image_metadata: ImageMetadata,
        image_sources: list[ImageSource],
    ) -> AskUiSerializedLocator:
        custom_elements: list[CustomElement] = [
            self._serialize_image_to_custom_element(
                image_metadata=image_metadata,
                image_source=image_source,
            )
            for image_source in image_sources
        ]
        return AskUiSerializedLocator(
            instruction=f"custom element with text {self._TEXT_DELIMITER}{image_metadata.name}{self._TEXT_DELIMITER}",
            customElements=custom_elements,
        )

    def _serialize_ai_element(
        self, ai_element_locator: AiElementLocator
    ) -> AskUiSerializedLocator:
        ai_elements = self._ai_element_collection.find(ai_element_locator.name)
        if len(ai_elements) == 0:
            raise AiElementNotFound(
                f"Could not find AI element with name \"{ai_element_locator.name}\""
            )
        return self._serialize_image(
            image_metadata=ai_element_locator,
            image_sources=[ImageSource.model_construct(root=ai_element.image) for ai_element in ai_elements],
        )
