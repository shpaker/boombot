import signal
from asyncio import ensure_future, get_event_loop, sleep
from logging import getLogger
from typing import Iterable, Optional

from twowires.matchers import EventsMatcher, EventTypes, MatcherProtocol
from twowires.transports.telegram_bot_api import TelegramBotApi

logger = getLogger(__name__)


class WatchDogBot(EventsMatcher):
    def __init__(
        self,
        token: str,
        matchers: Iterable[MatcherProtocol] = None,
        debug: bool = False,
    ) -> None:
        super().__init__()
        self.debug = debug
        self.api = TelegramBotApi(token)
        self.matchers = list(matchers) if matchers else list()

    def add_matcher(
        self,
        matcher: MatcherProtocol,
    ):
        self.matchers.append(matcher)

    async def _loop(self) -> None:
        offset: Optional[int] = None
        while True:
            updates, latest_update_id = await self.api.get_updates(timeout=60, offset=offset)
            if updates:
                for update in updates:
                    try:
                        for matcher in self.matchers:
                            await matcher.match(self.api, update.message)
                    except Exception as err:  # noqa, pylint: disable=broad-except
                        if self.debug:
                            raise
                        logger.erro(err)
                offset = latest_update_id + 1
            await sleep(1)

    async def _close(self) -> None:
        await self.call(self.api, EventTypes.SHUTDOWN)

    async def serve(self) -> None:
        loop = get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, callback=lambda: ensure_future(self._close()))
            except NotImplementedError:
                break
        await self.call(self.api, EventTypes.STARTUP)
        await self._loop()
