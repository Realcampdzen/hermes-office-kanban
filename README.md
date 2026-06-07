# hermes-office-kanban

Hermes Office Kanban plugin for Hermes Agent.

It packages the Real Lager / Hermes Office planning layer as an installable Hermes plugin:

- Portal API tools for tasks, plans, messages, updates, and status.
- Slash commands for planning and status.
- `pre_gateway_dispatch` hook for Telegram planning/status phrases.
- Bundled plugin skills for Agent Command Pipeline v13 and portal behavior.

## What it provides

### Tools

- `office_kanban_get_status`
- `office_kanban_create_task`
- `office_kanban_create_plan`
- `office_kanban_post_message`
- `office_kanban_update_task`

`office_kanban_create_task` and `office_kanban_create_plan` support `dryRun: true` to return normalized Portal requests without creating cards.

### Slash commands

- `/plan <goal>`
- `/office-status`
- `/blockers`
- `/assign <taskId> <agent>`

Note: `/status` is a built-in Hermes command, so this plugin uses `/office-status` for Portal status.

### Gateway hook

The plugin registers `pre_gateway_dispatch` and rewrites owner phrases into safer Hermes Office workflows.

Planning triggers include:

- `разбей цель`
- `создай план`
- `сделай карточки`
- `назначь DevBro`
- `назначь Кота`
- `назначь QA`

Read-only status triggers include:

- `что ждет одобрения`
- `что ждёт одобрения`
- `что на проверке`
- `какие блокеры`

Planning creates proposed cards only. It does not approve, reject, or run workflows.

## Requirements

Environment variables in the target Hermes profile `.env`:

```bash
KANBAN_PORTAL_AGENT_TOKEN=...
# optional overrides
KANBAN_PORTAL_URL=http://127.0.0.1:19600
KANBAN_PORTAL_AGENT_ID=neurostepa
```

Default Portal URL:

```text
http://127.0.0.1:19600
```

## Install

From this repo:

```bash
./scripts/install.sh neurostepa
```

For default Hermes home without profiles:

```bash
./scripts/install.sh default
```

The installer resolves the target plugin directory through `hermes config path` when the Hermes CLI is available. It falls back to:

```text
~/.hermes/plugins/hermes-office-kanban
~/.hermes/profiles/<profile>/plugins/hermes-office-kanban
```

Manual install:

```bash
PROFILE=neurostepa
PLUGIN_DIR="$(dirname "$(hermes --profile "$PROFILE" config path)")/plugins/hermes-office-kanban"
mkdir -p "$PLUGIN_DIR"
rsync -a --delete --exclude='.git' --exclude='__pycache__' ./ "$PLUGIN_DIR/"
hermes --profile "$PROFILE" plugins enable hermes-office-kanban
hermes --profile "$PROFILE" gateway restart
```

## Verify

```bash
hermes --profile neurostepa plugins list | grep hermes-office-kanban
hermes --profile neurostepa tools list | grep hermes_office_kanban

HERMES_PROFILE=neurostepa PYTHONPATH=/usr/local/lib/hermes-agent \
  /usr/local/lib/hermes-agent/venv/bin/python scripts/smoke_test.py
```

The Hermes smoke test verifies real plugin discovery, tools, commands, skills, and hook rewrites.

For CI or machines without Hermes installed:

```bash
python -m py_compile __init__.py scripts/smoke_test.py scripts/offline_smoke_test.py
python scripts/offline_smoke_test.py
```

The offline smoke test verifies registration and dry-run payloads with a fake plugin context. It does not require a Portal token.

## Dry-run examples

Create one normalized task payload without sending it:

```json
{
  "task": {
    "title": "Check Portal status",
    "assignedAgentId": "qa-engineer"
  },
  "dryRun": true
}
```

Create a normalized parent + child plan payload without sending it:

```json
{
  "goal": "Audit Kanban Portal release",
  "children": [
    {"title": "Backend API audit", "assignedAgentId": "backend-api"},
    {"title": "Frontend UX audit", "assignedAgentId": "frontend-swe"},
    {"title": "QA smoke", "assignedAgentId": "qa-engineer"}
  ],
  "dryRun": true
}
```

## API contract

See [docs/API_CONTRACT.md](docs/API_CONTRACT.md) for endpoint, payload, metadata, dry-run, and safety-boundary details.

## Troubleshooting

### Plugin is enabled but tools do not appear

Restart the gateway or start a new Hermes session. Plugin schemas are loaded at session start.

```bash
hermes --profile neurostepa gateway restart
```

Then verify:

```bash
hermes --profile neurostepa plugins list
hermes --profile neurostepa tools list | grep hermes_office_kanban
```

### Smoke test fails with `No module named hermes_cli`

Run the real smoke test through the Hermes installed venv:

```bash
HERMES_PROFILE=neurostepa PYTHONPATH=/usr/local/lib/hermes-agent \
  /usr/local/lib/hermes-agent/venv/bin/python scripts/smoke_test.py
```

Use the offline smoke test for CI/local checks without Hermes:

```bash
python scripts/offline_smoke_test.py
```

### Portal calls return `missing env KANBAN_PORTAL_AGENT_TOKEN`

Set the token in the active Hermes profile `.env`, not in the repo:

```bash
hermes --profile neurostepa config env-path
```

Add:

```bash
KANBAN_PORTAL_AGENT_TOKEN=...
```

Then restart the gateway.

### Portal calls return `401 Unauthorized`

Check that `KANBAN_PORTAL_AGENT_ID` matches the token's allowed agent identity and that the request targets the intended Portal URL.

```bash
KANBAN_PORTAL_URL=http://127.0.0.1:19600
KANBAN_PORTAL_AGENT_ID=neurostepa
```

### The plugin creates cards when I only asked for status

Read-only status phrases should be rewritten to `office_kanban_get_status`. If a new phrase is missing, add it to `STATUS_TRIGGERS` in `__init__.py` and update the smoke test.

## Development

```bash
python -m py_compile __init__.py scripts/smoke_test.py scripts/offline_smoke_test.py
python scripts/offline_smoke_test.py
```

Keep product policy in skills and mechanics in Python:

- Python plugin: tools, hooks, commands, API contracts.
- Skills: planning rules, role playbooks, editorial/procedural judgment.
- Portal: durable task state and human approval boundary.

## Safety boundary

This plugin may propose work and post portal messages. It must not call workflow approval/execution endpoints.

Human execution boundary remains in the Portal: `Prepare run` → `Approve pending`.

## Release notes

See [CHANGELOG.md](CHANGELOG.md).
