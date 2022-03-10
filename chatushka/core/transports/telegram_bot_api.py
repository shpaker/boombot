from datetime import datetime
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple, Union

from httpx import AsyncClient, Response
from pydantic import ValidationError

from chatushka.core.transports import models
from chatushka.core.transports.models import (
    ChatMemberAdministrator,
    ChatMemberOwner,
    ChatMemberStatuses,
    ChatPermissions,
)

logger = getLogger()


class TelegramBotApi:
    def __init__(
        self,
        token: str,
    ) -> None:
        self.token = token

    @property
    def _base_api_url(self) -> str:
        return f"https://api.telegram.org/bot{self.token}"

    def _api_method_url(
        self,
        method: str,
    ) -> str:
        return f"{self._base_api_url}/{method}"

    @staticmethod
    def check_api_response(
        response: Response,
    ) -> Dict[str, Any]:
        data: dict[str, Any] = response.json()
        is_ok: bool = data.get("ok", False)
        if not is_ok:
            logger.warning(response.text)
            raise ValueError(f"Telegram response error: {response.text}\n{data}")

        result: Dict[str, Any] = data["result"]
        return result

    async def _call_api(
        self,
        method: str,
        timeout: int = 10,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        url = self._api_method_url(method)
        async with AsyncClient() as client:  # type: AsyncClient
            response = await client.post(url, timeout=timeout * 2, data=kwargs)
        return self.check_api_response(response)

    async def get_me(
        self,
    ) -> models.User:
        result = await self._call_api("getme")
        return models.User(**result)  # type: ignore

    async def get_updates(
        self,
        timeout: int,
        offset: Optional[int] = None,
    ) -> Tuple[List[models.Update], int]:
        params = {}
        if offset:
            params["offset"] = offset
        results = await self._call_api(
            "getupdates",
            timeout=timeout,
            **params,
        )
        updates_list = []
        latest_update_id: Optional[int] = offset
        for result in results:
            if not latest_update_id or (latest_update_id < result["update_id"]):  # type: ignore
                latest_update_id = result["update_id"]  # type: ignore
            try:
                update = models.Update(**result)  # type: ignore
            except ValidationError as err:
                logger.debug(err)
                continue
            updates_list.append(update)
        return updates_list, latest_update_id  # type: ignore

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: Optional[int] = None,
        parse_mode: str = "html",
        disable_web_page_preview: bool = False,
    ) -> models.Message:
        result = await self._call_api(
            "sendmessage",
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
        )
        return models.Message(**result)  # type: ignore

    async def restrict_chat_member(
        self,
        chat_id: int,
        user_id: int,
        permissions: ChatPermissions,
        until_date: datetime,
    ) -> bool:
        result = await self._call_api(
            "restrictChatMember",
            chat_id=chat_id,
            user_id=user_id,
            permissions=permissions.json(),
            until_date=int(until_date.timestamp()),
        )
        return result  # noqa, type: ignore

    async def get_chat_administrators(
        self,
        chat_id: int,
    ) -> List[Union[ChatMemberAdministrator, ChatMemberOwner]]:
        results = await self._call_api(
            "getChatAdministrators",
            chat_id=chat_id,
        )
        admins = []
        for result in results:
            status = result["status"]
            if status == ChatMemberStatuses.CREATOR:
                admins.append(ChatMemberOwner(**result))
            if status == ChatMemberStatuses.ADMINISTRATOR:
                admins.append(ChatMemberAdministrator(**result))
        return admins

    async def pin_chat_message(
        self,
        chat_id: int,
        message_id: int,
        disable_notification: bool = True,
    ) -> bool:
        result = await self._call_api(
            "pinChatMessage",
            chat_id=chat_id,
            message_id=message_id,
            disable_notification=disable_notification,
        )
        return result  # noqa, type: ignore

    async def unpin_chat_message(
        self,
        chat_id: int,
        message_id: int,
    ) -> bool:
        result = await self._call_api(
            "unpinChatMessage",
            chat_id=chat_id,
            message_id=message_id,
        )
        return result  # noqa, type: ignore

    async def unpin_all_chat_messages(
        self,
        chat_id: int,
    ) -> bool:
        result = await self._call_api(
            "unpinAllChatMessages",
            chat_id=chat_id,
        )
        return result  # noqa, type: ignore
