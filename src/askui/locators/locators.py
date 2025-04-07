from abc import ABC, abstractmethod
from typing import Generic, Literal, TypeVar

from askui.locators.relatable import Relatable


SerializedLocator = TypeVar("SerializedLocator")


class LocatorSerializer(Generic[SerializedLocator], ABC):
    @abstractmethod
    def serialize(self, locator: "Locator") -> SerializedLocator:
        raise NotImplementedError()


class Locator(Relatable, ABC):
    def serialize(
        self, serializer: LocatorSerializer[SerializedLocator]
    ) -> SerializedLocator:
        return serializer.serialize(self)


class Description(Locator):
    def __init__(self, description: str):
        super().__init__()
        self.description = description

    def __str__(self):
        result = f'element with description "{self.description}"'
        return result + super()._relations_str()


class Class(Locator):
    # None is used to indicate that it is an element with a class but not a specific class
    def __init__(self, class_name: Literal["text", "textfield"] | None = None):
        super().__init__()
        self.class_name = class_name

    def __str__(self):
        result = (
            f'element with class "{self.class_name}"'
            if self.class_name
            else "element that has a class"
        )
        return result + super()._relations_str()


TextMatchType = Literal["similar", "exact", "contains", "regex"]


class Text(Class):
    def __init__(
        self,
        text: str | None = None,
        match_type: TextMatchType = "similar",
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
        return result + super()._relations_str()
