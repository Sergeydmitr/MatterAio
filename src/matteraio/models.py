from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MattermostModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class User(MattermostModel):
    id: str
    username: str
    email: str | None = None


class Channel(MattermostModel):
    id: str
    team_id: str | None = None
    name: str
    display_name: str
    type: str
    purpose: str | None = None
    header: str | None = None
    total_msg_count: int | None = None


class Post(MattermostModel):
    id: str
    channel_id: str
    message: str
    user_id: str | None = None
    root_id: str | None = None
    file_ids: list[str] = Field(default_factory=list)


class PostCreateRequest(MattermostModel):
    channel_id: str
    message: str
    root_id: str | None = None
    file_ids: list[str] | None = None


class ErrorResponse(MattermostModel):
    id: str
    message: str
    detailed_error: str | None = None
    request_id: str | None = None
    status_code: int | None = None


class FileInfo(MattermostModel):
    id: str
    user_id: str | None = None
    channel_id: str | None = None
    post_id: str | None = None
    name: str
    extension: str | None = None
    size: int | None = None
    mime_type: str | None = None
    width: int | None = None
    height: int | None = None
    has_preview_image: bool | None = None


class FileUploadResponse(MattermostModel):
    file_infos: list[FileInfo]
    client_ids: list[str] = Field(default_factory=list)
