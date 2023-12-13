import enum
import functools
import itertools
import typing

import core


class LightSwitch(core.State):
    class Status(enum.StrEnum):
        ON = enum.auto()
        OFF = enum.auto()

    status: Status = Status.OFF


class TurnOnInitiated(core.Event):
    ...


class TurnOffInitiated(core.Event):
    ...


class SwitchedOff(core.Event):
    ...


class SwitchedOn(core.Event):
    ...


# I originally wanted to make LightSwitchEvent an abstract base class but could
# not figure out how to get mypy to not expect it as a possible value in
# exhaustiveness checks. :/
LightSwitchEvent: typing.TypeAlias = (
    TurnOnInitiated | TurnOffInitiated | SwitchedOff | SwitchedOn
)


class ToggleLightSwitch(core.Command):
    ...


class TurnOn(core.Command):
    ...


class TurnOff(core.Command):
    ...


LightSwitchCommand: typing.TypeAlias = ToggleLightSwitch | TurnOn | TurnOff


class LightSwitchControllerDecider(
    core.Decider[LightSwitchCommand, LightSwitch, LightSwitchEvent]
):
    def __init__(self):
        super().__init__(initial_state=LightSwitch())

    def evolve(self, state: LightSwitch, event: LightSwitchEvent) -> LightSwitch:
        match event:
            case TurnOnInitiated():
                return state
            case TurnOffInitiated():
                return state
            case SwitchedOn():
                return state.copy(update={"status": LightSwitch.Status.ON})
            case SwitchedOff():
                return state.copy(update={"status": LightSwitch.Status.OFF})
            case _:
                typing.assert_never(event)

    def decide(
        self, command: LightSwitchCommand, state: LightSwitch
    ) -> list[LightSwitchEvent]:
        match command:
            case ToggleLightSwitch():
                match state.status:
                    case LightSwitch.Status.OFF:
                        return [TurnOnInitiated()]
                    case LightSwitch.Status.ON:
                        return [TurnOffInitiated()]
                    case _:
                        typing.assert_never(state.status)
            case TurnOn():
                return []
            case TurnOff():
                return []
            case _:
                typing.assert_never(command)


class Reactor(core.Reactor):
    def react(self, action_result: core.Message) -> list[core.Message]:
        match action_result:
            case TurnOnInitiated():
                return [TurnOn()]
            case TurnOffInitiated():
                return [TurnOff()]
            case _:
                return []


class SwitchClient:
    async def turn_on(self):
        ...

    async def turn_off(self):
        ...


class Aggregate:
    # def __new__(cls):
    #     cls.toggle_switch = lambda self, command: self.handle(command)
    #     cls.test_handle = lambda self, command: self.handle(command)

    def __init__(
        self,
        get_events: typing.Callable[
            [], typing.Awaitable[typing.Iterable[LightSwitchEvent]]
        ],
        switch_client: SwitchClient,
    ):
        self._decider = LightSwitchControllerDecider()
        self._reactor = Reactor()
        self._get_events = get_events
        self._switch_client = switch_client

    async def handle(self, message: core.Message) -> list[LightSwitchEvent]:
        match message:
            case TurnOn():
                await self._switch_client.turn_on()
                return [SwitchedOn()]
            case TurnOff():
                await self._switch_client.turn_off()
                return [SwitchedOff()]
            case ToggleLightSwitch():
                events = await self._get_events()
                current_state = functools.reduce(
                    self._decider.evolve,
                    events,
                    self._decider.initial_state,
                )
                resulting_events = self._decider.decide(message, current_state)
                es = []
                for event in resulting_events:
                    commands = self._reactor.react(event)
                    for command in commands:
                        es.extend(await self.handle(command))
                resulting_events.extend(es)
                return resulting_events
            case _:
                return []
