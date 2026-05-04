from __future__ import annotations

import asyncio
import os
from time import monotonic
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio

INTEGRATION_PASSWORD = "MatterAio-Integration-Password-1!"


def _api_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/api/v4"):
        return normalized
    return f"{normalized}/api/v4"


async def _wait_for_server(base_url: str, timeout: float = 180.0) -> None:
    deadline = monotonic() + timeout

    async with httpx.AsyncClient(
        base_url=_api_base_url(base_url),
        timeout=5.0,
        follow_redirects=True,
    ) as client:
        while monotonic() < deadline:
            try:
                response = await client.get("/system/ping")
            except httpx.HTTPError:
                response = None

            if response is not None and response.is_success:
                return

            await asyncio.sleep(1.0)

    raise RuntimeError("Timed out waiting for the Mattermost integration server to become ready.")


@pytest.fixture
def integration_base_url() -> str:
    if os.getenv("MATTERAIO_RUN_INTEGRATION") != "1":
        pytest.skip("integration tests are disabled; set MATTERAIO_RUN_INTEGRATION=1")

    return os.getenv("MATTERAIO_BASE_URL", "http://127.0.0.1:8065").rstrip("/")


@pytest_asyncio.fixture
async def integration_workspace(integration_base_url: str) -> dict[str, str]:
    await _wait_for_server(integration_base_url)

    suffix = uuid4().hex[:10]
    username = f"matteraio{suffix}"
    email = f"{username}@example.com"
    password = INTEGRATION_PASSWORD
    team_name = f"team{suffix}"
    channel_name = f"channel{suffix}"

    async with httpx.AsyncClient(
        base_url=_api_base_url(integration_base_url),
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        create_user_response = await client.post(
            "/users",
            json={
                "email": email,
                "username": username,
                "password": password,
            },
        )
        create_user_response.raise_for_status()

        login_response = await client.post(
            "/users/login",
            json={
                "login_id": email,
                "password": password,
            },
        )
        login_response.raise_for_status()

        token = login_response.headers.get("Token")
        if token is None:
            raise RuntimeError("Mattermost login response did not include a Token header.")

        headers = {"Authorization": f"Bearer {token}"}

        create_team_response = await client.post(
            "/teams",
            headers=headers,
            json={
                "name": team_name,
                "display_name": f"MatterAio {suffix}",
                "type": "O",
            },
        )
        create_team_response.raise_for_status()
        team_id = create_team_response.json()["id"]

        create_channel_response = await client.post(
            "/channels",
            headers=headers,
            json={
                "team_id": team_id,
                "name": channel_name,
                "display_name": f"MatterAio {suffix}",
                "type": "O",
            },
        )
        create_channel_response.raise_for_status()
        channel_id = create_channel_response.json()["id"]

    return {
        "base_url": integration_base_url,
        "token": token,
        "email": email,
        "password": password,
        "username": username,
        "team_id": team_id,
        "team_name": team_name,
        "channel_id": channel_id,
        "channel_name": channel_name,
    }
