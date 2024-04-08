from datetime import datetime
from types import TracebackType
from typing import Any, Literal

from httpx import AsyncClient, Response, TimeoutException

from chatushka._constants import HTTP_REGULAR_TIMEOUT
from chatushka._errors import ChatushkaResponseError
from chatushka._logger import logger
from chatushka._models import (
    ChatMemberAdministrator,
    ChatMemberOwner,
    ChatMemberStatuses,
    ChatPermissions,
    Message,
    Update,
)
from chatushka._sentry import report_exc


async def _raise_on_api_error_response_event_hook(
    response: Response,
) -> None:
    await response.aread()
    if not response.is_success:
        raise ChatushkaResponseError(
            response=response,
        )
    data: dict[str, Any] = response.json()
    if data.get("ok", False) is False or data.get("result") is None:
        raise ChatushkaResponseError(
            response=response,
        )


class TelegramBotAPI:
    _offsets: dict[str, int] = {}  # noqa

    def __init__(
        self,
        token: str,
        timeout: int = HTTP_REGULAR_TIMEOUT,
    ) -> None:
        self._token = token
        self._client = AsyncClient(
            base_url=f"https://api.telegram.org/bot{token}",
            event_hooks={  # type: ignore
                "response": [
                    _raise_on_api_error_response_event_hook,
                ]
            },
            timeout=timeout,
        )
        self._timeout = timeout

    def __repr__(
        self,
    ) -> str:
        return f"<{self.__class__.__name__}>"

    async def _api_request(
        self,
        api_method: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        logger.debug(f"{self} >>> {api_method} >>> {kwargs}")
        response = await self._client.post(
            url=api_method,
            json=kwargs,
        )
        data = response.json()["result"]
        logger.debug(f"{self} <<< {api_method} <<< {response.text}")
        return data

    async def __aenter__(
        self,
    ) -> "TelegramBotAPI":
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        return await self._client.__aexit__(
            exc_type=exc_type,
            exc_value=exc_value,
            traceback=traceback,
        )

    async def get_updates(
        self,
        offset: int | None,
    ) -> tuple[list[Update], int | None]:
        params = {} if not offset else {"offset": offset}
        if self._timeout:
            params["timeout"] = self._timeout
        try:
            response = await self._api_request(
                api_method="getUpdates",
                **params,
            )
        except TimeoutException:
            return [], offset
        except Exception as exc:
            report_exc(exc)
            logger.error(f"{self} !!! {exc.__class__.__name__} ({exc!s})")
            return [], offset
        results = [Update.model_validate(entry) for entry in response]
        if results:
            offset = results[-1].update_id + 1
        return results, offset

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
        parse_mode: Literal["html", "markdown"] = "markdown",
        disable_web_page_preview: bool = False,
    ) -> Message:
        result = await self._api_request(
            api_method="sendMessage",
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
        )
        return Message.model_validate(result)

    async def get_chat_administrators(
        self,
        chat_id: int,
    ) -> list[ChatMemberAdministrator | ChatMemberOwner]:
        results = await self._api_request(
            "getChatAdministrators",
            chat_id=chat_id,
        )
        admins: list[ChatMemberAdministrator | ChatMemberOwner] = []
        for result in results:
            status = result["status"]  # type: ignore
            if status == ChatMemberStatuses.CREATOR:
                admins.append(ChatMemberOwner.model_validate(result))
            if status == ChatMemberStatuses.ADMINISTRATOR:
                admins.append(ChatMemberAdministrator.model_validate(result))
        return admins

    async def restrict_chat_member(
        self,
        chat_id: int,
        user_id: int,
        permissions: ChatPermissions,
        until_date: datetime,
    ) -> bool:
        return await self._api_request(  # type: ignore
            "restrictChatMember",
            chat_id=chat_id,
            user_id=user_id,
            permissions=permissions.json(),
            until_date=int(until_date.timestamp()),
        )
