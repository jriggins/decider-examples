import enum
import typing
import core


class LightSwitch(core.State):
    class Status(enum.StrEnum):
        ON = enum.auto()
        OFF = enum.auto()

    status: Status = Status.OFF


class LightSwitchedOff(core.Event):
    ...


class LightSwitchedOn(core.Event):
    ...


LightSwitchEvent = typing.TypeVar("LightSwitchEvent", LightSwitchedOff, LightSwitchedOn)


class ToggleLightSwitch(core.Command):
    ...


LightSwitchCommand = typing.TypeVar("LightSwitchCommand", bound=ToggleLightSwitch)


class LightSwitchControllerDecider:
    def evolve(self, state: LightSwitch, event: LightSwitchEvent) -> LightSwitch:
        match event:
            case LightSwitchedOn():
                return state.copy(update={"status": LightSwitch.Status.ON})
            case LightSwitchedOff():
                return state.copy(update={"status": LightSwitch.Status.OFF})
            case _:
                typing.assert_never(event)

    def decide(
        self, command: LightSwitchCommand, state: LightSwitch
    ) -> list[core.Event]:
        match command:
            case ToggleLightSwitch():
                match state.status:
                    case LightSwitch.Status.ON:
                        return [LightSwitchedOff()]
                    case LightSwitch.Status.OFF:
                        return [LightSwitchedOn()]
                    case _:
                        typing.assert_never(state.status)
            case _:
                typing.assert_never(command)

    @property
    def initial_state(self) -> LightSwitch:
        return LightSwitch()
