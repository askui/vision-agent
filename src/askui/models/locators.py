from abc import ABC, abstractmethod
from typing import Literal, TypeVar, Generic
from typing_extensions import Self
from dataclasses import dataclass


SerializedLocator = TypeVar("SerializedLocator")


ReferencePoint = Literal["center", "boundary", "any"]


@dataclass(kw_only=True)
class RelationBase(ABC):
    other_locator: "Locator"

    def __str__(self):
        return f"{self.type} {self.other_locator}"


@dataclass(kw_only=True)
class NeighborRelation(RelationBase):
    type: Literal["above_of", "below_of", "right_of", "left_of"]
    index: int
    reference_point: ReferencePoint

    def __str__(self):
        return f"{self.type} {self.other_locator} at index {self.index} in reference to {self.reference_point}"


@dataclass(kw_only=True)
class LogicalRelation(RelationBase):
    type: Literal["and", "or"]


@dataclass(kw_only=True)
class BoundingRelation(RelationBase):
    type: Literal["containing", "inside_of"]


@dataclass(kw_only=True)
class NearestToRelation(RelationBase):
    type: Literal["nearest_to"]


Relation = NeighborRelation | LogicalRelation | BoundingRelation | NearestToRelation


class LocatorSerializer(Generic[SerializedLocator], ABC):
    @abstractmethod
    def serialize(self, locator: "Locator") -> SerializedLocator:
        raise NotImplementedError()


class Relatable(ABC):
    def __init__(self) -> None:
        self.relations: list[Relation] = []

    def above_of(
        self,
        other_locator: "Locator",
        index: int = 0,
        reference_point: Literal["center", "boundary", "any"] = "boundary",
    ) -> Self:
        self.relations.append(
            NeighborRelation(
                type="above_of",
                other_locator=other_locator,
                index=index,
                reference_point=reference_point,
            )
        )
        return self

    def below_of(
        self,
        other_locator: "Locator",
        index: int = 0,
        reference_point: Literal["center", "boundary", "any"] = "boundary",
    ) -> Self:
        self.relations.append(
            NeighborRelation(
                type="below_of",
                other_locator=other_locator,
                index=index,
                reference_point=reference_point,
            )
        )
        return self

    def right_of(
        self,
        other_locator: "Locator",
        index: int = 0,
        reference_point: Literal["center", "boundary", "any"] = "boundary",
    ) -> Self:
        self.relations.append(
            NeighborRelation(
                type="right_of",
                other_locator=other_locator,
                index=index,
                reference_point=reference_point,
            )
        )
        return self

    def left_of(
        self,
        other_locator: "Locator",
        index: int = 0,
        reference_point: Literal["center", "boundary", "any"] = "boundary",
    ) -> Self:
        self.relations.append(
            NeighborRelation(
                type="left_of",
                other_locator=other_locator,
                index=index,
                reference_point=reference_point,
            )
        )
        return self

    def containing(self, other_locator: "Locator") -> Self:
        self.relations.append(
            BoundingRelation(
                type="containing",
                other_locator=other_locator,
            )
        )
        return self

    def inside_of(self, other_locator: "Locator") -> Self:
        self.relations.append(
            BoundingRelation(
                type="inside_of",
                other_locator=other_locator,
            )
        )
        return self

    def nearest_to(self, other_locator: "Locator") -> Self:
        self.relations.append(
            NearestToRelation(
                type="nearest_to",
                other_locator=other_locator,
            )
        )
        return self

    def and_(self, other_locator: "Locator") -> Self:
        self.relations.append(
            LogicalRelation(
                type="and",
                other_locator=other_locator,
            )
        )
        return self

    def or_(self, other_locator: "Locator") -> Self:
        self.relations.append(
            LogicalRelation(
                type="or",
                other_locator=other_locator,
            )
        )
        return self


class Locator(Relatable, ABC):
    def serialize(
        self, serializer: LocatorSerializer[SerializedLocator]
    ) -> SerializedLocator:
        return serializer.serialize(self)


class Description(Locator):
    def __init__(self, description: str):
        self.description = description

    def __str__(self):
        return f'element with description "{self.description}"'


class Class(Locator):
    # None is used to indicate that it is an element with a class but not a specific class
    def __init__(self, class_name: Literal["text", "textfield"] | None = None):
        self.class_name = class_name

    def __str__(self):
        return (
            f'element with class "{self.class_name}"'
            if self.class_name
            else "element that has a class"
        )


class Text(Class):
    def __init__(
        self,
        text: str | None = None,
        match_type: Literal["similar", "exact", "contains", "regex"] = "similar",
        similarity_threshold: int = 70,
    ):
        super().__init__(class_name="text")
        self.text = text
        self.match_type = match_type
        self.similarity_threshold = similarity_threshold

    def __str__(self):
        result = "text "
        match self.match_type:
            case "similar":
                result += f'similar to "{self.text}" (similarity >= {self.similarity_threshold}%)'
            case "exact":
                result += f'"{self.text}"'
            case "contains":
                result += f'containing text "{self.text}"'
            case "regex":
                result += f'matching regex "{self.text}"'
        return result


class AskUiLocatorSerializer(LocatorSerializer[str]):
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
        "inside_of": "inside",
        "nearest_to": "nearest to",
        "and": "and",
        "or": "or",
    }

    def serialize(self, locator: Locator) -> str:
        if len(locator.relations) > 1:
            raise NotImplementedError(
                "Serializing locators with multiple relations is not yet supported by AskUI"
            )

        prefix = "Click on "
        if isinstance(locator, Text):
            serialized = prefix + self._serialize_text(locator)
        elif isinstance(locator, Class):
            serialized = prefix + self._serialize_class(locator)
        elif isinstance(locator, Description):
            serialized = prefix + self._serialize_description(locator)
        else:
            raise ValueError(f"Unsupported locator type: {type(locator)}")

        if len(locator.relations) == 0:
            return serialized

        return serialized + " " + self._serialize_relation(locator.relations[0])

    def _serialize_class(self, class_: Class) -> str:
        return class_.class_name or "element"

    def _serialize_description(self, description: Description) -> str:
        return (
            f"pta {self._TEXT_DELIMITER}{description.description}{self._TEXT_DELIMITER}"
        )

    def _serialize_text(self, text: Text) -> str:
        match text.match_type:
            case "similar":
                return f"with text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER} that matches to {text.similarity_threshold} %"
            case "exact":
                return f"equals text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}"
            case "contains":
                return f"contain text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}"
            case "regex":
                return f"match regex pattern {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}"

    def _serialize_relation(self, relation: Relation) -> str:
        match relation.type:
            case "above_of" | "below_of" | "right_of" | "left_of":
                assert isinstance(relation, NeighborRelation)
                return self._serialize_neighbor_relation(relation)
            case "containing" | "inside_of" | "nearest_to" | "and" | "or":
                return f"{self._RELATION_TYPE_MAPPING[relation.type]} {self.serialize(relation.other_locator)}"
            case _:
                raise ValueError(f"Unsupported relation type: {relation.type}")

    def _serialize_neighbor_relation(self, relation: NeighborRelation) -> str:
        return f"index {relation.index} {self._RELATION_TYPE_MAPPING[relation.type]} intersection_area {self._RP_TO_INTERSECTION_AREA_MAPPING[relation.reference_point]} {self.serialize(relation.other_locator)}"


class VlmLocatorSerializer(LocatorSerializer[str]):
    def serialize(self, locator: Locator) -> str:
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
