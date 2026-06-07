# Changelog

## v0.2.0 - 2026-06-07

Productization pass for the first reusable release.

- Added GitHub Actions CI for Python compile checks, offline plugin smoke, and package file validation.
- Added `scripts/offline_smoke_test.py` so CI can verify plugin registration without Hermes Agent or a live Portal token.
- Added `dryRun` support for `office_kanban_create_task` and `office_kanban_create_plan`.
- Added `docs/API_CONTRACT.md` with Portal endpoint, payload, metadata, and safety-boundary contract.
- Improved `scripts/install.sh` profile-path detection through `hermes config path`, with `rsync` fallback and clearer next steps.
- Expanded README with dry-run, CI, troubleshooting, and API contract references.

## v0.1.0 - 2026-06-07

Initial standalone plugin release.

- Added Portal tools for status, proposed tasks, proposed plans, messages, and task patches.
- Added slash commands: `/plan`, `/office-status`, `/blockers`, `/assign`.
- Added Telegram `pre_gateway_dispatch` rewrites for planning and read-only status phrases.
- Bundled planning/portal skills:
  - `agent-command-pipeline`
  - `kanban-orchestrator`
  - `portal-inbox`
  - `telegram-planning-contract`
- Added install and Hermes smoke-test scripts.
