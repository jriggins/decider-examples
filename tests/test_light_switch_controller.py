import functools

import switch_controller as sc


####


def test_given_initial_state_toggle_light_switch_switches_on():
    events = []
    command = sc.ToggleLightSwitch()
    decider = sc.LightSwitchControllerDecider()

    expected_events = [sc.LightSwitchedOn()]

    current_state = functools.reduce(
        lambda s, e: decider.evolve(s, e),
        events,
        decider.initial_state,
    )

    result = decider.decide(command, current_state)

    assert result == expected_events


def test_given_light_switch_on_toggle_light_switch_switches_off():
    events = [sc.LightSwitchedOn()]
    command = sc.ToggleLightSwitch()
    decider = sc.LightSwitchControllerDecider()

    expected_events = [sc.LightSwitchedOff()]

    current_state = functools.reduce(
        lambda s, e: decider.evolve(s, e),
        events,
        decider.initial_state,
    )

    result = decider.decide(command, current_state)

    assert result == expected_events


def test_given_light_switch_off_toggle_light_switch_switches_on():
    events = [sc.LightSwitchedOff()]
    command = sc.ToggleLightSwitch()
    decider = sc.LightSwitchControllerDecider()

    expected_events = [sc.LightSwitchedOn()]

    current_state = functools.reduce(
        lambda s, e: decider.evolve(s, e),
        events,
        decider.initial_state,
    )

    result = decider.decide(command, current_state)

    assert result == expected_events
