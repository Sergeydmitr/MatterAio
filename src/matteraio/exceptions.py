from __future__ import annotations


class MattermostError(Exception):
    pass


class TransportError(MattermostError):
    pass


class ApiError(MattermostError):
    def __init__(
            self,
            message: str,
            *,
            status_code: int,
            error_id: str | None = None,
            request_id: str | None = None,
            detailed_error: str | None = None,
            retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_id = error_id
        self.request_id = request_id
        self.detailed_error = detailed_error
        self.retry_after = retry_after


class AuthError(ApiError):
    pass


class RateLimitError(ApiError):
    pass


class WebSocketError(MattermostError):
    pass


class WebSocketConnectionError(WebSocketError):
    pass


class WebSocketNotConnectedError(WebSocketError):
    pass


class WebSocketProtocolError(WebSocketError):
    pass
