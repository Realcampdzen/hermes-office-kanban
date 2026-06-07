---
name: agent-command-pipeline
description: Hermes Office plugin-bundled Agent Command Pipeline v13 contract for proposed portal plans.
---

# Agent Command Pipeline v13

Use `office_kanban_create_plan` for Telegram planning triggers: `разбей цель`, `создай план`, `назначь DevBro`, `сделай карточки`.

Rules:

- Create one parent card and 2-8 child cards.
- All cards use `source: agent_captured`, `workflowState: proposed`.
- Metadata must include `planId`, `planOrder`, `origin: telegram`, `originAgentId`, `proposedByAgentId`.
- Child metadata must include `parentTaskId`.
- After task creation, post one `kind: plan` message with `priority: true` and `meta.planId`.
- Never run/approve/reject workflows. Human approves in Portal.

Use `office_kanban_get_status` for read-only questions about approvals, review, blockers, and status.
