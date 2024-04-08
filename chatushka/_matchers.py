from abc import ABC, abstractmethod
from asyncio import iscoroutinefunction
from collections.abc import Callable, Sequence
from inspect import signature
from random import random
from re import Pattern, RegexFlag, compile
from typing import Any, TypeVar

from pydantic import BaseModel

from chatushka._logger import logger
from chatushka._models import Events, Update
from chatushka._transport import TelegramBotAPI

Matcher = TypeVar("Matcher", bound="BaseMatcher")


class BaseMatcher(
    ABC,
):
    def __init__(
        self,
        action: Callable,
        chance_rate: float = 1.0,
        results_model: type[Any] | None = None,
    ) -> None:
        self._action: Callable = action
        self._chance_rate = chance_rate
        self._results_model = results_model

    @property
    def action(
        self,
    ) -> Callable:
        return self._action

    @abstractmethod
    def _check(
        self,
        update: Update,
    ) -> list[str] | None:
        raise NotImplementedError

    async def __call__(
        self,
        api: TelegramBotAPI,
        update: Update,
    ) -> None:
        if (
            results := self._check(
                update=update,
            )
        ) is None:
            return
        logger.info(f"{self} matched with update_id={update.update_id} {results=}")
        if (
            result := await self._call_action(
                api=api,
                update=update,
                results=results,
            )
        ) and update.message:
            await api.send_message(
                chat_id=update.message.chat.id,
                reply_to_message_id=update.message.message_id,
                text=result,
            )

    def _get_chance(
        self,
    ) -> bool:
        return random() <= self._chance_rate

    def _make_results_model(
        self,
        results: list[str],
    ) -> Any:
        if self._results_model is None:
            return None
        if issubclass(self._results_model, BaseModel):
            params = {}
            for i, name in enumerate(self._results_model.model_fields):
                if len(results) < i:
                    break
                params[name] = results[i]
            return self._results_model.model_validate(params)
        return self._results_model(results)

    async def _call_action(
        self,
        api: TelegramBotAPI,
        update: Update,
        results: Any,
    ) -> str | None:
        if not self._get_chance():
            return None
        kwargs = {}
        results_from_model = self._make_results_model(results)
        kwargs.update(
            {
                "api": api,
                "update": update,
                "message": update.message,
                "chat": update.message.chat if update.message else None,
                "user": update.message.user if update.message else None,
                "results": results_from_model or results,
            }
        )
        sig = signature(self._action)
        kwargs = {param: kwargs.get(param) for param in sig.parameters if param in kwargs}
        if update and update.message is not None and "message" in sig.parameters:
            kwargs["message"] = update.message
        if iscoroutinefunction(self._action):
            return await self._action(**kwargs)
        return self._action(**kwargs)


class CommandMatcher(
    BaseMatcher,
    ABC,
):
    def __init__(
        self,
        *commands: str,
        action: Callable,
        prefixes: str | Sequence[str] = (),
        case_sensitive: bool = False,
        chance_rate: float = 1.0,
        results_model: type[Any] | None = None,
    ) -> None:
        super().__init__(
            action=action,
            chance_rate=chance_rate,
            results_model=results_model,
        )
        if case_sensitive:
            commands = tuple(command.upper() for command in commands)
        self._commands = commands
        self._case_sensitive = case_sensitive
        if prefixes:
            self.add_commands_prefixes(prefixes)

    def __repr__(
        self,
    ) -> str:
        return f"<{self.__class__.__name__}: {', '.join(self._commands)}>"

    def add_commands_prefixes(
        self,
        prefixes: Sequence[str],
    ) -> None:
        if not prefixes:
            return
        self._commands = tuple(f"{prefix}{command}" for command in self._commands for prefix in prefixes)

    def _make_args(
        self,
        text: str,
    ) -> list[str]:
        args = [arg for arg in text.split(" ") if arg]
        if len(args) == 1:
            return []
        return args[1:]

    def _check(
        self,
        update: Update,
    ) -> list[str] | None:
        if not update.message or not update.message.text:
            return None
        case_sensitive = self._case_sensitive or False
        for command in self._commands:
            if case_sensitive and update.message.text.upper().startswith(command.upper()):
                return self._make_args(update.message.text)
            if update.message.text.startswith(command):
                return self._make_args(update.message.text)
        return None


class RegExMatcher(
    BaseMatcher,
    ABC,
):
    def __init__(
        self,
        *patterns: str | Pattern,
        action: Callable,
        re_flags: int | RegexFlag = 0,
        chance_rate: float = 1.0,
        results_model: type[Any] | None = None,
    ) -> None:
        super().__init__(
            action=action,
            chance_rate=chance_rate,
            results_model=results_model,
        )
        self._patterns = [
            compile(pattern, flags=re_flags) if isinstance(pattern, str) else pattern for pattern in patterns
        ]

    def __repr__(
        self,
    ) -> str:
        return f"<{self.__class__.__name__}: {', '.join([entry.pattern for entry in self._patterns])}>"

    def _check(
        self,
        update: Update,
    ) -> list[str] | None:
        if not update.message or not update.message.text:
            return None
        for pattern in self._patterns:
            if result := pattern.findall(update.message.text):
                return result
        return None


class EventMatcher(
    BaseMatcher,
    ABC,
):
    def __init__(
        self,
        *events: Events,
        action: Callable,
        chance_rate: float = 1.0,
        results_model: type[Any] | None = None,
    ) -> None:
        super().__init__(
            action=action,
            chance_rate=chance_rate,
            results_model=results_model,
        )
        self._events = events

    def __repr__(
        self,
    ) -> str:
        return f"<{self.__class__.__name__}: {', '.join(self._events)}>"

    def _check(
        self,
        update: Update,
    ) -> list[str] | None:
        results = []
        if update.message and update.message.text and "on_message" in self._events:
            results.append("on_message")
        if update.message and update.message.new_chat_members and "on_new_chat_members" in self._events:
            results.append("on_new_chat_members")
        if update.message and update.message.new_chat_members and "on_left_chat_member" in self._events:
            results.append("on_left_chat_member")
        if not results:
            return None
        return results
