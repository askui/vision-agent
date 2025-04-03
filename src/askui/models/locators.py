from abc import ABC, abstractmethod
from typing import Literal, TypeVar, Generic


SerializedLocator = TypeVar('SerializedLocator')


class LocatorSerializer(Generic[SerializedLocator], ABC):
    @abstractmethod
    def serialize(self, locator: "Locator") -> SerializedLocator:
        raise NotImplementedError()


class Locator:
    def serialize(self, serializer: LocatorSerializer[SerializedLocator]) -> SerializedLocator:
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
        return f'element with class "{self.class_name}"' if self.class_name else "element that has a class"


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
    
    def serialize(self, locator: Locator) -> str:
        prefix = "Click on "
        if isinstance(locator, Text):
            return prefix + self._serialize_text(locator)
        elif isinstance(locator, Class):
            return prefix + self._serialize_class(locator)
        elif isinstance(locator, Description):
            return prefix + self._serialize_description(locator)
        else:
            raise ValueError(f"Unsupported locator type: {type(locator)}")

    def _serialize_class(self, class_: Class) -> str:
        return class_.class_name or "element"
        
    def _serialize_description(self, description: Description) -> str:
        return f'pta {self._TEXT_DELIMITER}{description.description}{self._TEXT_DELIMITER}'

    def _serialize_text(self, text: Text) -> str:
        match text.match_type:
            case "similar":
                return f'with text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER} that matches to {text.similarity_threshold} %'
            case "exact":
                return f'equals text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}'
            case "contains":
                return f'contain text {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}'
            case "regex":
                return f'match regex pattern {self._TEXT_DELIMITER}{text.text}{self._TEXT_DELIMITER}'


class VlmLocatorSerializer(LocatorSerializer[str]):
    def serialize(self, locator: Locator) -> str:
        if isinstance(locator, Text):
            return self._serialize_text(locator)
        elif isinstance(locator, Class):
            return self._serialize_class(locator)
        elif isinstance(locator, Description):
            return self._serialize_description(locator)
        else:
            raise ValueError(f"Unsupported locator type: {type(locator)}")

    def _serialize_class(self, class_: Class) -> str:
        return class_.class_name or "ui element"
        
    def _serialize_description(self, description: Description) -> str:
        return description.description

    def _serialize_text(self, text: Text) -> str:
        if text.match_type == "similar":
            return f'text similar to "{text.text}"'

        return str(text)
