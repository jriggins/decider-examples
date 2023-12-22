from typing import Any, Awaitable, Coroutine
import typing
import core


class Decider(core.Decider):
    def __init__(self):
        super().__init__(None)

    def decide(self, message: Any, state: Any) -> Any:
        ...


class MessageHandler(core.MessageHandler):
    def __init__(
        self,
        get_events: typing.Callable[[], Awaitable[list]],
        save_events: typing.Callable[[list], Awaitable[list]],
    ):
        super().__init__(Decider(), get_events, save_events)

    async def handle(self, message: Any) -> Any:
        return []


def test_message_handler():
    message_handler = MessageHandler(None, None)
    assert message_handler
