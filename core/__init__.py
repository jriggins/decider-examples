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


class NoneReactor(Reactor):
    def react(self, action_result: AR) -> list[A]:
        return []


NONE_REACTOR = NoneReactor()


class Aggregate(abc.ABC, typing.Generic[C, S, E]):
    def __init__(
        self,
        decider: Decider[C, S, E],
        get_events: typing.Callable[[], typing.Awaitable[list[E]]],
        save_events: typing.Callable[
            [typing.Iterable[E]],
            typing.Awaitable[typing.Iterable[E]],
        ],
        reactor: Reactor[E, C] = NONE_REACTOR,
    ):
        super().__init__()
        self._decider = decider
        self._reactor = reactor
        self._get_events = get_events
        self._save_events = save_events

    async def _compute_current_state(self):
        events = await self._get_events()
        return functools.reduce(
            self._decider.evolve, events, self._decider.initial_state
        )

    @abc.abstractmethod
    async def handle(self, command: C) -> list[E]:
        ...

    async def compute_new_events_by_orchestrating(self, command: C) -> list[E]:
        current_state = await self._compute_current_state()
        new_events = self._compute_new_events(command, current_state)
        extra_events = await self._compute_new_events_from_orchestration(new_events)
        new_events.extend(extra_events)

        # TODO: make returns Iterables
        return list(await self._save_events(new_events))

    async def _compute_new_events_from_orchestration(self, resulting_events):
        es = []
        for event in resulting_events:
            commands = self._reactor.react(event)
            for command in commands:
                es.extend(await self.handle(command))
        return es

    def _compute_new_events(self, command, current_state):
        resulting_events = self._decider.decide(command, current_state)
        return resulting_events
