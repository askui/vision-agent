from abc import ABC
from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel, Field
from typing_extensions import Self


ReferencePoint = Literal["center", "boundary", "any"]


RelationTypeMapping = {
    "above_of": "above of",
    "below_of": "below of",
    "right_of": "right of",
    "left_of": "left of",
    "and": "and",
    "or": "or",
    "containing": "containing",
    "inside_of": "inside of",
    "nearest_to": "nearest to",
}


@dataclass(kw_only=True)
class RelationBase(ABC):
    other_locator: "Relatable"
    type: Literal["above_of", "below_of", "right_of", "left_of", "and", "or", "containing", "inside_of", "nearest_to"]

    def __str__(self):
        return f"{RelationTypeMapping[self.type]} {self.other_locator}"


@dataclass(kw_only=True)
class NeighborRelation(RelationBase):
    type: Literal["above_of", "below_of", "right_of", "left_of"]
    index: int
    reference_point: ReferencePoint

    def __str__(self):
        i = self.index + 1
        if i == 11 or i == 12 or i == 13:
            index_str = f"{i}th"
        else:
            index_str = f"{i}st" if i % 10 == 1 else f"{i}nd" if i % 10 == 2 else f"{i}rd" if i % 10 == 3 else f"{i}th"
        reference_point_str = " center of" if self.reference_point == "center" else " boundary of" if self.reference_point == "boundary" else ""
        return f"{RelationTypeMapping[self.type]}{reference_point_str} the {index_str} {self.other_locator}"


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


class Relatable(BaseModel, ABC):
    """Base class for locators that can be related to other locators, e.g., spatially, logically, distance based etc.
    
    Attributes:
        relations: List of relations to other locators
    """
    relations: list[Relation] = Field(default_factory=list)

    def above_of(
        self,
        other_locator: "Relatable",
        index: int = 0,
        reference_point: ReferencePoint = "boundary",
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
        other_locator: "Relatable",
        index: int = 0,
        reference_point: ReferencePoint = "boundary",
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
        other_locator: "Relatable",
        index: int = 0,
        reference_point: ReferencePoint = "boundary",
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
        other_locator: "Relatable",
        index: int = 0,
        reference_point: ReferencePoint = "boundary",
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

    def containing(self, other_locator: "Relatable") -> Self:
        self.relations.append(
            BoundingRelation(
                type="containing",
                other_locator=other_locator,
            )
        )
        return self

    def inside_of(self, other_locator: "Relatable") -> Self:
        self.relations.append(
            BoundingRelation(
                type="inside_of",
                other_locator=other_locator,
            )
        )
        return self

    def nearest_to(self, other_locator: "Relatable") -> Self:
        self.relations.append(
            NearestToRelation(
                type="nearest_to",
                other_locator=other_locator,
            )
        )
        return self

    def and_(self, other_locator: "Relatable") -> Self:
        self.relations.append(
            LogicalRelation(
                type="and",
                other_locator=other_locator,
            )
        )
        return self

    def or_(self, other_locator: "Relatable") -> Self:
        self.relations.append(
            LogicalRelation(
                type="or",
                other_locator=other_locator,
            )
        )
        return self

    def _relations_str(self) -> str:
        if not self.relations:
            return ""
        
        result = []
        for i, relation in enumerate(self.relations):
            [other_locator_str, *nested_relation_strs] = str(relation).split("\n")
            result.append(f"  {i + 1}. {other_locator_str}")
            for nested_relation_str in nested_relation_strs:
                result.append(f"  {nested_relation_str}")
        return "\n" + "\n".join(result)
