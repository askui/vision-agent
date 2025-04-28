from abc import ABC
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field
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


RelationIndex = Annotated[int, Field(ge=0)]


class RelationBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    other_locator: "Relatable"
    type: Literal[
        "above_of",
        "below_of",
        "right_of",
        "left_of",
        "and",
        "or",
        "containing",
        "inside_of",
        "nearest_to",
    ]

    def __str__(self):
        return f"{RelationTypeMapping[self.type]} {self.other_locator._str_with_relation()}"


class NeighborRelation(RelationBase):
    type: Literal["above_of", "below_of", "right_of", "left_of"]
    index: RelationIndex
    reference_point: ReferencePoint

    def __str__(self):
        i = self.index + 1
        if i == 11 or i == 12 or i == 13:
            index_str = f"{i}th"
        else:
            index_str = (
                f"{i}st"
                if i % 10 == 1
                else f"{i}nd" if i % 10 == 2 else f"{i}rd" if i % 10 == 3 else f"{i}th"
            )
        reference_point_str = (
            " center of"
            if self.reference_point == "center"
            else " boundary of" if self.reference_point == "boundary" else ""
        )
        return f"{RelationTypeMapping[self.type]}{reference_point_str} the {index_str} {self.other_locator._str_with_relation()}"


class LogicalRelation(RelationBase):
    type: Literal["and", "or"]


class BoundingRelation(RelationBase):
    type: Literal["containing", "inside_of"]


class NearestToRelation(RelationBase):
    type: Literal["nearest_to"]


Relation = NeighborRelation | LogicalRelation | BoundingRelation | NearestToRelation


class CircularDependencyError(ValueError):
    """Exception raised for circular dependencies in locator relations."""

    def __init__(
        self,
        message: str = (
            "Detected circular dependency in locator relations. "
            "This occurs when locators reference each other in a way that creates an infinite loop "
            "(e.g., A is above B and B is above A)."
        ),
    ) -> None:
        super().__init__(message)


class Relatable(ABC):
    """Base class for locators that can be related to other locators, e.g., spatially, logically, distance based etc.

    Attributes:
        relations: List of relations to other locators
    """

    def __init__(self) -> None:
        self._relations: list[Relation] = []

    # cannot be validated by pydantic using @validate_call because of the recursive nature of the relations --> validate using NeighborRelation
    def above_of(
        self,
        other_locator: "Relatable",
        index: RelationIndex = 0,
        reference_point: ReferencePoint = "boundary",
    ) -> Self:
        """Defines the element (located by *self*) to be **above** another element /
        other elements (located by *other_locator*).

        An element **A** is considered to be *above* another element / other elements **B**

        - if most of **A** (or, more specifically, **A**'s bounding box) is *above* **B**
          (or, more specifically, the **top border** of **B**'s bounding box) **and**
        - if the **bottom border** of **A** (or, more specifically, **A**'s bounding box)
          is *above* the **bottom border** of **B** (or, more specifically, **B**'s
          bounding box).

        Args:
            other_locator:
                Locator for an element / elements to relate to
            index:
                Index of the element (located by *self*) above the other element(s)
                (located by *other_locator*), e.g., the first (index=0), second
                (index=1), third (index=2) etc. element above the other element(s).
                Elements' (relative) position is determined by the **bottom border**
                (*y*-coordinate) of their bounding box.  
                We don't guarantee the order of elements with the same bottom border
                (*y*-coordinate).
            reference_point:
                Defines which element (located by *self*) is considered to be above the
                other element(s) (located by *other_locator*):

                **"center"**: One point of the element (located by *self*) is above the
                  center (in a straight vertical line) of the other element(s) (located
                  by *other_locator*).
                **"boundary"**: One point of the element (located by *self*) is above
                  any other point (in a straight vertical line) of the other element(s)
                  (located by *other_locator*).
                **"any"**: No point of the element (located by *self*) has to be above
                  a point (in a straight vertical line) of the other element(s) (located
                  by *other_locator*).

                *Default is **"boundary".***

        Returns:
            Self: The locator with the relation added

        Examples:
            ```text

            ===========
            |    A    |
            ===========
            ===========
            |    B    |
            ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element above ("center" of)
            # text "B"
            text = loc.Text().above_of(loc.Text("B"), reference_point="center")
            ```
            
            ```text

                   ===========
                   |    A    |
                   ===========
            ===========
            |    B    |
            ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element above
            # ("boundary" of / any point of) text "B" 
            # (reference point "center" won't work here)
            text = loc.Text().above_of(loc.Text("B"), reference_point="boundary")
            ```
            
            ```text

                        ===========
                        |    A    |
                        ===========
            ===========
            |    B    |
            ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element above text "B" 
            # (reference point "center" or "boundary" won't work here)
            text = loc.Text().above_of(loc.Text("B"), reference_point="any")
            ```
            
            ```text

                        ===========
                        |    A    |
                        ===========
            ===========
            |    B    |
            ===========
            ===========
            |    C    |
            ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the second (index 1) element above text "C" 
            # (reference point "center" or "boundary" won't work here)
            text = loc.Text().above_of(loc.Text("C"), index=1, reference_point="any")
            ```
            
            ```text

                    ===========
                    |    A    |
                    ===========
                        ===========
            =========== |    B    |
            |         | ===========
            |    C    |
            |         |
            ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the second (index 1) element above text "C"
            # (reference point "any")
            text = loc.Text().above_of(loc.Text("C"), index=1, reference_point="any")
            # locates also text "A" as it is the first (index 0) element above text "C"
            # with reference point "boundary"
            text = loc.Text().above_of(loc.Text("C"), index=0, reference_point="boundary")
            ```
        """
        self._relations.append(
            NeighborRelation(
                type="above_of",
                other_locator=other_locator,
                index=index,
                reference_point=reference_point,
            )
        )
        return self

    # cannot be validated by pydantic using @validate_call because of the recursive nature of the relations --> validate using NeighborRelation
    def below_of(
        self,
        other_locator: "Relatable",
        index: RelationIndex = 0,
        reference_point: ReferencePoint = "boundary",
    ) -> Self:
        """Defines the element (located by *self*) to be **below** another element /
        other elements (located by *other_locator*).

        An element **A** is considered to be *below* another element / other elements **B**

        - if most of **A** (or, more specifically, **A**'s bounding box) is *below* **B**
          (or, more specifically, the **bottom border** of **B**'s bounding box) **and**
        - if the **top border** of **A** (or, more specifically, **A**'s bounding box) is
          *below* the **top border** of **B** (or, more specifically, **B**'s bounding
          box).

        Args:
            other_locator:
                Locator for an element / elements to relate to.
            index:
                Index of the element (located by *self*) **below** the other
                element(s) (located by *other_locator*), e.g., the first (*index=0*),
                second (*index=1*), third (*index=2*) etc. element below the other
                element(s).  Elements' (relative) position is determined by the **top
                border** (*y*-coordinate) of their bounding box.  
                We don't guarantee the order of elements with the same top border
                (*y*-coordinate).
            reference_point:
                Defines which element (located by *self*) is considered to be
                *below* the other element(s) (located by *other_locator*):
                
                **"center"**: One point of the element (located by *self*) is
                  **below** the *center* (in a straight vertical line) of the other
                  element(s) (located by *other_locator*).
                **"boundary"**: One point of the element (located by *self*) is
                  **below** *any* other point (in a straight vertical line) of the
                  other element(s) (located by *other_locator*).
                **"any"**: No point of the element (located by *self*) has to
                  be **below** a point (in a straight vertical line) of the other
                  element(s) (located by *other_locator*).

                *Default is **"boundary".***

        Returns:
            Self: The locator with the relation added.

        Examples:
            ```text

            ===========
            |    B    |
            ===========
            ===========
            |    A    |
            ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element below ("center" of)
            # text "B"
            text = loc.Text().below_of(loc.Text("B"), reference_point="center")
            ```

            ```text

            ===========
            |    B    |
            ===========
                   ===========
                   |    A    |
                   ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element below 
            # ("boundary" of / any point of) text "B" 
            # (reference point "center" won't work here)
            text = loc.Text().below_of(loc.Text("B"), reference_point="boundary")
            ```

            ```text

            ===========
            |    B    |
            ===========
                        ===========
                        |    A    |
                        ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element below text "B"
            # (reference point "center" or "boundary won't work here)
            text = loc.Text().below_of(loc.Text("B"), reference_point="any")
            ```
            
            ```text

            ===========
            |    C    |
            ===========
            ===========
            |    B    |
            ===========
                        ===========
                        |    A    |
                        ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the second (index 1) element below text "C" 
            # (reference point "center" or "boundary" won't work here)
            text = loc.Text().below_of(loc.Text("C"), index=1, reference_point="any")
            ```
            
            ```text

            =========== 
            |         | 
            |    C    |
            |         |===========
            ===========|    B    |
                       ===========
                    ===========
                    |    A    |
                    ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the second (index 1) element below text "C"
            # (reference point "any")
            text = loc.Text().below_of(loc.Text("C"), index=1, reference_point="any")
            # locates also text "A" as it is the first (index 0) element below text "C"
            # with reference point "boundary"
            text = loc.Text().below_of(loc.Text("C"), index=0, reference_point="boundary")
            ```
        """
        self._relations.append(
            NeighborRelation(
                type="below_of",
                other_locator=other_locator,
                index=index,
                reference_point=reference_point,
            )
        )
        return self

    # cannot be validated by pydantic using @validate_call because of the recursive nature of the relations --> validate using NeighborRelation
    def right_of(
        self,
        other_locator: "Relatable",
        index: RelationIndex = 0,
        reference_point: ReferencePoint = "center",
    ) -> Self:
        """Defines the element (located by *self*) to be **right of** another element /
        other elements (located by *other_locator*).

        An element **A** is considered to be *right of* another element / other elements **B**

        - if most of **A** (or, more specifically, **A**'s bounding box) is *right of* **B**
          (or, more specifically, the **right border** of **B**'s bounding box) **and**
        - if the **left border** of **A** (or, more specifically, **A**'s bounding box) is
          *right of* the **left border** of **B** (or, more specifically, **B**'s
          bounding box).

        Args:
            other_locator:
                Locator for an element / elements to relate to.
            index:
                Index of the element (located by *self*) **right of** the other
                element(s) (located by *other_locator*), e.g., the first (*index=0*),
                second (*index=1*), third (*index=2*) etc. element right of the other
                element(s).  Elements' (relative) position is determined by the **left
                border** (*x*-coordinate) of their bounding box.  
                We don't guarantee the order of elements with the same left border
                (*x*-coordinate).
            reference_point:
                Defines which element (located by *self*) is considered to be
                *right of* the other element(s) (located by *other_locator*):

                **"center"**: One point of the element (located by *self*) is
                  **right of** the *center* (in a straight horizontal line) of the
                  other element(s) (located by *other_locator*).
                **"boundary"**: One point of the element (located by *self*) is
                  **right of** *any* other point (in a straight horizontal line) of
                  the other element(s) (located by *other_locator*).
                **"any"**: No point of the element (located by *self*) has to
                  be **right of** a point (in a straight horizontal line) of the
                  other element(s) (located by *other_locator*).

                *Default is **"center".***

        Returns:
            Self: The locator with the relation added.

        Examples:
            ```text

            =========== ===========
            |    B    | |    A    |
            =========== ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element right of ("center"
            # of) text "B"
            text = loc.Text().right_of(loc.Text("B"), reference_point="center")
            ```

            ```text

            =========== 
            |    B    | 
            =========== ===========
                        |    A    |
                        ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element right of 
            # ("boundary" of / any point of) text "B" 
            # (reference point "center" won't work here)
            text = loc.Text().right_of(loc.Text("B"), reference_point="boundary")
            ```

            ```text

            =========== 
            |    B    |
            ===========
                        ===========
                        |    A    |
                        ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element right of text "B" 
            # (reference point "center" or "boundary" won't work here)
            text = loc.Text().right_of(loc.Text("B"), reference_point="any")
            ```
            
            ```text
     
                                    ===========
                                    |    A    |
                                    ===========
            =========== ===========
            |    C    | |    B    |
            =========== ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the second (index 1) element right of text "C" 
            # (reference point "center" or "boundary" won't work here)
            text = loc.Text().right_of(loc.Text("C"), index=1, reference_point="any")
            ```
            
            ```text
            
                    ===========
                    |    B    |
                    =========== ===========
            ===========         |    A    |
            |    C    |         ===========
            ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the second (index 1) element right of text "C"
            # (reference point "any")
            text = loc.Text().right_of(loc.Text("C"), index=1, reference_point="any")
            # locates also text "A" as it is the first (index 0) element right of text
            # "C" with reference point "boundary"
            text = loc.Text().right_of(loc.Text("C"), index=0, reference_point="boundary")
            ```
        """
        self._relations.append(
            NeighborRelation(
                type="right_of",
                other_locator=other_locator,
                index=index,
                reference_point=reference_point,
            )
        )
        return self

    # cannot be validated by pydantic using @validate_call because of the recursive nature of the relations --> validate using NeighborRelation
    def left_of(
        self,
        other_locator: "Relatable",
        index: RelationIndex = 0,
        reference_point: ReferencePoint = "center",
    ) -> Self:
        """Defines the element (located by *self*) to be **left of** another element /
        other elements (located by *other_locator*).

        An element **A** is considered to be *left of* another element / other elements **B**

        - if most of **A** (or, more specifically, **A**'s bounding box) is *left of* **B**
          (or, more specifically, the **left border** of **B**'s bounding box) **and**
        - if the **right border** of **A** (or, more specifically, **A**'s bounding box) is
          *left of* the **right border** of **B** (or, more specifically, **B**'s
          bounding box).

        Args:
            other_locator:
                Locator for an element / elements to relate to.
            index:
                Index of the element (located by *self*) **left of** the other
                element(s) (located by *other_locator*), e.g., the first (*index=0*),
                second (*index=1*), third (*index=2*) etc. element left of the other
                element(s).  Elements' (relative) position is determined by the **right
                border** (*x*-coordinate) of their bounding box.  
                We don't guarantee the order of elements with the same right border
                (*x*-coordinate).
            reference_point:
                Defines which element (located by *self*) is considered to be
                *left of* the other element(s) (located by *other_locator*):

                **"center"**  : One point of the element (located by *self*) is
                  **left of** the *center* (in a straight horizontal line) of the
                  other element(s) (located by *other_locator*).
                **"boundary"**: One point of the element (located by *self*) is
                  **left of** *any* other point (in a straight horizontal line) of
                  the other element(s) (located by *other_locator*).
                **"any"**     : No point of the element (located by *self*) has to
                  be **left of** a point (in a straight horizontal line) of the
                  other element(s) (located by *other_locator*).

                *Default is **"center".***

        Returns:
            Self: The locator with the relation added.

        Examples:
            ```text

            =========== ===========
            |    A    | |    B    |
            =========== ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element left of ("center"
            # of) text "B"
            text = loc.Text().left_of(loc.Text("B"), reference_point="center")
            ```

            ```text

                        =========== 
            =========== |    B    |
            |    A    | =========== 
            ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element left of ("boundary"
            # of / any point of) text "B"
            # (reference point "center" won't work here)
            text = loc.Text().left_of(loc.Text("B"), reference_point="boundary")
            ```

            ```text

                        =========== 
                        |    B    |
                        =========== 
            ===========              
            |    A    |
            =========== 
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the first (index 0) element left of text "B" 
            # (reference point "center" or "boundary won't work here)
            text = loc.Text().left_of(loc.Text("B"), reference_point="any")
            ```

            ```text
     
            ===========
            |    A    |
            ===========
                        =========== ===========
                        |    B    | |    C    |
                        =========== ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the second (index 1) element left of text "C" 
            # (reference point "center" or "boundary" won't work here)
            text = loc.Text().left_of(loc.Text("C"), index=1, reference_point="any")
            ```
            
            ```text
             
                        ===========
                        |    B    |
            =========== =========== 
            |    A    |        ===========         
            ===========        |    C    |         
                               ===========
            ```
            ```python
            from askui import locators as loc
            # locates text "A" as it is the second (index 1) element left of text "C"
            # (reference point "any")
            text = loc.Text().left_of(loc.Text("C"), index=1, reference_point="any")
            # locates also text "A" as it is the first (index 0) element right of text
            # "C" with reference point "boundary"
            text = loc.Text().right_of(loc.Text("C"), index=0, reference_point="boundary")
            ```
        """
        self._relations.append(
            NeighborRelation(
                type="left_of",
                other_locator=other_locator,
                index=index,
                reference_point=reference_point,
            )
        )
        return self

    # cannot be validated by pydantic using @validate_call because of the recursive nature of the relations --> validate using BoundingRelation
    def containing(self, other_locator: "Relatable") -> Self:
        """Defines the element (located by *self*) to contain another element (located
        by *other_locator*).

        Args:
            other_locator: The locator to check if it's contained

        Returns:
            Self: The locator with the relation added

        Examples:
            ```text
            ---------------------------
            |     textfield           |
            |  ---------------------  |
            |  |  placeholder text |  |
            |  ---------------------  |
            |                         |
            ---------------------------
            ```
            ```python
            from askui import locators as loc

            # Returns the textfield because it contains the placeholder text
            textfield = loc.Element("textfield").containing(loc.Text("placeholder"))
            ```
        """
        self._relations.append(
            BoundingRelation(
                type="containing",
                other_locator=other_locator,
            )
        )
        return self

    # cannot be validated by pydantic using @validate_call because of the recursive nature of the relations --> validate using BoundingRelation
    def inside_of(self, other_locator: "Relatable") -> Self:
        """Defines the element (located by *self*) to be inside of another element
        (located by *other_locator*).

        Args:
            other_locator: The locator to check if it contains this element

        Returns:
            Self: The locator with the relation added

        Examples:
            ```text
            ---------------------------
            |     textfield           |
            |  ---------------------  |
            |  |  placeholder text |  |
            |  ---------------------  |
            |                         |
            ---------------------------
            ```
            ```python
            from askui import locators as loc

            # Returns the placeholder text of the textfield
            placeholder_text = loc.Text("placeholder").inside_of(
                loc.Element("textfield")
            )
            ```
        """
        self._relations.append(
            BoundingRelation(
                type="inside_of",
                other_locator=other_locator,
            )
        )
        return self

    # cannot be validated by pydantic using @validate_call because of the recursive nature of the relations --> validate using NearestToRelation
    def nearest_to(self, other_locator: "Relatable") -> Self:
        """Defines the element (located by *self*) to be the nearest to another element
        (located by *other_locator*).

        Args:
            other_locator: The locator to compare distance against

        Returns:
            Self: The locator with the relation added

        Examples:
            ```text
            --------------
            |    text    |
            --------------
            ---------------
            | textfield 1 |
            ---------------




            ---------------
            | textfield 2 |
            ---------------
            ```
            ```python
            from askui import locators as loc

            # Returns textfield 1 because it is nearer to the text than textfield 2
            textfield = loc.Element("textfield").nearest_to(loc.Text())
            ```
        """
        self._relations.append(
            NearestToRelation(
                type="nearest_to",
                other_locator=other_locator,
            )
        )
        return self

    # cannot be validated by pydantic using @validate_call because of the recursive nature of the relations --> validate using LogicalRelation
    def and_(self, other_locator: "Relatable") -> Self:
        """Logical and operator to combine multiple locators, e.g., to require an
        element to match multiple locators.

        Args:
            other_locator: The locator to combine with

        Returns:
            Self: The locator with the relation added

        Examples:
            ```python
            from askui import locators as loc

            # Searches for an element that contains the text "Google" and is a
            # multi-colored Google logo (instead of, e.g., simply some text that says
            # "Google")
            icon_user = loc.Element().containing(
                loc.Text("Google").and_(loc.Description("Multi-colored Google logo"))
            )
            ```
        """
        self._relations.append(
            LogicalRelation(
                type="and",
                other_locator=other_locator,
            )
        )
        return self

    # cannot be validated by pydantic using @validate_call because of the recursive nature of the relations --> validate using LogicalRelation
    def or_(self, other_locator: "Relatable") -> Self:
        """Logical or operator to combine multiple locators, e.g., to provide a fallback
        if no element is found for one of the locators.

        Args:
            other_locator: The locator to combine with

        Returns:
            Self: The locator with the relation added

        Examples:
            ```python
            from askui import locators as loc

            # Searches for element using a description and if the element cannot be
            # found, searches for it using an image
            search_icon = loc.Description("search icon").or_(
                loc.Image("search_icon.png")
            )
            ```
        """
        self._relations.append(
            LogicalRelation(
                type="or",
                other_locator=other_locator,
            )
        )
        return self

    def _str(self) -> str:
        return "relatable"

    def _relations_str(self) -> str:
        if not self._relations:
            return ""

        result = []
        for i, relation in enumerate(self._relations):
            [other_locator_str, *nested_relation_strs] = str(relation).split("\n")
            result.append(f"  {i + 1}. {other_locator_str}")
            for nested_relation_str in nested_relation_strs:
                result.append(f"  {nested_relation_str}")
        return "\n" + "\n".join(result)
    
    def _str_with_relation(self) -> str:
        return self._str() + self._relations_str()

    def raise_if_cycle(self) -> None:
        """Raises CircularDependencyError if the relations form a cycle (see [Cycle (graph theory)](https://en.wikipedia.org/wiki/Cycle_(graph_theory)))."""
        if self._has_cycle():
            raise CircularDependencyError()

    def _has_cycle(self) -> bool:
        """Check if the relations form a cycle (see [Cycle (graph theory)](https://en.wikipedia.org/wiki/Cycle_(graph_theory)))."""
        visited_ids: set[int] = set()
        recursion_stack_ids: set[int] = set()

        def _dfs(node: Relatable) -> bool:
            node_id = id(node)
            if node_id in recursion_stack_ids:
                return True
            if node_id in visited_ids:
                return False

            visited_ids.add(node_id)
            recursion_stack_ids.add(node_id)

            for relation in node._relations:
                if _dfs(relation.other_locator):
                    return True

            recursion_stack_ids.remove(node_id)
            return False

        return _dfs(self)

    def __str__(self) -> str:
        self.raise_if_cycle()
        return self._str_with_relation()
