from unittest import mock
import pytest
import core
import remote


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
def test_decider(test_description, message, expected_response):
    decider = remote.Decider2()
    response = decider.decide(message, None)

    assert expected_response == response


def set_toggle_switch_response(m):
    m.toggle_switch.return_value = core.EventStream(events=[remote.ToggleSwitchSent()])


@pytest.mark.parametrize(
    "test_description,input_message,expected_response,setup_mock_client,expected_client_calls",
    [
        (
            "",
            remote.ToggleSwitch(),
            core.EventStream.from_list([remote.ToggleSwitchInitiated()]),
            None,
            None,
        ),
        (
            "",
            remote.SendToggleSwitch(),
            core.EventStream.from_list([remote.ToggleSwitchSent()]),
            set_toggle_switch_response,
            lambda m: m.toggle_switch.assert_called(),
        ),
        (
            "",
            remote.MarkSwitchedOn(),
            core.EventStream.from_list([remote.SwitchedOn()]),
            None,
            None,
        ),
        (
            "",
            remote.MarkSwitchedOff(),
            core.EventStream.from_list([remote.SwitchedOff()]),
            None,
            None,
        ),
    ],
)
async def test_message_handler(
    test_description,
    input_message,
    expected_response,
    setup_mock_client,
    expected_client_calls,
):
    mock_switch_client = mock.AsyncMock(spec=remote.SwitchControllerClient)
    if setup_mock_client:
        setup_mock_client(mock_switch_client)

    message_handler = remote.MessageHandler(None, mock_switch_client)

    response = await message_handler.handle(input_message)

    assert expected_response == response

    if expected_client_calls:
        expected_client_calls(mock_switch_client)
