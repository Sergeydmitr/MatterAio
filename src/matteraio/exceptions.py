from __future__ import annotations


class MattermostError(Exception):
    pass


class TransportError(MattermostError):
    pass


class ResponseValidationError(MattermostError):
    def __init__(
        self,
        message: str,
        *,
        method: str,
        path: str,
        status_code: int,
        request_id: str | None = None,
        raw_body: str | None = None,
        reason: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.method = method
        self.path = path
        self.status_code = status_code
        self.request_id = request_id
        self.raw_body = raw_body
        self.reason = reason


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


class WebSocketDisconnectedError(WebSocketConnectionError):
    def __init__(
        self,
        message: str,
        *,
        close_code: int | None = None,
        close_reason: str | None = None,
    ) -> None:
        super().__init__(message)
        self.close_code = close_code
        self.close_reason = close_reason


class WebSocketNotConnectedError(WebSocketError):
    pass


class WebSocketProtocolError(WebSocketError):
    pass


class WebSocketTimeoutError(WebSocketError):
    pass
