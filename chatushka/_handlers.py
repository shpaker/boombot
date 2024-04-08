from chatushka._matchers import CommandMatcher
from chatushka._models import Chat, User
from chatushka._types import Bot


def make_ping_handler(
    command: str,
) -> CommandMatcher:
    def _ping_action() -> str:
        return "pong"

    return CommandMatcher(
        command,
        action=_ping_action,
    )


def make_id_handler(
    command: str,
) -> CommandMatcher:
    def _id_action(
        user: User,
        chat: Chat,
    ) -> str:
        text = f"*USER_ID:* `{user.id}`"
        if user.id != chat.id:
            text += f"\n*CHAT_ID:* `{chat.id}`"
        return text

    return CommandMatcher(
        command,
        action=_id_action,
    )


def get_description(
    obj: object,
) -> str:
    return obj.__doc__ or obj.__class__.__name__


def make_help_handler(
    command: str,
    bot: Bot,
) -> CommandMatcher:
    def _help_action() -> str:
        for _handler in bot.matchers:
            return ""
        return ""

    return CommandMatcher(
        command,
        action=_help_action,
    )
