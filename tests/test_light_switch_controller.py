import functools
import typing
from unittest import mock

import pytest
import core

import switch_controller as sc


class StateChangeTester:
    def __init__(self, decider):
        self.decider = decider

    def given(self, events):
        self.events = events
        return self

    def when(self, command):
        self.command = command
        return self

    def then_expect_events(self, expected_events):
        assert (
            self.decider.decide(self.command, self._compute_current_state())
            == expected_events
        )

    def _compute_current_state(self):
        current_state = functools.reduce(
            lambda s, e: self.decider.evolve(s, e),
            self.events,
            self.decider.initial_state,
        )

        return current_state


class ExternalInputTester:
    def __init__(self, reactor):
        self.reactor = reactor

    def given(self, events):
        self.events = events
        return self

    def when(self, input_message):
        self.input_message = input_message
        return self

    def then_expect_commands(self, expected_commands):
        assert self._react() == expected_commands

    def _react(self):
        return self.reactor.react(self.input_message)


@pytest.mark.parametrize(
    "test_name, current_events, command, expected_new_events",
    [
        (
            "given initial state toggle light switch initiates turning on",
            [],
            sc.ToggleLightSwitch(),
            [sc.TurnOnInitiated()],
        ),
        (
            "given switch on toggle switch initiates turning off",
            [sc.SwitchedOn()],
            sc.ToggleLightSwitch(),
            [sc.TurnOffInitiated()],
        ),
        (
            "given switch off toggle switch initiates turning on",
            [sc.SwitchedOff()],
            sc.ToggleLightSwitch(),
            [sc.TurnOnInitiated()],
        ),
    ],
)
def test_state_changes(test_name, current_events, command, expected_new_events):
    # fmt: off
    (
        StateChangeTester(sc.Decider())
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
        ExternalInputTester(sc.Reactor())
            .when(command)
            .then_expect_commands(expected_commands)
    )
    # fmt: on


def event_saver(saved_events=[]):
    async def save_events(events: typing.Iterable[core.Event]):
        saved_events.extend(list(events))
        return saved_events

    return save_events


async def test_service_given_turn_on_initiated_turns_on_switch():
    mock_switch_client = mock.AsyncMock(spec=sc.SwitchClient)

    async def get_events():
        return []

    expected_events = [sc.SwitchedOn()]

    service = sc.Aggregate(
        get_events=get_events, save_events=event_saver, switch_client=mock_switch_client
    )
    output_stream = await service.handle(command=sc.TurnOn())

    mock_switch_client.turn_on.assert_called()

    assert output_stream == expected_events


async def test_service_given_turn_off_initiated_turns_off_switch():
    mock_switch_client = mock.AsyncMock(spec=sc.SwitchClient)

    async def get_events():
        return []

    expected_events = [sc.SwitchedOff()]

    service = sc.Aggregate(
        get_events=get_events, save_events=event_saver, switch_client=mock_switch_client
    )
    output_stream = await service.handle(command=sc.TurnOff())

    mock_switch_client.turn_off.assert_called()

    assert output_stream == expected_events


async def test_service_given_initial_state_toggle_switch_turns_on():
    async def get_events():
        return []

    mock_switch_client = mock.AsyncMock(spec=sc.SwitchClient)
    expected_events = [sc.TurnOnInitiated(), sc.SwitchedOn()]

    saved_events = []

    service = sc.Aggregate(
        get_events=get_events,
        save_events=event_saver(saved_events=saved_events),
        switch_client=mock_switch_client,
    )
    output_stream = await service.handle(command=sc.ToggleLightSwitch())

    mock_switch_client.turn_on.assert_called()

    assert output_stream == expected_events
    assert output_stream == saved_events
