import typing
from unittest import mock
import pytest
import core

import tests

import remote
import switch_controller as sc


@pytest.mark.parametrize(
    "test_name, current_events, command, expected_new_events",
    [
        (
            "given inital state toggle switch initiates",
            [],
            remote.ToggleSwitch(),
            [remote.ToggleSwitchInitiated()],
        ),
        (
            "given switched on toggle switch initiates",
            [remote.SwitchedOn()],
            remote.ToggleSwitch(),
            [remote.ToggleSwitchInitiated()],
        ),
        (
            "given switched off toggle switch initiates",
            [remote.SwitchedOff()],
            remote.ToggleSwitch(),
            [remote.ToggleSwitchInitiated()],
        ),
        (
            "given inital state mark switched on marks on",
            [],
            remote.MarkSwitchedOn(),
            [remote.SwitchedOn()],
        ),
        (
            "given switched on mark switched on marks on",
            [remote.SwitchedOn()],
            remote.MarkSwitchedOn(),
            [remote.SwitchedOn()],
        ),
        (
            "given switched off mark switched on marks on",
            [remote.SwitchedOff()],
            remote.MarkSwitchedOn(),
            [remote.SwitchedOn()],
        ),
        (
            "given inital state mark switched off marks off",
            [],
            remote.MarkSwitchedOff(),
            [remote.SwitchedOff()],
        ),
        (
            "given switched off mark switched off marks off",
            [remote.SwitchedOn()],
            remote.MarkSwitchedOff(),
            [remote.SwitchedOff()],
        ),
        (
            "given switched off mark switched off marks off",
            [remote.SwitchedOff()],
            remote.MarkSwitchedOff(),
            [remote.SwitchedOff()],
        ),
    ],
)
def test_state_changes(test_name, current_events, command, expected_new_events):
    # fmt: off
    (
        tests.StateChangeTester(remote.Decider())
            .given(current_events)
            .when(command)
            .then_expect_events(expected_new_events)
    )
    # fmt: on


@pytest.mark.parametrize(
    "test_name, initial_state, events, expected_new_state",
    [
        (
            "given initial state when switched on switch is on",
            remote.Switch(),
            [remote.SwitchedOn()],
            remote.Switch(status=remote.Switch.Status.ON),
        ),
        (
            "given initial state when switched off switch is off",
            remote.Switch(),
            [remote.SwitchedOff()],
            remote.Switch(status=remote.Switch.Status.OFF),
        ),
        (
            "given initial state when toggle initiated switch is off",
            remote.Switch(),
            [remote.ToggleSwitchInitiated()],
            remote.Switch(status=remote.Switch.Status.OFF),
        ),
        (
            "given switched on when switched on switch is on",
            remote.Switch(status=remote.Switch.Status.ON),
            [remote.SwitchedOn()],
            remote.Switch(status=remote.Switch.Status.ON),
        ),
        (
            "given switched on when switched off switch is off",
            remote.Switch(status=remote.Switch.Status.ON),
            [remote.SwitchedOff()],
            remote.Switch(status=remote.Switch.Status.OFF),
        ),
        (
            "given switched on when toggle initiated switch is on",
            remote.Switch(status=remote.Switch.Status.ON),
            [remote.ToggleSwitchInitiated()],
            remote.Switch(status=remote.Switch.Status.ON),
        ),
        (
            "given switched off when switched on switch is on",
            remote.Switch(),
            [remote.SwitchedOn()],
            remote.Switch(status=remote.Switch.Status.ON),
        ),
        (
            "given switched off when switched off switch is off",
            remote.Switch(),
            [remote.SwitchedOff()],
            remote.Switch(status=remote.Switch.Status.OFF),
        ),
        (
            "given switched off when toggle initiated switch is off",
            remote.Switch(),
            [remote.ToggleSwitchInitiated()],
            remote.Switch(status=remote.Switch.Status.OFF),
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
    "test_name, command, expected_commands",
    [
        (
            "when controller is switched on mark remote switched on",
            sc.SwitchedOn(),
            [remote.MarkSwitchedOn()],
        ),
        (
            "when controller is switched off mark remote switched off",
            sc.SwitchedOff(),
            [remote.MarkSwitchedOff()],
        ),
    ],
)
def test_external_inputs(test_name, command, expected_commands):
    # fmt: off
    (
        tests.ExternalStateInputTester(remote.Reactor())
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
            remote.ToggleSwitch(),
            [remote.ToggleSwitchInitiated()],
            None,
        ),
    ],
)
async def test_aggregate(
    test_name, current_events, command, expected_events, expected_side_effects
):
    mock_switch_client = mock.AsyncMock(spec=remote.SwitchControllerClient)

    async def get_events():
        return current_events

    saved_events = []

    aggregate = remote.Aggregate(
        get_events=get_events,
        save_events=event_saver(saved_events),
        switch_controller_client=mock_switch_client,
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
