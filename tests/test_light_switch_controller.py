import typing
from unittest import mock

import pytest

import tests
import core
import switch_controller as sc


@pytest.mark.parametrize(
    "test_name, initial_state, events, expected_new_state",
    [
        (
            "given initial state when switched on switch is on",
            sc.LightSwitch(),
            [sc.SwitchedOn()],
            sc.LightSwitch(status=sc.LightSwitch.Status.ON),
        ),
        (
            "given switch off when switched off switch is off",
            sc.LightSwitch(status=sc.LightSwitch.Status.OFF),
            [sc.SwitchedOff()],
            sc.LightSwitch(status=sc.LightSwitch.Status.OFF),
        ),
        (
            "given switch off when turn off initiated switch is off",
            sc.LightSwitch(status=sc.LightSwitch.Status.OFF),
            [sc.TurnOffInitiated()],
            sc.LightSwitch(status=sc.LightSwitch.Status.OFF),
        ),
        (
            "given switch off when turn on initiated switch is off",
            sc.LightSwitch(status=sc.LightSwitch.Status.OFF),
            [sc.TurnOnInitiated()],
            sc.LightSwitch(status=sc.LightSwitch.Status.OFF),
        ),
        (
            "given switch on when switched on switch is on",
            sc.LightSwitch(status=sc.LightSwitch.Status.ON),
            [sc.SwitchedOn()],
            sc.LightSwitch(status=sc.LightSwitch.Status.ON),
        ),
        (
            "given switch on when switched off switch is off",
            sc.LightSwitch(status=sc.LightSwitch.Status.ON),
            [sc.SwitchedOff()],
            sc.LightSwitch(status=sc.LightSwitch.Status.OFF),
        ),
        (
            "given switch on when turn off initiated switch is on",
            sc.LightSwitch(status=sc.LightSwitch.Status.ON),
            [sc.TurnOnInitiated()],
            sc.LightSwitch(status=sc.LightSwitch.Status.ON),
        ),
        (
            "given switch on when turn on initiated switch is on",
            sc.LightSwitch(status=sc.LightSwitch.Status.ON),
            [sc.TurnOffInitiated()],
            sc.LightSwitch(status=sc.LightSwitch.Status.ON),
        ),
    ],
)
def test_state_view(test_name, initial_state, events, expected_new_state):
    # fmt: off
    (
        tests.StateViewTester()
            .given(initial_state)
            .when(events)
            .then_expect_state(expected_new_state)
    )
    # fmt: on


@pytest.mark.parametrize(
    "test_name, current_events, command, expected_new_events",
    [
        (
            "given initial state turn on initiates turning on",
            [],
            sc.TurnOn(),
            [sc.TurnOnInitiated()],
        ),
        (
            "given initial state turn off does nothing",
            [],
            sc.TurnOff(),
            [],
        ),
        (
            "given initial state toggle light switch initiates turning on",
            [],
            sc.ToggleLightSwitch(),
            [sc.TurnOnInitiated()],
        ),
        (
            "given switch off turn on initiates turning on",
            [sc.SwitchedOff()],
            sc.TurnOn(),
            [sc.TurnOnInitiated()],
        ),
        (
            "given switch off turn off does nothing",
            [sc.SwitchedOff()],
            sc.TurnOff(),
            [],
        ),
        (
            "given switch off toggle switch initiates turning on",
            [sc.SwitchedOff()],
            sc.ToggleLightSwitch(),
            [sc.TurnOnInitiated()],
        ),
        (
            "given switch on turn off initiates turning off",
            [sc.SwitchedOn()],
            sc.TurnOff(),
            [sc.TurnOffInitiated()],
        ),
        (
            "given switch on turn off initiates turning off",
            [sc.SwitchedOn()],
            sc.TurnOff(),
            [sc.TurnOffInitiated()],
        ),
        (
            "given switch on toggle switch initiates turning off",
            [sc.SwitchedOn()],
            sc.ToggleLightSwitch(),
            [sc.TurnOffInitiated()],
        ),
    ],
)
def test_state_changes(test_name, current_events, command, expected_new_events):
    # fmt: off
    (
        tests.StateChangeTester(sc.Decider())
            .given(current_events)
            .when(command)
            .then_expect_events(expected_new_events)
    )
    # fmt: on


@pytest.mark.parametrize(
    "test_name, command, expected_commands",
    [
        ("when turn on initiated turn on", sc.TurnOnInitiated(), [sc.TurnOn()]),
        ("when turn off initiated turn off", sc.TurnOffInitiated(), [sc.TurnOff()]),
    ],
)
def test_external_inputs(test_name, command, expected_commands):
    # fmt: off
    (
        tests.ExternalStateInputTester(sc.Reactor())
            .when(command)
            .then_expect_commands(expected_commands)
    )
    # fmt: on


def event_saver(saved_events=[]):
    async def save_events(events: typing.Iterable[core.Event]):
        saved_events.extend(list(events))
        return saved_events

    return save_events


@pytest.mark.parametrize(
    "test_name, current_events, command, expected_events, expected_side_effects",
    [
        (
            "given initial state turn on turns on",
            [],
            sc.TurnOn(),
            [sc.SwitchedOn()],
            lambda m: m.turn_on.assert_called(),
        ),
        (
            "given initial state turn off turns off",
            [],
            sc.TurnOff(),
            [sc.SwitchedOff()],
            lambda m: m.turn_off.assert_called(),
        ),
        (
            "given turned on turn off turns off",
            [sc.SwitchedOn()],
            sc.TurnOff(),
            [sc.SwitchedOff()],
            lambda m: m.turn_off.assert_called(),
        ),
        (
            "given turned off turn on turns on",
            [sc.SwitchedOff()],
            sc.TurnOn(),
            [sc.SwitchedOn()],
            lambda m: m.turn_on.assert_called(),
        ),
        # (
        #     "given turned on turn on makes no change",
        #     [sc.SwitchedOn()],
        #     sc.TurnOn(),
        #     [sc.SwitchedOn()],
        #     lambda m: m.turn_on.assert_called(),
        # ),
        (
            "given turned off turn off turns off",
            [sc.SwitchedOff()],
            sc.TurnOff(),
            [sc.SwitchedOff()],
            lambda m: m.turn_off.assert_called(),
        ),
        (
            "given initial state toggle turns on",
            [],
            sc.ToggleLightSwitch(),
            [sc.TurnOnInitiated(), sc.SwitchedOn()],
            lambda m: m.turn_on.assert_called(),
        ),
        (
            "given turned on toggle turns off",
            [sc.SwitchedOn()],
            sc.ToggleLightSwitch(),
            [sc.TurnOffInitiated(), sc.SwitchedOff()],
            lambda m: m.turn_off.assert_called(),
        ),
        (
            "given turned off toggle turns on",
            [sc.SwitchedOff()],
            sc.ToggleLightSwitch(),
            [sc.TurnOnInitiated(), sc.SwitchedOn()],
            lambda m: m.turn_on.assert_called(),
        ),
    ],
)
async def test_aggregate(
    test_name, current_events, command, expected_events, expected_side_effects
):
    mock_switch_client = mock.AsyncMock(spec=sc.SwitchClient)

    async def get_events():
        return current_events

    saved_events = []

    aggregate = sc.Aggregate(
        get_events=get_events,
        save_events=event_saver(saved_events),
        switch_client=mock_switch_client,
    )

    # fmt: off
    await (
        tests.AggregateTester(aggregate)
            .given(current_events)
            .when(command)
            .then_expect_events(expected_events)
            .and_expect_side_effect(expected_side_effects, mock_switch_client)
    )
    # fmt: on


######

import uuid
import pydantic
import dataclasses


@dataclasses.dataclass
class UserFromExternal:
    id: str
    name: str


class User(pydantic.BaseModel):
    id: uuid.UUID
    name: str


def test_converts_str_to_uuid():
    user_external = UserFromExternal(
        id="A4C6BC9E-92A7-4FFE-963B-BCC0707EC926", name="Test User"
    )

    user_internal = User(**user_external.__dict__)

    assert type(user_internal.id) == uuid.UUID
