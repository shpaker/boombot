from typing import Callable

from pytest import fixture

from chatushka import Update, Message, User, Chat
from chatushka._models import ChatType


@fixture(name="make_update_data")
def _make_update_data() -> Callable[[str], Update]:
    def _func(
        text: str = "-foo-",
    ) -> Update:
        return Update(
            update_id=780080167,
            message=Message(
                message_id=164380,
                user=User(
                    id=777000,
                    is_bot=False,
                    first_name="Telegram",
                    last_name=None,
                    can_join_groups=None,
                    can_read_all_group_messages=None,
                ),
                chat=Chat(
                    id=-1001357425012,
                    type=ChatType.SUPERGROUP,
                    title="биг блк дик",
                ),
                text=text,
                reply_to_message=None,
                new_chat_members=[],
            ),
            my_chat_member=None,
        )

    return _func


@fixture
def testing_update_data(
    make_update_data: Callable[[], Update],
) -> Update:
    return make_update_data()
