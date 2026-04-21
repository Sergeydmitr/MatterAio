from __future__ import annotations

from types import TracebackType
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .channels import ChannelsResource
from .config import MattermostConfig
from .exceptions import ApiError, AuthError, RateLimitError, TransportError
from .files import FilesResource
from .models import ErrorResponse
from .posts import PostsResource
from .users import UsersResource

ModelT = TypeVar("ModelT", bound=BaseModel)


class MattermostClient:
    def __init__(
            self,
            base_url: str,
            token: str,
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

        self._client = httpx.AsyncClient(
            base_url=self.config.api_base_url,
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Accept": "application/json",
            },
            timeout=timeout_config,
            limits=limits,
            transport=transport,
        )

        self.channels = ChannelsResource(self)
        self.files = FilesResource(self)
        self.users = UsersResource(self)
        self.posts = PostsResource(self)

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
        return model_type.model_validate(response.json())

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

    @staticmethod
    def _parse_retry_after(value: str | None) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except ValueError:
            return None
