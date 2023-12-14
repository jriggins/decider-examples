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


class Reactor(abc.ABC, typing.Generic[AR, A]):
    @abc.abstractmethod
    def react(self, action_result: AR) -> list[A]:
        ...


class Aggregate(abc.ABC, typing.Generic[C, S, E]):
    # def __new__(cls):
    #     cls.toggle_switch = lambda self, command: self.handle(command)
    #     cls.test_handle = lambda self, command: self.handle(command)

    def __init__(
        self,
        decider: Decider[C, S, E],
        get_events: typing.Callable[[], typing.Awaitable[list[E]]],
        reactor: Reactor[E, C],
    ):
        super().__init__()
        self._decider = decider
        self._reactor = reactor
        self._get_events = get_events

    @abc.abstractmethod
    async def handle(self, command: C) -> list[E]:
        ...

    async def compute_new_events_by_orchestrating(self, command: C) -> list[E]:
        events = await self._get_events()
        current_state = functools.reduce(
            self._decider.evolve, events, self._decider.initial_state
        )
        resulting_events = self._decider.decide(command, current_state)
        es = []
        for event in resulting_events:
            commands = self._reactor.react(event)
            for command in commands:
                es.extend(await self.handle(command))
        resulting_events.extend(es)

        return resulting_events
