import enum
import typing

import core


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


class LightSwitch(core.State):
    class Status(enum.StrEnum):
        ON = enum.auto()
        OFF = enum.auto()

    status: Status = Status.OFF

    def evolve(self, state: "LightSwitch", event: LightSwitchEvent) -> "LightSwitch":
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


class Decider(core.Decider):
    def __init__(self):
        super().__init__(initial_state=LightSwitch())

    def decide(
        self, message: core.Message, state: LightSwitch
    ) -> list[LightSwitchEvent]:
        match message:
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
                        return message
                    case LightSwitch.Status.ON:
                        return []
                return []
            case TurnOff():
                match state.status:
                    case LightSwitch.Status.OFF:
                        return []
                    case LightSwitch.Status.ON:
                        return message
                return []
            case TurnOnInitiated():
                return TurnOn()
            case TurnOffInitiated():
                return TurnOff()
            case _:
                # TODO: Fix
                typing.assert_never(message)


class SwitchClient:
    async def turn_on(self):
        ...

    async def turn_off(self):
        ...


class MessageHandler(core.MessageHandler):
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
            get_events=get_events,
            save_events=save_events,
        )
        self._switch_client = switch_client

    async def handle(self, message: core.Message) -> list[LightSwitchEvent]:
        current_state = await self._compute_current_state()
        response = self._decider.decide(message, current_state)

        event_stream = None
        match response:
            case [core.Event()]:
                # case core.EventStream():
                event_stream = response
            case TurnOn():
                event_stream = await self._turn_on()
            case TurnOff():
                event_stream = await self._turn_off()

        if event_stream:
            saved_event_stream = await self._save_events(event_stream)
            return saved_event_stream
        else:
            return None

    async def _turn_off(self):
        await self._switch_client.turn_off()
        return [SwitchedOff()]

    async def _turn_on(self):
        await self._switch_client.turn_on()
        return [SwitchedOn()]
