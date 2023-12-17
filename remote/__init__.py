import enum
import typing
from typing import Any, Coroutine

import core

import switch_controller as sc


class SwitchedOn(core.Event):
    ...


class SwitchedOff(core.Event):
    ...


class ToggleSwitchInitiated(core.Event):
    ...


class ToggleSwitch(core.Command):
    ...


class MarkSwitchedOn(core.Command):
    ...


class MarkSwitchedOff(core.Command):
    ...


SwitchEvent: typing.TypeAlias = ToggleSwitchInitiated | SwitchedOn | SwitchedOff

SwitchCommand: typing.TypeAlias = ToggleSwitch | MarkSwitchedOn | MarkSwitchedOff

SwitchControllerEvent: typing.TypeAlias = sc.SwitchedOn | sc.SwitchedOff


class Switch(core.State):
    class Status(enum.StrEnum):
        OFF = enum.auto()
        ON = enum.auto()

    status: Status = Status.OFF

    def evolve(self, state: typing.Self, event: SwitchEvent) -> typing.Self:
        match event:
            case SwitchedOn():
                return state.copy(update=dict(status=self.Status.ON))
            case SwitchedOff():
                return state.copy(update=dict(status=self.Status.OFF))
            case ToggleSwitchInitiated():
                return state
            case _:
                typing.assert_never(event)
        return self


class Decider(core.Decider[SwitchCommand, Switch, SwitchEvent]):
    def __init__(self):
        super().__init__(initial_state=Switch())

    def decide(self, command: SwitchCommand, state: Switch) -> list[SwitchEvent]:
        match command:
            case ToggleSwitch():
                return [ToggleSwitchInitiated()]
            case MarkSwitchedOn():
                return [SwitchedOn()]
            case MarkSwitchedOff():
                return [SwitchedOff()]
            case _:
                typing.assert_never(command)


class Reactor(core.Reactor[SwitchControllerEvent, SwitchCommand]):
    def react(self, action_result: SwitchControllerEvent) -> list[SwitchCommand]:
        match action_result:
            case sc.SwitchedOn():
                return [MarkSwitchedOn()]
            case sc.SwitchedOff():
                return [MarkSwitchedOff()]
            case _:
                typing.assert_never(action_result)


class SwitchControllerClient:
    async def toggle_switch(self):
        ...


class Aggregate(core.Aggregate[SwitchCommand, Switch, SwitchEvent]):
    def __init__(
        self, get_events, save_events, switch_controller_client: SwitchControllerClient
    ):
        self._get_events = get_events
        self._save_events = save_events
        self._switch_controller_client = switch_controller_client

    async def handle(self, command: SwitchCommand) -> list[SwitchEvent]:
        return [ToggleSwitchInitiated()]
