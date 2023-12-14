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


class ExternalStateInputTester:
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
        return self

    def _react(self):
        return self.reactor.react(self.input_message)


class AggregateTester:
    def __init__(self, aggregate):
        self.aggregate = aggregate
        self.verify_expectations = None
        self.verify_side_effects = []

    def given(self, events):
        self.events = events
        return self

    def when(self, command):
        self.command = command
        return self

    def then_expect_events(self, expected_events):
        async def coro():
            assert await self.aggregate.handle(self.command) == expected_events

        self.verify_expectations = coro
        return self

    def and_expect_side_effect(self, verify_side_effect, *args):
        async def coro():
            verify_side_effect(*args)

        self.verify_side_effects.append(coro)
        return self

    def __await__(self):
        yield from self.verify_expectations().__await__()
        for c in self.verify_side_effects:
            yield from c().__await__()


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
        ExternalStateInputTester(sc.Reactor())
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
        AggregateTester(aggregate)
            .given(current_events)
            .when(command)
            .then_expect_events(expected_events)
            .and_expect_side_effect(expected_side_effects, mock_switch_client)
    )
    # fmt: on
