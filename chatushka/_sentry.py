from contextlib import suppress

from httpx import RequestNotRead

from chatushka._errors import ChatushkaResponseError

try:
    import sentry_sdk  # type: ignore
except ImportError:
    sentry_sdk = None  # type: ignore


def report_exc(
    exc: Exception,
) -> None:
    with sentry_sdk.push_scope() as scope:
        if isinstance(exc, ChatushkaResponseError):
            scope.set_extra(
                "response",
                {
                    "status": exc.response.status_code,
                    "data": exc.response.json(),
                },
            )
            with suppress(UnicodeDecodeError, RequestNotRead):
                scope.set_extra(
                    "request",
                    exc.response.request.content.decode(),
                )
            sentry_sdk.capture_exception(exc)
