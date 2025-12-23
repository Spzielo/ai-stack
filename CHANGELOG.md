# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.2.0] - 2025-12-23 (Infrastructure Hardening)

### Added
- **Dependency Management**: Migrated `python-runner` to **Poetry** (`pyproject.toml`, `poetry.lock`).
- **Notifications**: Integrated **Slack Incoming Webhooks** with dual-channel routing (`#cerveau-log`, `#cerveau-alert`) and Block Kit formatting.
- **Environment Management**: Added `make dev`, `make prod`, `make logs` shortcuts and environment separation via `docker-compose.override.yml`.
- **Documentation**: Added comprehensive `README.md`, `CHANGELOG.md`, `JOURNAL.md`, and Architecture Decision Records (ADR).

### Changed
- **Python Runner**: Refactored `Dockerfile` to use Poetry instead of `pip install`.
- **Notifications**: Reverted Pushover integration in favor of Slack for better team/log management.

## [0.1.0] - 2025-12-22 (Initial Release)

### Added
- **Core Architecture**: Docker Compose setup with `n8n`, `postgres`, `open-webui`, `qdrant`, and `python-runner`.
- **Database**: Dedicated `brain` Postgres database with migration scripts (`001_init.sql`).
- **API**: `python-runner` implementation using **FastAPI** (migrated from Flask).
- **Backups**: Automated backup scripts (`backup_brain.sh`) with Git auto-commit to private repository.
- **Security**: Tailscale integration for secure remote access without public ports.
- **Mobile**: Custom n8n Docker image to fix iOS Home Screen Icon "white square" issue.
