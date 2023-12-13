import functools
from unittest import mock

import pytest

import switch_controller as sc


####


def test_given_initial_state_toggle_light_switch_switches_on():
    events = []
    command = sc.ToggleLightSwitch()
    decider = sc.LightSwitchControllerDecider()

    expected_events = [sc.TurnOnInitiated()]

    current_state = functools.reduce(
        lambda s, e: decider.evolve(s, e),
        events,
        decider.initial_state,
    )

    result = decider.decide(command, current_state)

    assert result == expected_events


def test_given_light_switch_on_toggle_light_switch_switches_off():
    events = [sc.SwitchedOn()]
    command = sc.ToggleLightSwitch()
    decider = sc.LightSwitchControllerDecider()

    expected_events = [sc.TurnOffInitiated()]

    current_state = functools.reduce(
        lambda s, e: decider.evolve(s, e),
        events,
        decider.initial_state,
    )

    result = decider.decide(command, current_state)

    assert result == expected_events


def test_given_light_switch_off_toggle_light_switch_switches_on():
    events = [sc.SwitchedOff()]
    command = sc.ToggleLightSwitch()
    decider = sc.LightSwitchControllerDecider()

    expected_events = [sc.TurnOnInitiated()]

    current_state = functools.reduce(
        lambda s, e: decider.evolve(s, e),
        events,
        decider.initial_state,
    )

    result = decider.decide(command, current_state)

    assert result == expected_events


def test_switch_toggled_event_turns_switch_on():
    input_message = sc.TurnOnInitiated()
    saga = sc.Reactor()

    expected_output_messages = [sc.TurnOn()]

    result = saga.react(input_message)

    assert result == expected_output_messages


def test_switch_toggled_event_turns_switch_off():
    input_message = sc.TurnOffInitiated()
    saga = sc.Reactor()

    expected_output_messages = [sc.TurnOff()]

    result = saga.react(input_message)

    assert result == expected_output_messages


async def test_service_given_turn_on_initiated_turns_on_switch():
    mock_switch_client = mock.AsyncMock(spec=sc.SwitchClient)

    async def get_events():
        return []

    expected_events = [sc.SwitchedOn()]

    service = sc.Aggregate(get_events=get_events, switch_client=mock_switch_client)
    output_stream = await service.handle(message=sc.TurnOn())

    mock_switch_client.turn_on.assert_called()

    assert output_stream == expected_events


async def test_service_given_turn_off_initiated_turns_off_switch():
    mock_switch_client = mock.AsyncMock(spec=sc.SwitchClient)

    async def get_events():
        return []

    expected_events = [sc.SwitchedOff()]

    service = sc.Aggregate(get_events=get_events, switch_client=mock_switch_client)
    output_stream = await service.handle(message=sc.TurnOff())

    mock_switch_client.turn_off.assert_called()

    assert output_stream == expected_events


async def test_service_given_initial_state_toggle_switch_turns_on():
    async def get_events():
        return []

    mock_switch_client = mock.AsyncMock(spec=sc.SwitchClient)
    expected_events = [sc.TurnOnInitiated(), sc.SwitchedOn()]

    service = sc.Aggregate(get_events=get_events, switch_client=mock_switch_client)
    output_stream = await service.handle(message=sc.ToggleLightSwitch())

    mock_switch_client.turn_on.assert_called()

    assert output_stream == expected_events


# async def test_service_given_turned_on_state_toggle_switch_turns_off():
#     async def get_events():
#         return [sc.SwitchedOn()]

#     mock_switch_client = mock.AsyncMock(spec=sc.SwitchClient)
#     expected_events = [sc.TurnOnInitiated()]

#     service = sc.Aggregate(get_events=get_events, switch_client=mock_switch_client)
#     output_stream = await service.handle(message=sc.ToggleLightSwitch())

#     mock_switch_client.turn_on.assert_not_called()

#     assert output_stream == expected_events
