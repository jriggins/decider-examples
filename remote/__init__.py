import enum
import typing

import core
import switch_controller as sc


class SwitchedOn(core.Event):
    ...


class SwitchedOff(core.Event):
    ...


class ToggleSwitchInitiated(core.Event):
    ...


class ToggleSwitchSent(core.Event):
    ...


class ToggleSwitch(core.Command):
    ...


class SendToggleSwitch(core.Command):
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


class Decider(core.Decider):
    def __init__(self):
        super().__init__(initial_state=Switch())

    def decide(self, message: typing.Any, state: typing.Any):
        match message:
            case SendToggleSwitch():
                return message
                # return core.DelegatedCommand(command=message)
            case ToggleSwitch():
                return core.EventStream.from_list([ToggleSwitchInitiated()])
            case MarkSwitchedOn():
                return core.EventStream.from_list([SwitchedOn()])
            case MarkSwitchedOff():
                return core.EventStream.from_list([SwitchedOff()])


class SwitchControllerClient:
    async def toggle_switch(self) -> list[SwitchEvent]:
        return []


class MessageHandler:
    def __init__(
        self, get_events, save_events, switch_controller_client: SwitchControllerClient
    ):
        self._decider = Decider()
        self._get_events = get_events
        self._save_events = save_events
        self._switch_controller_client = switch_controller_client

    async def handle(self, message: core.Message):
        response = self._decider.decide(message, None)

        event_stream = None
        match response:
            case core.EventStream():
                event_stream = response
            case SendToggleSwitch():
                event_stream = await self._send_toggle_switch()

        if event_stream:
            saved_event_stream = await self._save_events(event_stream)
            return saved_event_stream
        else:
            return None

    async def _send_toggle_switch(self):
        return await self._switch_controller_client.toggle_switch()
