import abc
import functools
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


M = typing.TypeVar("M", covariant=False)
R = typing.TypeVar("R", covariant=False)
C = typing.TypeVar("C", covariant=False)
S = typing.TypeVar("S", covariant=False)
E = typing.TypeVar("E", covariant=False)
A = typing.TypeVar("A", covariant=False)
AR = typing.TypeVar("AR", covariant=False)


class State(abc.ABC, BaseModel, typing.Generic[S, E]):
    initial_state: S | None = None

    @abc.abstractmethod
    def evolve(self, state: S, event: S) -> S:
        ...


class DeciderResponse(BaseModel):
    ...


class EventStream(DeciderResponse, typing.Generic[E]):
    events: typing.List[E]

    @classmethod
    def from_list(cls, events=list[E]) -> typing.Self:
        return cls(events=events)


class DelegatedCommand(DeciderResponse):
    command: Command


class Decider(abc.ABC, typing.Generic[M, S, E, R]):
    def __init__(self, initial_state: S):
        self.initial_state = initial_state

    def evolve(self, state: S, event: E) -> S:
        return self.initial_state.evolve(state, event)  # type: ignore

    @abc.abstractmethod
    def decide(self, message: M, state: S) -> R:
        ...


class MessageHandler(abc.ABC, typing.Generic[M, S, E, R]):
    def __init__(
        self,
        decider: Decider[M, S, E, R],
        get_events: typing.Callable[[], typing.Awaitable[list[E]]],
        save_events: typing.Callable[
            [typing.Iterable[E]],
            typing.Awaitable[typing.Iterable[E]],
        ],
    ):
        self._decider = decider
        self._get_events = get_events
        self._save_events = save_events

    @abc.abstractmethod
    async def handle(self, message: M) -> list[E]:
        ...

    async def _compute_current_state(self):
        events = await self._get_events()
        return functools.reduce(
            self._decider.evolve, events, self._decider.initial_state
        )
