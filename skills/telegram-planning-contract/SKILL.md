---
name: telegram-planning-contract
description: Hermes Office plugin-bundled Telegram trigger and safety contract.
---

# Telegram Planning Contract

Trigger planning when the owner says variants of:

- `разбей цель`
- `создай план`
- `сделай карточки`
- `назначь DevBro`
- `назначь Кота`
- `назначь QA`

For status questions like `что ждёт одобрения`, `что на проверке`, `какие блокеры`, use `office_kanban_get_status`; do not create a task just to answer.

Safety boundary:

- Planning creates proposed cards only.
- No direct delegation for execution.
- No `workflow approve/run/reject/on/off`.
- Human starts execution in the portal.
