import signal
from asyncio import ensure_future, gather, get_event_loop
from collections.abc import Callable, Sequence
from datetime import timezone, tzinfo
from traceback import print_exception

import aiocron  # type: ignore

from chatushka._constants import HTTP_POOLING_TIMEOUT, HTTP_REGULAR_TIMEOUT
from chatushka._errors import ChatushkaResponseError
from chatushka._logger import logger
from chatushka._matchers import CommandMatcher, Matcher, TelegramBotAPI
from chatushka._sentry import report_exc


class BotBase:
    def __init__(
        self,
        *,
        token: str,
        cmd_prefixes: str | Sequence[str],
    ) -> None:
        self._matchers: list[Matcher] = []  # type: ignore
        self._schedulers: list[aiocron.Cron] = []
        self._token = token
        if isinstance(cmd_prefixes, str):
            cmd_prefixes = [cmd_prefixes]
        self._cmd_prefixes = cmd_prefixes
        self._closed: bool = True

    @property
    def matchers(
        self,
    ) -> list[Matcher]:
        return self._matchers

    def __repr__(
        self,
    ) -> str:
        return f"<{self.__class__.__name__}: {len(self._matchers)} matchers, {len(self._schedulers)} schedulers>"

    def add(
        self,
        matcher: Matcher,
    ) -> None:
        if isinstance(matcher, CommandMatcher):
            matcher.add_commands_prefixes(
                self._cmd_prefixes,
            )
        logger.info(f"{self} + {matcher}")
        self._matchers.append(matcher)

    async def _call_scheduled(
        self,
        func,
    ):
        logger.info(f"{self} ::: scheduled call of {func.__name__}")
        async with self._make_api_client() as client:
            await func(
                api=client,
            )

    def schedule(
        self,
        cron: str,
        tz: tzinfo = timezone.utc,
    ) -> Callable[[Callable], None]:
        def _wrapper(
            func,
        ):
            job = aiocron.Cron(
                spec=cron,
                func=self._call_scheduled,
                start=False,
                tz=tz,
                args=(func,),
            )
            logger.info(f"{self} + {job!r}")
            self._schedulers.append(job)

        return _wrapper

    async def _check_updates(
        self,
        api: TelegramBotAPI,
        offset: int | None,
    ) -> int | None:
        try:
            updates, offset = await api.get_updates(offset)
        except (Exception, ChatushkaResponseError) as exc:
            report_exc(exc)
            return offset
        if not updates:
            return offset
        logger.debug(f"{self} <<< {len(updates)} updates from {offset=}")
        results = await gather(
            *[
                matcher(  # type: ignore
                    api=api,
                    update=update,
                )
                for update in updates
                for matcher in self._matchers
            ],
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                print_exception(result)
                report_exc(result)
        return offset

    async def _loop(
        self,
    ) -> None:
        offset: int | None = None
        while not self._closed:
            async with TelegramBotAPI(
                token=self._token,
                timeout=HTTP_POOLING_TIMEOUT,
            ) as api:
                offset = await self._check_updates(
                    api=api,
                    offset=offset,
                )

    def _make_api_client(
        self,
        timeout: int = HTTP_REGULAR_TIMEOUT,
    ) -> TelegramBotAPI:
        return TelegramBotAPI(
            token=self._token,
            timeout=timeout,
        )

    async def _stop(
        self,
    ) -> None:
        self._closed = True
        logger.info(f"{self} (っ◔◡◔)っ stop chats reading")
        if self._schedulers:
            logger.info(f"{self} (っ◔◡◔)っ stop schedulers")
        for scheduler in self._schedulers:
            scheduler.stop()
        logger.info(f"{self} (っ◔◡◔)っ closed")

    async def run(
        self,
    ) -> None:
        loop = get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, callback=lambda: ensure_future(self._stop()))
            except NotImplementedError:
                break
        for scheduler in self._schedulers:
            logger.info(f"{self} (っ◔◡◔)っ start scheduler {scheduler!r}")
            scheduler.start()
        logger.info(f"{self} (っ◔◡◔)っ start polling")
        self._closed = False
        await self._loop()
