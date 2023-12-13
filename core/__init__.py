import abc
import typing
import pydantic


class BaseModel(pydantic.BaseModel):
    def __eq__(self, other):
        if issubclass(other.__class__, self.__class__):
            return self.dict() == other.dict()
        return False


class Message(BaseModel, abc.ABC):
    ...


class Command(Message, abc.ABC):
    ...


class Event(Message, abc.ABC):
    ...


class State(BaseModel, abc.ABC):
    ...


C = typing.TypeVar("C")
S = typing.TypeVar("S")
E = typing.TypeVar("E")
A = typing.TypeVar("A")
AR = typing.TypeVar("AR")


class Decider(abc.ABC, typing.Generic[C, S, E]):
    def __init__(self, initial_state: S):
        self.initial_state = initial_state

    @abc.abstractmethod
    def evolve(self, state: S, event: E) -> S:
        ...

    @abc.abstractmethod
    def decide(self, command: C, state: S) -> list[E]:
        ...


class Reactor(abc.ABC, typing.Generic[A, AR]):
    @abc.abstractmethod
    def react(self, action_result: AR) -> list[A]:
        ...
