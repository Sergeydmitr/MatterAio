# Changelog

## 1.1.1 - 2026-05-05

### Added

- Async pagination iterators for teams, team members, channels, channel members, and channel
  posts.
- `ResponseValidationError` for successful REST responses that do not match expected typed
  models.

### Fixed

- Quote dynamic REST path segments before sending requests.

## 1.0.2 - 2026-05-05

### Fixed

- Pinned `astral-sh/setup-uv` to the resolvable `v8.1.0` tag in GitHub Actions
  workflows.

## 1.0.1 - 2026-05-04

### Fixed

- Updated GitHub Actions workflow actions to Node.js 24-compatible versions.

## 1.0.0 - 2026-05-04

First production/stable release.

### Added

- Async Mattermost REST client for users/auth, teams, channels, posts, reactions, and files.
- Typed Pydantic response models for supported Mattermost REST resources.
- Mattermost WebSocket client with typed `hello`, `posted`, and `status_change` events.
- Decorator-based WebSocket event routers and dispatcher.
- Resource-level endpoint documentation with returned data structures and request examples.
- GitHub Actions workflow for publishing distributions to PyPI.

### Notes

- MatterAio keeps the client explicit and async-only; methods map directly to Mattermost API
  calls without hidden multi-step workflows.
- Live Mattermost coverage remains opt-in via `MATTERAIO_RUN_INTEGRATION=1`.
