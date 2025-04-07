from .locators import Class, Description, LocatorSerializer, Text
from .relatable import NeighborRelation, ReferencePoint, Relatable, Relation


class VlmLocatorSerializer(LocatorSerializer[str]):
    def serialize(self, locator: Relatable) -> str:
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

    def serialize(self, locator: Relatable) -> str:
        if len(locator.relations) > 1:
            raise NotImplementedError(
                "Serializing locators with multiple relations is not yet supported by AskUI"
            )

        if isinstance(locator, Text):
            serialized = self._serialize_text(locator)
        elif isinstance(locator, Class):
            serialized = self._serialize_class(locator)
        elif isinstance(locator, Description):
            serialized = self._serialize_description(locator)
        else:
            raise ValueError(f"Unsupported locator type: \"{type(locator)}\"")

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
                return f"text with text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER} that matches to {text.similarity_threshold} %"
            case "exact":
                return f"text equals text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}"
            case "contains":
                return f"text contain text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}"
            case "regex":
                return f"text match regex pattern {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}"
            case _:
                raise ValueError(f"Unsupported text match type: \"{text.match_type}\"")

    def _serialize_relation(self, relation: Relation) -> str:
        match relation.type:
            case "above_of" | "below_of" | "right_of" | "left_of":
                assert isinstance(relation, NeighborRelation)
                return self._serialize_neighbor_relation(relation)
            case "containing" | "inside_of" | "nearest_to" | "and" | "or":
                return f"{self._RELATION_TYPE_MAPPING[relation.type]} {self.serialize(relation.other_locator)}"
            case _:
                raise ValueError(f"Unsupported relation type: \"{relation.type}\"")

    def _serialize_neighbor_relation(self, relation: NeighborRelation) -> str:
        return f"index {relation.index} {self._RELATION_TYPE_MAPPING[relation.type]} intersection_area {self._RP_TO_INTERSECTION_AREA_MAPPING[relation.reference_point]} {self.serialize(relation.other_locator)}"
