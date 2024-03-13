from asyncio import gather
from collections.abc import AsyncGenerator, Callable, MutableMapping, Sequence
from contextlib import (
    AbstractAsyncContextManager,
    _AsyncGeneratorContextManager,
    asynccontextmanager,
)
from typing import Any, final

from chatushka._constants import (
    HTTP_POOLING_TIMEOUT,
)
from chatushka._matchers import CommandMatcher, EventMatcher, Matcher, RegExMatcher
from chatushka._models import Events
from chatushka._transport import TelegramBotAPI


@asynccontextmanager
async def _default_lifespan(
    _: "Chatushka",
) -> AsyncGenerator[None, None]:
    yield


@final
class Chatushka:
    def __init__(
        self,
        *,
        token: str,
        cmd_prefixes: str | Sequence[str] = (),
        lifespan: AbstractAsyncContextManager | None = None,
    ) -> None:
        self._state: MutableMapping = {}
        self._lifespan: (
            AbstractAsyncContextManager[Any]
            | Callable[[Chatushka], _AsyncGeneratorContextManager[None]]
        ) = (lifespan or _default_lifespan)
        self._token = token
        if isinstance(cmd_prefixes, str):
            cmd_prefixes = [cmd_prefixes]
        self._cmd_prefixes = cmd_prefixes
        self._matchers: list[Matcher] = []  # type: ignore

    def add_matcher(
        self,
        matcher: Matcher,
    ) -> None:
        if isinstance(matcher, CommandMatcher):
            matcher.add_commands_prefixes(
                self._cmd_prefixes,
            )
        self._matchers.append(matcher)

    def add_cmd(
        self,
        *commands: str,
        action: Callable,
        case_sensitive: bool = False,
        chance_rate: float = 1.0,
    ):
        self.add_matcher(
            CommandMatcher(
                *commands,
                action=action,
                case_sensitive=case_sensitive,
                chance_rate=chance_rate,
            )
        )

    def cmd(
        self,
        *commands: str,
        case_sensitive: bool = False,
        chance_rate: float = 1.0,
    ) -> Callable:
        def _wrapper(
            func,
        ) -> None:
            self.add_cmd(
                *commands,
                action=func,
                case_sensitive=case_sensitive,
                chance_rate=chance_rate,
            )

        return _wrapper

    def add_regex(
        self,
        *patterns: str,
        action: Callable,
        chance_rate: float = 1.0,
    ):
        self.add_matcher(
            RegExMatcher(
                *patterns,
                action=action,
                chance_rate=chance_rate,
            )
        )

    def regex(
        self,
        *patterns: str,
        chance_rate: float = 1.0,
    ) -> Callable:
        def _wrapper(
            func,
        ) -> None:
            self.add_regex(
                *patterns,
                action=func,
                chance_rate=chance_rate,
            )

        return _wrapper

    def add_event(
        self,
        event: Events,
        action: Callable,
        chance_rate: float = 1.0,
    ) -> None:
        self.add_matcher(
            EventMatcher(
                event=event,
                action=action,
                chance_rate=chance_rate,
            )
        )

    def event(
        self,
        event: Events,
        chance_rate: float = 1.0,
    ) -> Callable:
        def _wrapper(
            func,
        ) -> None:
            self.add_event(
                event=event,
                action=func,
                chance_rate=chance_rate,
            )

        return _wrapper

    async def _check_updates(
        self,
        api: TelegramBotAPI,
        offset: int | None,
    ) -> int | None:
        updates, offset = await api.get_updates(offset)
        if not updates:
            return offset
        await gather(
            *[
                matcher(  # type: ignore
                    api=api,
                    update=update,
                )
                for update in updates
                for matcher in self._matchers
            ]
        )
        return offset

    async def _loop(
        self,
    ) -> None:
        offset: int | None = None
        while True:
            async with TelegramBotAPI(
                token=self._token,
                timeout=HTTP_POOLING_TIMEOUT,
            ) as api:
                offset = await self._check_updates(
                    api=api,
                    offset=offset,
                )

    async def run(
        self,
    ) -> None:
        async with self._lifespan(
            self,
        ):
            await self._loop()
