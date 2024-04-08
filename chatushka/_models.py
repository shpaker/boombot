from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ChatType(
    str,
    Enum,
):
    GROUP = "group"
    SUPERGROUP = "supergroup"
    PRIVATE = "private"


class ChatMemberStatuses(
    str,
    Enum,
):
    MEMBER = "member"
    CREATOR = "creator"
    ADMINISTRATOR = "administrator"
    LEFT = "left"
    KICKED = "kicked"
    RESTRICTED = "restricted"


class User(
    BaseModel,
):
    id: int
    is_bot: bool
    first_name: str | None = None
    last_name: str | None = None
    can_join_groups: bool | None = None
    can_read_all_group_messages: bool | None = None

    @property
    def readable_name(self) -> str:
        return f"{self.first_name}{' '+self.last_name if self.last_name else ''}"


class ChatMemberBase(
    BaseModel,
):
    status: ChatMemberStatuses
    user: User
    is_anonymous: bool | None = None
    custom_title: str | None = None


class ChatMemberOwner(
    ChatMemberBase,
): ...


class ChatMemberAdministrator(
    ChatMemberBase,
):
    can_be_edited: bool | None = None
    can_manage_chat: bool | None = None
    can_delete_messages: bool | None = None
    can_manage_voice_chats: bool | None = None
    can_restrict_members: bool | None = None
    can_promote_members: bool | None = None
    can_change_info: bool | None = None
    can_invite_users: bool | None = None
    can_post_messages: bool | None = None
    can_edit_messages: bool | None = None
    can_pin_messages: bool | None = None


class Chat(
    BaseModel,
):
    id: int
    type: ChatType
    title: str | None = None


class NewChatMember(
    ChatMemberAdministrator,
): ...


class OldChatMember(
    ChatMemberAdministrator,
): ...


class Message(
    BaseModel,
):
    message_id: int
    user: User = Field(
        validation_alias=AliasChoices("user", "from"),
    )
    chat: Chat
    text: str | None = None
    reply_to_message: Optional["Message"] = None
    new_chat_members: list[User] = Field(default_factory=list)


Message.update_forward_refs()


class MyChatMember(
    BaseModel,
):
    chat: Chat
    user: User = Field(..., alias="from")
    date: datetime
    old_chat_member: OldChatMember
    new_chat_member: NewChatMember


class Update(
    BaseModel,
):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    update_id: int
    message: Message | None = None
    my_chat_member: MyChatMember | None = None


class ChatPermissions(
    BaseModel,
):
    can_send_messages: bool
    can_send_media_messages: bool
    can_send_polls: bool
    can_send_other_messages: bool


Events = Literal[
    "on_message",
    "on_new_chat_members",
    "on_left_chat_member",
]
