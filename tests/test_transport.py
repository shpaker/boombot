from typing import Callable

from httpx import Response, Request
from pytest import raises, mark
from respx import MockRouter

from chatushka._errors import ChatushkaResponseError
from chatushka._models import Update, Message, User, Chat, ChatType
from chatushka._transport import (
    TelegramBotAPI,
)
from chatushka._transport import _raise_on_api_error_response_event_hook

_TESTING_TOKEN = "123:foo"


async def test_raise_on_api_error_response_event_hook_ok() -> None:
    await _raise_on_api_error_response_event_hook(
        Response(
            status_code=200,
            text='{"ok": true, "result": {}}',
            request=Request(
                method="GET",
                url="/foo",
            ),
        ),
    )


@mark.parametrize(
    "status_code,response_text",
    [
        (500, ""),
        (200, '{"ok": false}'),
        (200, '{"ok": true}'),
    ],
)
async def test_raise_on_api_error_response_event_hook_errors(
    status_code: int,
    response_text: str,
) -> None:
    with raises(ChatushkaResponseError):
        await _raise_on_api_error_response_event_hook(
            Response(
                status_code=status_code,
                text=response_text,
                request=Request(
                    method="GET",
                    url="/foo",
                ),
            ),
        )


async def test_telegram_bot_api_client_request(
    respx_mock: MockRouter,
) -> None:
    respx_mock.post().respond(
        json={
            "ok": True,
            "result": {"foo": "bar"},
        }
    )
    bot_api = TelegramBotAPI(
        token=_TESTING_TOKEN,
    )
    response = await bot_api._api_request(
        api_method="getMe",
    )
    assert response == {"foo": "bar"}, response


async def test_telegram_bot_api_transport_get_updates(
    respx_mock: MockRouter,
    testing_update_data: Update,
) -> None:
    respx_mock.post().respond(
        json={
            "ok": True,
            "result": [
                {
                    "update_id": 780080167,
                    "message": {
                        "message_id": 164380,
                        "from": {
                            "id": 777000,
                            "is_bot": False,
                            "first_name": "Telegram",
                        },
                        "sender_chat": {
                            "id": -1001033348013,
                            "title": "гиг пиг ниг",
                            "username": "geekshit",
                            "type": "channel",
                        },
                        "chat": {
                            "id": -1001357425012,
                            "title": "биг блк дик",
                            "type": "supergroup",
                        },
                        "date": 1709893596,
                        "edit_date": 1709893972,
                        "forward_origin": {
                            "type": "channel",
                            "chat": {
                                "id": -1001033348013,
                                "title": "гиг пиг ниг",
                                "username": "geekshit",
                                "type": "channel",
                            },
                            "message_id": 35146,
                            "date": 1709893593,
                        },
                        "is_automatic_forward": True,
                        "forward_from_chat": {
                            "id": -1001033348013,
                            "title": "гиг пиг ниг",
                            "username": "geekshit",
                            "type": "channel",
                        },
                        "forward_from_message_id": 35146,
                        "forward_date": 1709893593,
                        "text": "-foo-",
                        "entities": [{"offset": 22, "length": 33, "type": "url"}],
                        "link_preview_options": {"url": "https://t.me/Veyderr_history/1747"},
                    },
                },
            ],
        }
    )
    async with TelegramBotAPI(
        token=_TESTING_TOKEN,
    ) as transport:
        results = await transport.get_updates(None)
    assert results == (
        [testing_update_data],
        780080168,
    ), results


async def test_telegram_bot_api_transport_send_message(
    respx_mock: MockRouter,
) -> None:
    respx_mock.post().respond(
        json={
            "ok": True,
            "result": {
                "message_id": 512,
                "from": {
                    "id": 5594826653,
                    "is_bot": True,
                    "first_name": "mentionbot",
                    "username": "wowmentionbot",
                },
                "chat": {
                    "id": 9429534,
                    "first_name": "shpak",
                    "last_name": "er",
                    "username": "shpaker",
                    "type": "private",
                },
                "date": 1709994025,
                "text": "foo",
            },
        },
    )
    async with TelegramBotAPI(
        token=_TESTING_TOKEN,
    ) as transport:
        results = await transport.send_message(
            chat_id=9429534,
            text="foo",
        )
    assert results == Message(
        message_id=512,
        user=User(
            id=5594826653,
            is_bot=True,
            first_name="mentionbot",
            last_name=None,
            can_join_groups=None,
            can_read_all_group_messages=None,
        ),
        chat=Chat(id=9429534, type=ChatType.PRIVATE, title=None),
        text="foo",
        reply_to_message=None,
        new_chat_members=[],
    ), results
