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

    def evolve(self, state: "LightSwitch", event: "LightSwitchEvent") -> "LightSwitch":
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


class Decider(core.Decider):
    def __init__(self):
        super().__init__(initial_state=LightSwitch())

    def evolve(self, state: LightSwitch, event: LightSwitchEvent) -> LightSwitch:
        return self.initial_state.evolve(state, event)

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
                match state.status:
                    case LightSwitch.Status.OFF:
                        return [TurnOnInitiated()]
                    case LightSwitch.Status.ON:
                        return []
                return []
            case TurnOff():
                match state.status:
                    case LightSwitch.Status.OFF:
                        return []
                    case LightSwitch.Status.ON:
                        return [TurnOffInitiated()]
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


class Aggregate(core.Aggregate):
    def __init__(
        self,
        get_events: typing.Callable[[], typing.Awaitable[list[LightSwitchEvent]]],
        save_events: typing.Callable[
            [typing.Iterable[LightSwitchEvent]],
            typing.Awaitable[typing.Iterable[LightSwitchEvent]],
        ],
        switch_client: SwitchClient,
    ):
        super().__init__(
            decider=Decider(),
            reactor=Reactor(),
            get_events=get_events,
            save_events=save_events,
        )
        self._switch_client = switch_client

    async def handle(self, command: core.Command) -> list[LightSwitchEvent]:
        match command:
            case TurnOn():
                await self._switch_client.turn_on()
                return [SwitchedOn()]
            case TurnOff():
                await self._switch_client.turn_off()
                return [SwitchedOff()]
            case ToggleLightSwitch():
                return await self.compute_state_change_with_reaction(command)
            case _:
                return []
