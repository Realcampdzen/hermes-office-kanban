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

Or manually:

```bash
PROFILE=neurostepa
PLUGIN_DIR="/root/.hermes/profiles/$PROFILE/plugins/hermes-office-kanban"
mkdir -p "$PLUGIN_DIR"
rsync -a --delete --exclude='.git' --exclude='__pycache__' ./ "$PLUGIN_DIR/"
hermes --profile "$PROFILE" plugins enable hermes-office-kanban
hermes --profile "$PROFILE" gateway restart
```

For default Hermes home without profiles:

```bash
./scripts/install.sh default
```

## Verify

```bash
hermes --profile neurostepa plugins list | grep hermes-office-kanban
hermes --profile neurostepa tools list | grep hermes_office_kanban

HERMES_PROFILE=neurostepa PYTHONPATH=/usr/local/lib/hermes-agent \
  /usr/local/lib/hermes-agent/venv/bin/python scripts/smoke_test.py
```

The smoke test verifies plugin discovery, tools, commands, skills, and hook rewrites.

## Development

```bash
python -m py_compile __init__.py
python scripts/smoke_test.py
```

Keep product policy in skills and mechanics in Python:

- Python plugin: tools, hooks, commands, API contracts.
- Skills: planning rules, role playbooks, editorial/procedural judgment.
- Portal: durable task state and human approval boundary.

## Safety boundary

This plugin may propose work and post portal messages. It must not call workflow approval/execution endpoints.

Human execution boundary remains in the Portal: `Prepare run` → `Approve pending`.
