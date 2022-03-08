from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChatType(str, Enum):
    GROUP = "group"
    SUPERGROUP = "supergroup"
    PRIVATE = "private"


class ChatMemberStatuses(str, Enum):
    CREATOR = "creator"
    ADMINISTRATOR = "administrator"


class User(BaseModel):
    id: int
    is_bot: bool
    first_name: Optional[str]
    last_name: Optional[str]
    can_join_groups: Optional[bool]
    can_read_all_group_messages: Optional[bool]

    @property
    def readable_name(self) -> str:
        return f"{self.first_name}{' '+self.last_name if self.last_name else ''}"


class ChatMemberBase(BaseModel):
    status: ChatMemberStatuses
    user: User
    is_anonymous: bool
    custom_title: Optional[str]


class ChatMemberOwner(ChatMemberBase):
    ...


class ChatMemberAdministrator(ChatMemberBase):
    can_be_edited: bool
    can_manage_chat: bool
    can_delete_messages: bool
    can_manage_voice_chats: bool
    can_restrict_members: bool
    can_promote_members: bool
    can_change_info: bool
    can_invite_users: bool
    can_post_messages: Optional[bool]
    can_edit_messages: Optional[bool]
    can_pin_messages: Optional[bool]


class Chat(BaseModel):
    id: int
    type: ChatType
    title: Optional[str]


class Message(BaseModel):
    message_id: int
    user: User = Field(..., alias="from")
    chat: Chat
    text: str
    reply_to_message: Optional["Message"] = None


Message.update_forward_refs()


class Update(BaseModel):
    update_id: int
    message: Message


class ChatPermissions(BaseModel):
    can_send_messages: bool
    can_send_media_messages: bool
    can_send_polls: bool
    can_send_other_messages: bool
    # can_add_web_page_previews: bool
    # can_change_info: bool
    # can_invite_users: bool
    # can_pin_messages: bool
