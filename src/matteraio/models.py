from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MattermostModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class User(MattermostModel):
    id: str
    username: str
    email: str | None = None


class UserLoginRequest(MattermostModel):
    login_id: str
    password: str
    token: str | None = None


class LoginResponse(MattermostModel):
    user: User
    token: str


class UserSearchRequest(MattermostModel):
    term: str
    team_id: str | None = None
    not_in_team_id: str | None = None
    in_channel_id: str | None = None
    not_in_channel_id: str | None = None
    in_group_id: str | None = None
    group_constrained: bool | None = None
    allow_inactive: bool | None = None
    without_team: bool | None = None
    limit: int | None = None


class Team(MattermostModel):
    id: str
    name: str
    display_name: str
    type: str
    description: str | None = None
    company_name: str | None = None
    allowed_domains: str | None = None
    invite_id: str | None = None
    allow_open_invite: bool | None = None


class TeamCreateRequest(MattermostModel):
    name: str
    display_name: str
    type: str


class TeamSearchRequest(MattermostModel):
    term: str
    page: int | None = None
    per_page: int | None = None
    allow_open_invite: bool | None = None
    group_constrained: bool | None = None
    exclude_policy_constrained: bool | None = None


class TeamUpdateRequest(MattermostModel):
    id: str
    display_name: str
    description: str
    company_name: str
    allowed_domains: str
    invite_id: str
    allow_open_invite: bool


class TeamPatchRequest(MattermostModel):
    display_name: str | None = None
    description: str | None = None
    company_name: str | None = None
    invite_id: str | None = None
    allow_open_invite: bool | None = None


class TeamMember(MattermostModel):
    team_id: str
    user_id: str
    roles: str
    delete_at: int | None = None
    scheme_user: bool | None = None
    scheme_admin: bool | None = None
    explicit_roles: str | None = None


class TeamMemberAddRequest(MattermostModel):
    team_id: str
    user_id: str


class TeamMemberRolesRequest(MattermostModel):
    roles: str


class Channel(MattermostModel):
    id: str
    team_id: str | None = None
    name: str
    display_name: str
    type: str
    purpose: str | None = None
    header: str | None = None
    total_msg_count: int | None = None


class ChannelCreateRequest(MattermostModel):
    team_id: str
    name: str
    display_name: str
    type: str
    purpose: str | None = None
    header: str | None = None


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


class StatusOK(MattermostModel):
    status: str


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
