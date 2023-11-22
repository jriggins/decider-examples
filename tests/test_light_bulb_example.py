import functools
import typing
import pydantic

from pydantic import generics as py_generics
import pytest


############
# Core
############


class BaseModel(pydantic.BaseModel):
    def __eq__(self, other):
        if issubclass(other.__class__, self.__class__):
            return self.dict() == other.dict()
        return False


class Event(BaseModel):
    ...


class Command(BaseModel):
    ...


class State(BaseModel):
    ...


C = typing.TypeVar("C", bound=Command)
S = typing.TypeVar("S", bound=State)
E = typing.TypeVar("E", bound=Event)


class Decider(py_generics.GenericModel, py_generics.Generic[C, S, E]):
    decide: typing.Callable[[C, S], typing.Iterator[E]]
    evolve: typing.Callable[[S, E], S]
    initial_state: S


class Saga(py_generics.GenericModel, py_generics.Generic[E, C]):
    react: typing.Callable[[E], typing.Iterator[C]]


#####################
# Light Swtich Domain
#####################

#########
# Events
#########


class LightSwitchEvent(Event):
    ...


class LightSwitchedOn(LightSwitchEvent):
    ...


class LightSwitchedOff(LightSwitchEvent):
    ...


###########
# Commands
###########


class LightSwitchCommand(Command):
    ...


class SwitchLightOn(LightSwitchCommand):
    ...


class SwitchLightOff(LightSwitchCommand):
    ...

class ToggleLightSwitch(LightSwitchCommand):
    ...


###############
# States/Views
###############


class LightSwitch(State):
    @classmethod
    def evolve(cls, state: "LightSwitch", event: LightSwitchEvent) -> "LightSwitch":
        match event:
            case LightSwitchedOn():
                return LightSwitchOn()
            case LightSwitchedOff():
                return LightSwitchOff()
            case _:
                typing.assert_never(event)


class LightSwitchOn(LightSwitch):
    ...


class LightSwitchOff(LightSwitch):
    ...


class LightSwitchService:
    def light_switch_decider(
        self,
    ) -> Decider[LightSwitchCommand, LightSwitch, LightSwitchEvent]:
        def decide(
            command: LightSwitchCommand, state: LightSwitch
        ) -> typing.Iterator[LightSwitchEvent]:
            match command:
                case ToggleLightSwitch():
                    match state:
                        case LightSwitchOff():
                            return iter([LightSwitchedOn()])
                        case LightSwitchOn():
                            return iter([LightSwitchedOff()])
                        case _:
                            return typing.assert_never(state)
                case SwitchLightOn():
                    match state:
                        case LightSwitchOff():
                            return iter([LightSwitchedOn()])
                        case LightSwitchOn():
                            return iter([])
                        case _:
                            return typing.assert_never(state)
                case SwitchLightOff():
                    match state:
                        case LightSwitchOn():
                            return iter([LightSwitchedOff()])
                        case LightSwitchOff():
                            return iter([])
                        case _:
                            return typing.assert_never(state)
                case _:
                    typing.assert_never(command)

        return Decider(
            decide=decide,
            evolve=LightSwitch.evolve,
            initial_state=LightSwitchOff(),
        )

@pytest.mark.parametrize(
    "test_name, decider, initial_state, events, command, expected_events",
    [
        (
            "toggle switch when no previous events should turn on",
            LightSwitchService().light_switch_decider(),
            LightSwitchOff(),
            [],
            ToggleLightSwitch(),
            [LightSwitchedOn()],
        ),
        (
            "toggle switch when on should turn off",
            LightSwitchService().light_switch_decider(),
            LightSwitchOff(),
            [LightSwitchedOff()],
            ToggleLightSwitch(),
            [LightSwitchedOn()],
        ),
        (
            "toggle switch when off should turn on 2",
            LightSwitchService().light_switch_decider(),
            LightSwitchOff(),
            [LightSwitchedOn(), LightSwitchedOff()],
            ToggleLightSwitch(),
            [LightSwitchedOn()],
        ),
        (
            "toggle switch when on should turn off 2",
            LightSwitchService().light_switch_decider(),
            LightSwitchOff(),
            [LightSwitchedOn(), LightSwitchedOff(), LightSwitchedOn()],
            ToggleLightSwitch(),
            [LightSwitchedOff()],
        ),
    ],
)
def test_light_switch_decider(
    test_name, decider, initial_state, events, command, expected_events
):
    state = functools.reduce(lambda s, e: decider.evolve(s, e), events, initial_state)

    assert list(decider.decide(command, state)) == expected_events
