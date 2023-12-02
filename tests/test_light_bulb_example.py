import functools
import typing
import pydantic

from pydantic import generics as py_generics
import pytest


############
# Core
############

V = typing.TypeVar("V")


# class Result(typing.Generic[V]):
#     def __init__(self, value: V):
#         self._value = value

#     def bind(self, f: typing.Callable) -> "Result[V]":
#         ...

# class Success(Result[V]):
#     def bind(self, f: typing.Callable) -> "Result[V]":
#         return


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


class ToggleLightSwitchAttemptFailed(LightSwitchEvent):
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


class LightSwitchAdapter:
    def turn_on(self) -> bool:
        return True

    def turn_off(self) -> bool:
        return True


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
        self, light_switch_adapter: LightSwitchAdapter
    ) -> Decider[LightSwitchCommand, LightSwitch, LightSwitchEvent]:
        def decide(
            command: LightSwitchCommand, state: LightSwitch
        ) -> typing.Iterator[LightSwitchEvent]:
            match command:
                case ToggleLightSwitch():
                    match state:
                        case LightSwitchOff():
                            if light_switch_adapter.turn_on():
                                return iter([LightSwitchedOn()])
                            else:
                                return iter([ToggleLightSwitchAttemptFailed()])
                        case LightSwitchOn():
                            if light_switch_adapter.turn_off():
                                return iter([LightSwitchedOff()])
                            else:
                                return iter([ToggleLightSwitchAttemptFailed()])
                        case _:
                            return typing.assert_never(state)
                case _:
                    typing.assert_never(command)

        return Decider(
            decide=decide,
            evolve=LightSwitch.evolve,
            initial_state=LightSwitchOff(),
        )


import unittest.mock

success_light_adapter: LightSwitchAdapter = unittest.mock.MagicMock(
    spec=LightSwitchAdapter
)
success_light_adapter.turn_on.return_value = True
success_light_adapter.turn_off.return_value = True

failure_light_adapter: LightSwitchAdapter = unittest.mock.MagicMock(
    spec=LightSwitchAdapter
)
failure_light_adapter.turn_on.return_value = False
failure_light_adapter.turn_off.return_value = False


@pytest.mark.parametrize(
    "test_name, decider, initial_state, events, command, expected_events",
    [
        (
            "toggle switch when no previous events should turn on",
            LightSwitchService().light_switch_decider(success_light_adapter),
            LightSwitchOff(),
            [],
            ToggleLightSwitch(),
            [LightSwitchedOn()],
        ),
        (
            "toggle switch when on should turn off",
            LightSwitchService().light_switch_decider(success_light_adapter),
            LightSwitchOff(),
            [LightSwitchedOn()],
            ToggleLightSwitch(),
            [LightSwitchedOff()],
        ),
        (
            "toggle switch when off should turn on 2",
            LightSwitchService().light_switch_decider(success_light_adapter),
            LightSwitchOff(),
            [LightSwitchedOn(), LightSwitchedOff()],
            ToggleLightSwitch(),
            [LightSwitchedOn()],
        ),
        (
            "toggle switch when on should turn off 2",
            LightSwitchService().light_switch_decider(success_light_adapter),
            LightSwitchOff(),
            [LightSwitchedOn(), LightSwitchedOff(), LightSwitchedOn()],
            ToggleLightSwitch(),
            [LightSwitchedOff()],
        ),
        (
            "toggle switch when no previous events but fails should indicate failure",
            LightSwitchService().light_switch_decider(failure_light_adapter),
            LightSwitchOff(),
            [],
            ToggleLightSwitch(),
            [ToggleLightSwitchAttemptFailed()],
        ),
        (
            "toggle switch when on but fails should indicate failure",
            LightSwitchService().light_switch_decider(failure_light_adapter),
            LightSwitchOff(),
            [LightSwitchedOn()],
            ToggleLightSwitch(),
            [ToggleLightSwitchAttemptFailed()],
        ),
    ],
)
def test_light_switch_decider(
    test_name, decider, initial_state, events, command, expected_events
):
    state = functools.reduce(lambda s, e: decider.evolve(s, e), events, initial_state)

    assert list(decider.decide(command, state)) == expected_events
