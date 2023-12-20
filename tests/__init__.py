import functools

import core


class StateViewTester:
    def given(self, initial_state: core.State):
        self.state = initial_state
        return self

    def when(self, events):
        self.events = events
        return self

    def then_expect_state(self, expected_state):
        computed_state = self._compute_current_state()
        assert computed_state == expected_state, f"{computed_state} != {expected_state}"

    def _compute_current_state(self):
        current_state = functools.reduce(
            lambda s, e: self.state.evolve(s, e), self.events, self.state
        )

        return current_state


class StateChangeTester:
    def __init__(self, decider: core.Decider):
        self.decider = decider

    def given(self, events):
        self.events = events
        return self

    def when(self, command):
        self.command = command
        return self

    def then_expect_events(self, expected_events):
        computed_events = self.decider.decide(
            self.command, self._compute_current_state()
        )
        assert (
            computed_events == expected_events
        ), f"{computed_events} != {expected_events}"

    def _compute_current_state(self):
        current_state = functools.reduce(
            lambda s, e: self.decider.evolve(s, e),
            self.events,
            self.decider.initial_state,
        )

        return current_state


# class ExternalStateInputTester:
#     def __init__(self, reactor: core.Reactor):
#         self.reactor = reactor

#     def given(self, events):
#         self.events = events
#         return self

#     def when(self, input_message):
#         self.input_message = input_message
#         return self

#     def then_expect_commands(self, expected_commands):
#         assert self._react() == expected_commands
#         return self

#     def _react(self):
#         return self.reactor.react(self.input_message)


class MessageHandlerTester:
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
            new_events = await self.aggregate.handle(self.command)
            assert new_events == expected_events, f"{new_events} != {expected_events}"

        self.verify_expectations = coro
        return self

    def and_expect_side_effect(self, verify_side_effect, *args):
        async def coro():
            verify_side_effect(*args)

        if verify_side_effect is not None:
            self.verify_side_effects.append(coro)
        return self

    def __await__(self):
        yield from self.verify_expectations().__await__()
        for c in self.verify_side_effects:
            yield from c().__await__()
