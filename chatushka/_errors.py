from httpx import Response


class ChatushkaError(
    Exception,
):
    pass


class ChatushkaResponseError(
    ChatushkaError,
):
    def __init__(
        self,
        response: Response,
    ) -> None:
        self.response = response
        super().__init__(f'Telegram BOT API response error:\n  {response.text}"')
