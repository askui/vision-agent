import math
from collections.abc import Callable
from typing import Any

# Tool = TypeVar("Tool", bound=Callable[..., Any])


# class Agent(Generic[Tool]):
#     def __init__(self, tools: list[Tool]) -> None:
#         for tool in tools:
#             setattr(self, tool.__name__, tool)


def add(a: int, b: int) -> int:
    return a + b


def subtract(a: int, b: int) -> int:
    return a - b


# class MathAgent(Protocol):
#     add: type[add]


# def make_agent(tools: list[Tool]) -> Agent[Tool] & Protocol:


# agent = Agent([add, subtract])

# print(agent.add(1, 2))
# print(agent.subtract(1, 2))


# class X:
#     pass

# X.add = staticmethod(add)


# def greet(self):
#     print(f"Hi, I'm {self.name}!")

# def set_name(self, name):
#     self.name = name

# def make_person_class():
#     return type('Person', (object,), {
#         'greet': greet,
#         'set_name': set_name,
#     })

# Person = make_person_class()


# person = Person()

# person.greet()


class ToolsBase:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}
        for attr in dir(self):
            if attr.startswith("_"):
                continue
            val = getattr(self, attr)
            if callable(val):
                self._tools[attr] = val


class Tools(ToolsBase):
    add = staticmethod(add)
    subtract = staticmethod(subtract)
    floor = staticmethod(math.floor)


# T = TypeVar("T")


# class Agent(Generic[T]):
#     def __init__(self, tools: T) -> None:
#         self.tools = tools


class MathAgent(Tools):
    pass


math_agent = MathAgent()

math_agent.add


# agent = Agent({
#     'add': add,
#     'subtract': subtract,
#     'floor': math.floor,
# })

# print(agent.tools['add'](1, 2))
# print(agent.tools['subtract'](1, 2))



class Agent:

