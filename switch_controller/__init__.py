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


# I originally wanted to make LightSwitchEvent an abstract base class but could
# not figure out how to get mypy to not expect it as a possible value in
# exhaustiveness checks. :/
LightSwitchEvent: typing.TypeAlias = LightSwitchedOff | LightSwitchedOn


class ToggleLightSwitch(core.Command):
    ...


LightSwitchCommand: typing.TypeAlias = ToggleLightSwitch


class LightSwitchControllerDecider(
    core.Decider[LightSwitchCommand, LightSwitch, LightSwitchEvent]
):
    def __init__(self):
        super().__init__(initial_state=LightSwitch())

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
    ) -> list[LightSwitchEvent]:
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
