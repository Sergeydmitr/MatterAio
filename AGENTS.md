# Repository Guidelines

## Project Structure & Module Organization

This is an async Python package for Mattermost APIs. Source code lives in
`src/matteraio/`, with one module per client area: `client.py`, `users.py`, `channels.py`,
`posts.py`, `files.py`, `websocket.py`, plus shared `models.py`, `events.py`,
`config.py`, and `exceptions.py`. Public exports are collected in `src/matteraio/__init__.py`.

Tests live in `tests/`. Unit tests are top-level `test_*.py` files, while live Mattermost
coverage is under `tests/integration/`. CI configuration is in `.github/workflows/ci.yml`.
The local integration service is defined in `docker-compose.integration.yml`.

## Build, Test, and Development Commands

- `uv sync --all-groups`: install runtime and development dependencies.
- `uv run ruff format .`: format the package and tests.
- `uv run ruff check .`: run lint checks.
- `uv run mypy src tests`: run strict type checks.
- `uv run pytest`: run the default unit test suite.
- `docker compose -f docker-compose.integration.yml up -d`: start the local Mattermost
  preview server for live tests.
- `MATTERAIO_RUN_INTEGRATION=1 uv run pytest tests/integration -m integration`: run live tests.

## Coding Style & Naming Conventions

Target Python 3.12. Ruff is authoritative for formatting and imports, with a 100-character
line length and lint rules `E`, `F`, `I`, and `UP`. Keep APIs async-only and explicit; avoid
helper methods that hide multiple Mattermost API calls. Use typed signatures for new code:
mypy requires typed definitions, checks untyped bodies, and rejects implicit optional types.

## Testing Guidelines

Use pytest with `pytest-asyncio` in auto mode. Name unit files `test_<area>.py` and test
functions `test_<expected_behavior>`. Put network-dependent tests in `tests/integration/`,
mark them with `@pytest.mark.integration`, and keep them skipped unless
`MATTERAIO_RUN_INTEGRATION=1` is set. Add focused tests for client methods, models, errors,
and WebSocket parsing.

## Commit & Pull Request Guidelines

Recent commits use short Conventional Commit-style prefixes such as `feat:` and `fix:`.
Keep subjects imperative and scoped to one change. Pull requests should describe the behavior
change, list validation commands, link related issues, and include logs only for user-visible
or integration-test evidence.

## Security & Configuration Tips

Do not commit tokens, Mattermost credentials, or local `.env` files. Use environment variables
for live tests, such as `MATTERAIO_BASE_URL` and `MATTERAIO_RUN_INTEGRATION`. Treat the
Mattermost preview container as local test infrastructure only.

## Agent-Specific Instructions

For code discovery, prefer the codebase-memory MCP graph tools before grep-style searches:
`search_graph`, `trace_path`, `get_code_snippet`, `query_graph`, then `get_architecture`.
Use shell search only for config files, string literals, or when the graph is insufficient.
