from __future__ import annotations

from dataclasses import dataclass, replace
from types import TracebackType
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .channels import ChannelsResource
from .config import MattermostConfig
from .exceptions import (
    ApiError,
    AuthError,
    MattermostError,
    RateLimitError,
    ResponseValidationError,
    TransportError,
)
from .files import FilesResource
from .models import ErrorResponse, User
from .posts import PostsResource
from .reactions import ReactionsResource
from .teams import TeamsResource
from .users import UsersResource

ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(frozen=True)
class BotSession:
    user: User

    @property
    def user_id(self) -> str:
        return self.user.id

    @property
    def username(self) -> str:
        return self.user.username

    @property
    def email(self) -> str | None:
        return self.user.email


class MattermostClient:
    def __init__(
        self,
        base_url: str,
        token: str = "",
        *,
        timeout: float = 10.0,
        connect_timeout: float = 5.0,
        max_connections: int = 20,
        max_keepalive_connections: int = 10,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.config = MattermostConfig(
            base_url=base_url,
            token=token,
            timeout=timeout,
            connect_timeout=connect_timeout,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )

        timeout_config = httpx.Timeout(self.config.timeout, connect=self.config.connect_timeout)
        limits = httpx.Limits(
            max_connections=self.config.max_connections,
            max_keepalive_connections=self.config.max_keepalive_connections,
        )

        headers = {"Accept": "application/json"}
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"

        self._client = httpx.AsyncClient(
            base_url=self.config.api_base_url,
            headers=headers,
            timeout=timeout_config,
            limits=limits,
            transport=transport,
        )

        self.channels = ChannelsResource(self)
        self.files = FilesResource(self)
        self.users = UsersResource(self)
        self.posts = PostsResource(self)
        self.reactions = ReactionsResource(self)
        self.teams = TeamsResource(self)
        self._bot_session: BotSession | None = None

    async def __aenter__(self) -> MattermostClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    @property
    def bot_session(self) -> BotSession | None:
        return self._bot_session

    async def init_session(self) -> BotSession:
        if self._bot_session is not None:
            return self._bot_session

        user = await self.users.me()
        return self._set_bot_session(user)

    def require_session(self) -> BotSession:
        if self._bot_session is None:
            raise MattermostError("Session is not initialized. Call await client.init_session().")
        return self._bot_session

    def _ensure_login_allowed(self) -> None:
        if self.config.token:
            raise MattermostError(
                "MattermostClient already has a token. Create a new client to log in again."
            )

    def _set_token(self, token: str) -> None:
        if self.config.token and self.config.token != token:
            raise MattermostError(
                "MattermostClient token is already set. Create a new client to use another token."
            )
        self.config = replace(self.config, token=token)
        self._client.headers["Authorization"] = f"Bearer {token}"

    def _set_bot_session(self, user: User) -> BotSession:
        if self._bot_session is not None:
            if self._bot_session.user_id != user.id:
                raise MattermostError(
                    "Session is already initialized for another user. "
                    "Create a new client to use another token."
                )
            return self._bot_session

        self._bot_session = BotSession(user=user)
        return self._bot_session

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise TransportError("Request to Mattermost failed") from exc

        if response.is_error:
            raise self._build_api_error(response)

        return response

    async def _request_model(
        self,
        method: str,
        path: str,
        model_type: type[ModelT],
        **kwargs: Any,
    ) -> ModelT:
        response = await self._request(method, path, **kwargs)
        return self._validate_response_model(response, model_type)

    def _response_json(self, response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise self._build_response_validation_error(
                response,
                "Mattermost returned invalid JSON.",
            ) from exc

    def _validate_response_model(
        self,
        response: httpx.Response,
        model_type: type[ModelT],
    ) -> ModelT:
        return self._validate_model_data(response, model_type, self._response_json(response))

    def _validate_model_data(
        self,
        response: httpx.Response,
        model_type: type[ModelT],
        data: Any,
    ) -> ModelT:
        try:
            return model_type.model_validate(data)
        except ValidationError as exc:
            raise self._build_response_validation_error(
                response,
                "Mattermost returned an unexpected response body.",
            ) from exc

    def _validate_model_list_data(
        self,
        response: httpx.Response,
        model_type: type[ModelT],
        data: Any,
    ) -> list[ModelT]:
        if not isinstance(data, list):
            raise self._build_response_validation_error(
                response,
                "Mattermost returned an unexpected response body.",
            )

        try:
            return [model_type.model_validate(item) for item in data]
        except ValidationError as exc:
            raise self._build_response_validation_error(
                response,
                "Mattermost returned an unexpected response body.",
            ) from exc

    def _build_api_error(self, response: httpx.Response) -> ApiError:
        try:
            payload = ErrorResponse.model_validate(response.json())
        except (ValidationError, ValueError, TypeError):
            payload = ErrorResponse(
                id="unknown_error",
                message=response.text or "Mattermost returned an error response.",
                detailed_error=None,
                request_id=None,
                status_code=response.status_code,
            )

        error_type: type[ApiError]
        if response.status_code in {401, 403}:
            error_type = AuthError
        elif response.status_code == 429:
            error_type = RateLimitError
        else:
            error_type = ApiError

        retry_after = self._parse_retry_after(response.headers.get("Retry-After"))
        return error_type(
            message=payload.message,
            status_code=response.status_code,
            error_id=payload.id,
            request_id=payload.request_id,
            detailed_error=payload.detailed_error,
            retry_after=retry_after,
        )

    def _build_response_validation_error(
        self,
        response: httpx.Response,
        reason: str,
    ) -> ResponseValidationError:
        method = ""
        path = ""
        try:
            request = response.request
        except RuntimeError:
            request = None

        if request is not None:
            method = request.method
            path = request.url.raw_path.decode("ascii", errors="replace")

        request_id = response.headers.get("X-Request-Id") or response.headers.get("X-Request-ID")
        return ResponseValidationError(
            reason,
            method=method,
            path=path,
            status_code=response.status_code,
            request_id=request_id,
            raw_body=response.text,
            reason=reason,
        )

    @staticmethod
    def _parse_retry_after(value: str | None) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except ValueError:
            return None
