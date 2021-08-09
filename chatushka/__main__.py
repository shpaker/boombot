from asyncio import run
from logging import DEBUG, INFO, WARNING, basicConfig, getLogger

from chatushka import samples
from chatushka.bot import Chatushka
from chatushka.matchers import CommandsMatcher, RegexMatcher
from chatushka.samples.heroes import add_heroes_matchers

from chatushka.services.mongodb.wrapper import MongoDBWrapper
from chatushka.settings import get_settings

logger = getLogger()
settings = get_settings()


def make_regex_matcher():
    matcher = RegexMatcher()
    matcher.add_handler(r"\?", samples.random_eight_ball_answer)
    return matcher


def make_commands_matcher():
    matcher = CommandsMatcher(
        prefixes=settings.command_prefixes,
        postfixes=settings.command_postfixes,
        allow_raw=True,
    )
    matcher.add_handler("id", samples.user_id)
    matcher.add_handler("joke", samples.joke)
    matcher.add_handler(("8ball", "ball8", "b8", "8b"), samples.eight_ball_answer)
    return matcher


def make_sensitive_matcher():
    matcher = CommandsMatcher(
        prefixes=settings.command_prefixes,
        postfixes=settings.command_postfixes,
    )
    matcher.add_handler(("suicide", "wtf"), samples.suicide)
    return matcher


def make_privilege_matcher():
    matcher = CommandsMatcher(
        prefixes=settings.command_prefixes,
        postfixes=settings.command_postfixes,
        whitelist=settings.admins,
    )
    matcher.add_handler("mute", samples.mute)
    return matcher


def make_bot() -> Chatushka:
    instance = Chatushka(token=settings.token, debug=settings.debug)
    wrapper = MongoDBWrapper()
    wrapper.add_event_handlers(instance)
    add_heroes_matchers(instance)
    instance.add_matchers(
        make_commands_matcher(),
        make_sensitive_matcher(),
        make_privilege_matcher(),
        make_regex_matcher(),
    )
    return instance


def main():
    basicConfig(level=DEBUG if settings.debug else INFO)
    logger.debug("Debug mode is on".upper())
    getLogger("httpx").setLevel(WARNING)
    bot = make_bot()
    run(bot.serve())


if __name__ == "__main__":
    main()
