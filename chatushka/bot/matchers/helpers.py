from chatushka.bot.settings import get_settings
from chatushka.core.matchers import CommandsMatcher
from chatushka.core.transports.models import Message
from chatushka.core.transports.telegram_bot_api import TelegramBotApi

settings = get_settings()
helpers_matcher = CommandsMatcher(
    prefixes=settings.command_prefixes,
    postfixes=settings.command_postfixes,
)


@helpers_matcher("id")
async def id_handler(
    api: TelegramBotApi,
    message: Message,
) -> None:
    admins = await api.get_chat_administrators(message.chat.id)
    line_tmpl = "{id_type}: <pre>{id_value}</pre>"
    ids = dict(user_id=message.user.id)
    for admin in admins:
        if admin.user.id == message.user.id:
            ids = ids | dict(chat_id=message.chat.id)
    text = "\n".join(list(line_tmpl.format(id_type=id_type, id_value=id_value) for id_type, id_value in ids.items()))
    await api.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_to_message_id=message.message_id,
    )


@helpers_matcher("ping", "пинг")
async def ping_handler(
    api: TelegramBotApi,
    message: Message,
) -> None:
    answer = "pong" if "ping" in message.text else "понг"
    await api.send_message(
        chat_id=message.chat.id,
        text=answer,
        reply_to_message_id=message.message_id,
    )
