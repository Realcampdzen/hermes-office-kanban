---
name: portal-inbox
description: Hermes Office plugin-bundled rules for concise portal messages.
---

# Portal Inbox

Use `office_kanban_post_message` for plan summaries, blockers, review notices, and concise status updates.

Message kinds:

- `plan`: proposed plan summary, must include `meta.planId` for plans.
- `blocker`: concrete blocker with missing input/evidence.
- `review`: review request or QA result.
- `note`: neutral context update.

Keep messages short, actionable, and linked to the task/thread. Do not spam the portal with internal reasoning.
