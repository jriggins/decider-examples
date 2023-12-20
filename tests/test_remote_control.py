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
            core.EventStream(events=[remote.ToggleSwitchInitiated()]),
        ),
        (
            "given switched on toggle switch initiates",
            [remote.SwitchedOn()],
            remote.ToggleSwitch(),
            core.EventStream(events=[remote.ToggleSwitchInitiated()]),
        ),
        (
            "given switched off toggle switch initiates",
            [remote.SwitchedOff()],
            remote.ToggleSwitch(),
            core.EventStream(events=[remote.ToggleSwitchInitiated()]),
        ),
        (
            "given inital state mark switched on marks on",
            [],
            remote.MarkSwitchedOn(),
            core.EventStream(events=[remote.SwitchedOn()]),
        ),
        (
            "given switched on mark switched on marks on",
            [remote.SwitchedOn()],
            remote.MarkSwitchedOn(),
            core.EventStream(events=[remote.SwitchedOn()]),
        ),
        (
            "given switched off mark switched on marks on",
            [remote.SwitchedOff()],
            remote.MarkSwitchedOn(),
            core.EventStream(events=[remote.SwitchedOn()]),
        ),
        (
            "given inital state mark switched off marks off",
            [],
            remote.MarkSwitchedOff(),
            core.EventStream(events=[remote.SwitchedOff()]),
        ),
        (
            "given switched off mark switched off marks off",
            [remote.SwitchedOn()],
            remote.MarkSwitchedOff(),
            core.EventStream(events=[remote.SwitchedOff()]),
        ),
        (
            "given switched off mark switched off marks off",
            [remote.SwitchedOff()],
            remote.MarkSwitchedOff(),
            core.EventStream(events=[remote.SwitchedOff()]),
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


def event_saver(saved_events=[]):
    async def save_events(events: typing.Iterable[core.Event]):
        saved_events.extend(list(events))
        return saved_events

    return save_events


@pytest.mark.parametrize(
    "test_description,message,expected_response",
    [
        (
            "given any state when toggle switch then toggle switch is initiated",
            remote.ToggleSwitch(),
            core.EventStream.from_list([remote.ToggleSwitchInitiated()]),
        ),
        (
            "given any state when toggle switch then toggle switch is initiated",
            remote.SendToggleSwitch(),
            remote.SendToggleSwitch(),
        ),
        (
            "given any state when mark switch on then switch is marked on",
            remote.MarkSwitchedOn(),
            core.EventStream.from_list([remote.SwitchedOn()]),
        ),
        (
            "given any state when mark switch off then switch is marked off",
            remote.MarkSwitchedOff(),
            core.EventStream.from_list([remote.SwitchedOff()]),
        ),
    ],
)
def test_state_change(test_description, message, expected_response):
    decider = remote.Decider()
    response = decider.decide(message, None)

    assert expected_response == response


def set_toggle_switch_response(m):
    m.toggle_switch.return_value = core.EventStream(events=[remote.ToggleSwitchSent()])


@pytest.mark.parametrize(
    "test_description,input_message,expected_response,setup_mock_client,expected_client_calls,expect_saved_events",
    [
        (
            "",
            remote.ToggleSwitch(),
            core.EventStream.from_list([remote.ToggleSwitchInitiated()]),
            None,
            None,
            True,
        ),
        (
            "",
            remote.SendToggleSwitch(),
            core.EventStream.from_list([remote.ToggleSwitchSent()]),
            set_toggle_switch_response,
            lambda m: m.toggle_switch.assert_called(),
            False,
        ),
        (
            "",
            remote.MarkSwitchedOn(),
            core.EventStream.from_list([remote.SwitchedOn()]),
            None,
            None,
            False,
        ),
        (
            "",
            remote.MarkSwitchedOff(),
            core.EventStream.from_list([remote.SwitchedOff()]),
            None,
            None,
            False,
        ),
    ],
)
async def test_message_handler(
    test_description,
    input_message,
    expected_response,
    setup_mock_client,
    expected_client_calls,
    expect_saved_events,
):
    event_saver = mock.AsyncMock()
    event_saver.return_value = expected_response

    mock_switch_client = mock.AsyncMock(spec=remote.SwitchControllerClient)
    if setup_mock_client:
        setup_mock_client(mock_switch_client)

    message_handler = remote.MessageHandler(None, event_saver, mock_switch_client)

    response = await message_handler.handle(input_message)

    assert expected_response == response

    if expected_client_calls:
        expected_client_calls(mock_switch_client)

    if expect_saved_events:
        event_saver.assert_called_with(expected_response)
