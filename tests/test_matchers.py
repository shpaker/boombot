from typing import Callable

from pytest import mark, param, raises

from chatushka._matchers import CommandMatcher, RegExMatcher
from chatushka._models import Update
from chatushka._transport import TelegramBotAPI


async def test_matcher_call_async_action() -> None:
    async def _func() -> None:
        raise RuntimeError

    matcher = CommandMatcher(action=_func)

    with raises(
        RuntimeError,
    ):
        await matcher._call_action(
            api=TelegramBotAPI(token="token"),
            update=Update(
                update_id="911",
            ),
            results=(),
        )


async def test_matcher_call_sync_action() -> None:
    def _func() -> None:
        raise RuntimeError

    matcher = CommandMatcher(action=_func)

    with raises(
        RuntimeError,
    ):
        await matcher._call_action(
            api=TelegramBotAPI(token="token"),
            update=Update(
                update_id="911",
            ),
            results=(),
        )


@mark.parametrize(
    "command, prefixes, case_sensitive, text",
    [
        param("test", "", False, "test bar", id="ok"),
        param("test", "", True, "tESt bar", id="not case_sensitive"),
        param("test", "!", True, "!test bar", id="with prefix"),
        param("test", ["!", "?"], True, "?test bar", id="several prefixes"),
    ],
)
async def test_command_matcher_success(
    command: str,
    prefixes: str | list[str],
    case_sensitive: bool,
    text: str,
    make_update_data: Callable[[str], Update],
) -> None:
    def _func() -> None:
        raise RuntimeError

    matcher = CommandMatcher(
        command,
        action=_func,
        case_sensitive=case_sensitive,
        prefixes=prefixes,
    )
    update = make_update_data(text)
    assert matcher._check(update=update) == [
        "bar",
    ]
    with raises(RuntimeError):
        await matcher._call_action(
            api=TelegramBotAPI(token="123:abc"),
            update=update,
            results=(),
        )


@mark.parametrize(
    "command, prefixes, case_sensitive, text",
    [
        ("test", "", False, "foo bar"),
        ("test", "", False, "foo TEST bar"),
        ("test", "!", True, "foo test bar"),
    ],
)
async def test_command_matcher_fail(
    command,
    prefixes,
    case_sensitive: bool,
    text: str,
    make_update_data: Callable[[str], Update],
) -> None:
    def _func() -> None:
        raise RuntimeError

    matcher = CommandMatcher(
        command,
        action=_func,
        case_sensitive=case_sensitive,
        prefixes=prefixes,
    )
    update = make_update_data(text)
    assert matcher._check(update=update) is None


async def test_regex_matcher_success(
    make_update_data: Callable[[str], Update],
) -> None:
    def _func() -> None:
        raise RuntimeError

    matcher = RegExMatcher(
        "^a...s$",
        action=_func,
    )
    update = make_update_data("abyss")
    assert matcher._check(update=update) == ["abyss"]
    with raises(RuntimeError):
        await matcher._call_action(
            api=TelegramBotAPI(token="123:abc"),
            update=update,
            results=(),
        )


async def test_regex_matcher_fail(
    make_update_data: Callable[[str], Update],
) -> None:
    def _func() -> None:
        raise RuntimeError

    matcher = RegExMatcher(
        "^a...s$",
        action=_func,
    )
    update = make_update_data("abyss22")
    assert matcher._check(update=update) is None
