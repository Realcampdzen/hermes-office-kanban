# Hermes Office Kanban API Contract

`hermes-office-kanban` talks to the Hermes Kanban Portal through the agent API.
The plugin is intentionally small: it creates proposed work, posts messages, and
reads status. It does not approve, reject, or run workflow execution.

## Authentication

Every Portal request uses profile env values:

```bash
KANBAN_PORTAL_AGENT_TOKEN=***
KANBAN_PORTAL_AGENT_ID=neurostepa       # optional, default: neurostepa
KANBAN_PORTAL_URL=http://127.0.0.1:19600 # optional, default shown
```

Headers:

```http
Content-Type: application/json
X-Agent-Id: <KANBAN_PORTAL_AGENT_ID>
X-Agent-Token: <KANBAN_PORTAL_AGENT_TOKEN>
```

## Read status

Tool: `office_kanban_get_status`

```http
GET /api/status
```

Use for read-only questions such as:

- what waits for approval;
- what is on review;
- current blockers.

The plugin should not create a task for read-only status questions.

## Create one proposed task

Tool: `office_kanban_create_task`

```http
POST /api/tasks
```

Payload shape:

```json
{
  "task": {
    "id": "optional-stable-id",
    "title": "Task title",
    "description": "Task description",
    "status": "todo",
    "source": "agent_captured",
    "workflowState": "proposed",
    "assignedAgentId": "devbro",
    "metadata": {
      "origin": "telegram",
      "originAgentId": "neurostepa",
      "proposedByAgentId": "neurostepa"
    }
  }
}
```

The plugin fills missing required Agent Command Pipeline defaults.

Dry-run:

```json
{
  "task": {"title": "Check Portal"},
  "dryRun": true
}
```

Dry-run returns the normalized request and does not call the Portal.

## Create a Telegram-origin proposed plan

Tool: `office_kanban_create_plan`

Creates:

1. one parent proposed card;
2. 2-8 child proposed cards;
3. one priority `/api/messages` entry with `kind: "plan"` and `meta.planId`.

Input shape:

```json
{
  "goal": "Ship feature X",
  "description": "Optional details",
  "children": [
    {"title": "Backend", "assignedAgentId": "backend-api"},
    {"title": "Frontend", "assignedAgentId": "frontend-swe"},
    {"title": "QA", "assignedAgentId": "qa-engineer"}
  ],
  "planId": "optional-plan-id",
  "summary": "Optional plan summary",
  "dryRun": false
}
```

Each card gets:

```json
{
  "source": "agent_captured",
  "workflowState": "proposed",
  "metadata": {
    "planId": "...",
    "planOrder": 0,
    "origin": "telegram",
    "originAgentId": "neurostepa",
    "proposedByAgentId": "neurostepa"
  }
}
```

Child cards additionally get:

```json
{
  "metadata": {
    "parentTaskId": "<parent task id>"
  }
}
```

Dry-run returns all planned `POST /api/tasks` and `POST /api/messages` requests
without sending them.

## Post a task/thread message

Tool: `office_kanban_post_message`

```http
POST /api/messages
```

Payload shape:

```json
{
  "taskId": "task-id",
  "threadId": "task:task-id",
  "kind": "plan",
  "body": "Message body",
  "priority": true,
  "meta": {"planId": "telegram-plan-..."}
}
```

For plan messages, `kind: "plan"` and `meta.planId` are required by the Portal
planning contract.

## Patch a task

Tool: `office_kanban_update_task`

```http
PATCH /api/tasks/<taskId>
```

Payload shape:

```json
{
  "assignedAgentId": "devbro",
  "expectedRevision": 12
}
```

Prefer `expectedRevision` when known to avoid overwriting concurrent updates.

## Safety boundary

Allowed:

- read `/api/status`;
- create proposed cards;
- patch normal task fields such as assignment;
- post plan/blocker/review messages.

Not allowed:

- workflow approve;
- workflow run;
- workflow reject;
- deployment/merge side effects;
- raw task-store access on public `:19500`.

The human execution boundary remains the Portal UI: `Prepare run` →
`Approve pending`.
