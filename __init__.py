"""Hermes Office Kanban plugin.

Moves the Agent Command Pipeline v13 portal contract out of profile prompts and
into an installable Hermes plugin: tools, slash commands, gateway trigger
rewrites, and plugin-scoped skills.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

PLUGIN_DIR = Path(__file__).resolve().parent
PORTAL_URL = os.getenv("KANBAN_PORTAL_URL", "http://127.0.0.1:19600").rstrip("/")
AGENT_ID = os.getenv("KANBAN_PORTAL_AGENT_ID", "neurostepa")
TOKEN_ENV = "KANBAN_PORTAL_AGENT_TOKEN"
TOOLSET = "hermes_office_kanban"

PLAN_TRIGGERS = (
    "разбей цель",
    "создай план",
    "сделай план",
    "сделай карточки",
    "назначь devbro",
    "назначь dev bro",
    "назначь девбро",
    "назначь кота",
    "назначь qa",
)
STATUS_TRIGGERS = (
    "что ждет одобрения",
    "что ждёт одобрения",
    "что на проверке",
    "какие блокеры",
    "что заблокировано",
)


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _token() -> str:
    return os.getenv(TOKEN_ENV, "")


def _headers() -> Dict[str, str]:
    token = _token()
    headers = {
        "Content-Type": "application/json",
        "X-Agent-Id": AGENT_ID,
    }
    if token:
        headers["X-Agent-Token"] = token
    return headers


def _request(method: str, path: str, payload: Optional[dict] = None, timeout: int = 20) -> dict:
    if not _token():
        return {
            "success": False,
            "error": f"missing env {TOKEN_ENV}",
            "hint": "Set KANBAN_PORTAL_AGENT_TOKEN in the active Hermes profile .env and restart gateway.",
        }
    url = f"{PORTAL_URL}{path}"
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                data = {"raw": raw}
            return {"success": 200 <= resp.status < 300, "status": resp.status, "data": data}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"raw": raw}
        return {"success": False, "status": exc.code, "error": data}
    except Exception as exc:
        return {"success": False, "error": repr(exc), "url": url}


def _slug(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ]+", "-", (text or "task").lower()).strip("-")
    return (s[:max_len].strip("-") or "task")


def _now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _base_metadata(plan_id: Optional[str] = None, plan_order: Optional[int] = None) -> dict:
    meta = {
        "origin": "telegram",
        "originAgentId": AGENT_ID,
        "proposedByAgentId": AGENT_ID,
    }
    if plan_id is not None:
        meta["planId"] = plan_id
    if plan_order is not None:
        meta["planOrder"] = plan_order
    return meta


def _normalize_task(task: dict, *, plan_id: Optional[str] = None, plan_order: Optional[int] = None, parent_task_id: Optional[str] = None) -> dict:
    task = dict(task or {})
    title = str(task.get("title") or "Untitled task")
    task.setdefault("id", f"task-{AGENT_ID}-{_now_id()}-{_slug(title, 24)}")
    task.setdefault("description", "Created by hermes-office-kanban plugin.")
    task.setdefault("status", "todo")
    task.setdefault("source", "agent_captured")
    task.setdefault("workflowState", "proposed")
    task.setdefault("assignedAgentId", AGENT_ID)
    meta = dict(task.get("metadata") or {})
    base = _base_metadata(plan_id, plan_order)
    base.update(meta)
    if parent_task_id:
        base["parentTaskId"] = parent_task_id
    task["metadata"] = base
    return task


def tool_get_status(params: dict, **_: Any) -> str:
    """Read-only portal status snapshot."""
    result = _request("GET", "/api/status")
    return _json(result)


def tool_create_task(params: dict, **_: Any) -> str:
    task = params.get("task") if isinstance(params, dict) else None
    if not isinstance(task, dict):
        return _json({"success": False, "error": "Expected {task:{...}}"})
    normalized = _normalize_task(task)
    return _json(_request("POST", "/api/tasks", {"task": normalized}))


def tool_update_task(params: dict, **_: Any) -> str:
    task_id = params.get("taskId") or params.get("id")
    patch = params.get("patch") or params.get("updates")
    if not task_id or not isinstance(patch, dict):
        return _json({"success": False, "error": "Expected taskId and patch object"})
    payload = dict(patch)
    if "expectedRevision" in params and "expectedRevision" not in payload:
        payload["expectedRevision"] = params["expectedRevision"]
    return _json(_request("PATCH", f"/api/tasks/{task_id}", payload))


def tool_post_message(params: dict, **_: Any) -> str:
    payload = {
        "taskId": params.get("taskId"),
        "threadId": params.get("threadId") or (f"task:{params.get('taskId')}" if params.get("taskId") else None),
        "kind": params.get("kind", "plan"),
        "body": params.get("body") or params.get("message") or "",
        "priority": bool(params.get("priority", False)),
        "meta": params.get("meta") or {},
    }
    if not payload["body"]:
        return _json({"success": False, "error": "Expected body/message"})
    return _json(_request("POST", "/api/messages", payload))


def tool_create_plan(params: dict, **_: Any) -> str:
    """Create parent + 2-8 child proposed cards and a portal plan message.

    Expected params:
      goal/title, description, children=[{title,description,assignedAgentId}], optional planId.
    """
    goal = str(params.get("goal") or params.get("title") or "Telegram plan")
    description = str(params.get("description") or goal)
    children = params.get("children") or params.get("tasks") or []
    if not isinstance(children, list) or not (2 <= len(children) <= 8):
        return _json({"success": False, "error": "Expected children/tasks list with 2-8 items"})

    stamp = _now_id()
    plan_id = str(params.get("planId") or f"telegram-plan-{AGENT_ID}-{stamp}")
    parent_id = str(params.get("parentTaskId") or f"plan-{AGENT_ID}-{stamp}-{_slug(goal, 20)}")
    parent = _normalize_task(
        {
            "id": parent_id,
            "title": f"Plan: {goal}",
            "description": description,
            "assignedAgentId": params.get("assignedAgentId", AGENT_ID),
        },
        plan_id=plan_id,
        plan_order=0,
    )

    results: List[dict] = []
    parent_result = _request("POST", "/api/tasks", {"task": parent})
    results.append({"role": "parent", "taskId": parent_id, "result": parent_result})
    if not parent_result.get("success"):
        return _json({"success": False, "planId": plan_id, "results": results})

    for idx, child in enumerate(children, start=1):
        if not isinstance(child, dict):
            child = {"title": str(child)}
        child_title = str(child.get("title") or f"Plan task {idx}")
        child_id = str(child.get("id") or f"{parent_id}-{idx}-{_slug(child_title, 18)}")
        child_task = _normalize_task({**child, "id": child_id}, plan_id=plan_id, plan_order=idx, parent_task_id=parent_id)
        res = _request("POST", "/api/tasks", {"task": child_task})
        results.append({"role": "child", "taskId": child_id, "result": res})
        if not res.get("success"):
            return _json({"success": False, "planId": plan_id, "parentTaskId": parent_id, "results": results})

    summary = params.get("summary") or f"Created parent card and {len(children)} child cards. Waiting for portal approval."
    msg = _request("POST", "/api/messages", {
        "taskId": parent_id,
        "threadId": f"task:{parent_id}",
        "kind": "plan",
        "body": summary,
        "priority": True,
        "meta": {"planId": plan_id},
    })
    results.append({"role": "message", "result": msg})
    return _json({"success": bool(msg.get("success")), "planId": plan_id, "parentTaskId": parent_id, "results": results})


def _format_status(snapshot: dict, blockers_only: bool = False) -> str:
    if not snapshot.get("success"):
        return "Не смог прочитать статус портала: " + _json(snapshot)
    data = snapshot.get("data") or {}
    # Keep generic: portal schemas evolve. Return useful top-level fields without leaking raw walls.
    if blockers_only:
        keys = ["blockers", "blocked", "topBlockers", "blockedTasks"]
    else:
        keys = ["approval", "pendingApproval", "review", "blocked", "blockers", "plans", "topPlans", "libraryCounts", "topTasks"]
    lines = ["Статус Hermes Office:"]
    found = False
    for key in keys:
        if key in data:
            found = True
            val = data[key]
            if isinstance(val, (list, tuple)):
                lines.append(f"- {key}: {len(val)}")
                for item in list(val)[:5]:
                    if isinstance(item, dict):
                        title = item.get("title") or item.get("id") or str(item)[:80]
                        lines.append(f"  - {title}")
                    else:
                        lines.append(f"  - {str(item)[:120]}")
            elif isinstance(val, dict):
                lines.append(f"- {key}: " + ", ".join(f"{k}={v}" for k, v in list(val.items())[:8]))
            else:
                lines.append(f"- {key}: {val}")
    if not found:
        lines.append(_json(data)[:3500])
    return "\n".join(lines)


def _cmd_status(raw_args: str = "") -> str:
    return _format_status(_request("GET", "/api/status"), blockers_only=False)


def _cmd_blockers(raw_args: str = "") -> str:
    return _format_status(_request("GET", "/api/status"), blockers_only=True)


def _cmd_plan(raw_args: str = "") -> str:
    goal = (raw_args or "").strip()
    if not goal:
        return "Напиши после /plan цель. Я превращу её в proposed parent+child карточки через office_kanban_create_plan."
    return (
        "Создай Telegram-план через plugin tool `office_kanban_create_plan`. "
        "Соблюдай human approval boundary: только proposed cards, без workflow approve/run.\n\n"
        f"Цель: {goal}"
    )


def _cmd_assign(raw_args: str = "") -> str:
    return (
        "Назначение через Hermes Office Kanban: используй `office_kanban_update_task` "
        "с patch.assignedAgentId и expectedRevision, если он известен. Аргументы: "
        f"{raw_args.strip()}"
    )


def _pre_gateway_dispatch(**kwargs: Any) -> Optional[dict]:
    event = kwargs.get("event")
    text = (getattr(event, "text", "") or "").strip()
    if not text or text.startswith("/"):
        return None
    low = text.lower()
    if any(trigger in low for trigger in STATUS_TRIGGERS):
        return {
            "action": "rewrite",
            "text": (
                "Ответь по Hermes Office Portal через plugin tool `office_kanban_get_status`. "
                "Не создавай карточку для read-only статусного вопроса. Исходный вопрос пользователя:\n\n" + text
            ),
        }
    if any(trigger in low for trigger in PLAN_TRIGGERS):
        return {
            "action": "rewrite",
            "text": (
                "Используй hermes-office-kanban для Agent Command Pipeline v13: "
                "создай proposed parent+2-8 child карточки через `office_kanban_create_plan`, "
                "не запускай workflow approve/run. Исходная команда пользователя:\n\n" + text
            ),
        }
    return None


def _schema(name: str, description: str, properties: dict, required: Optional[Iterable[str]] = None) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": list(required or []),
        },
    }


def register(ctx) -> None:
    requires = [TOKEN_ENV]
    ctx.register_tool(
        "office_kanban_get_status",
        TOOLSET,
        _schema("office_kanban_get_status", "Read Hermes Office Portal status snapshot via GET /api/status.", {}),
        handler=lambda args, **kw: tool_get_status(args, **kw),
        requires_env=requires,
        description="Read Hermes Office Portal status.",
        emoji="📋",
    )
    ctx.register_tool(
        "office_kanban_create_task",
        TOOLSET,
        _schema("office_kanban_create_task", "Create one proposed Hermes Portal task. Adds Agent Command Pipeline metadata defaults.", {"task": {"type": "object"}}, ["task"]),
        handler=lambda args, **kw: tool_create_task(args, **kw),
        requires_env=requires,
        description="Create proposed portal task.",
        emoji="🧩",
    )
    ctx.register_tool(
        "office_kanban_create_plan",
        TOOLSET,
        _schema(
            "office_kanban_create_plan",
            "Create a Telegram-origin proposed plan: parent card, 2-8 child cards, and a priority plan message. Does not approve or run workflows.",
            {
                "goal": {"type": "string"},
                "description": {"type": "string"},
                "children": {"type": "array", "items": {"type": "object"}},
                "planId": {"type": "string"},
                "summary": {"type": "string"},
            },
            ["goal", "children"],
        ),
        handler=lambda args, **kw: tool_create_plan(args, **kw),
        requires_env=requires,
        description="Create proposed portal plan.",
        emoji="🗺️",
    )
    ctx.register_tool(
        "office_kanban_post_message",
        TOOLSET,
        _schema("office_kanban_post_message", "Post a message to a Hermes Portal task thread, e.g. kind=plan/blocker/review.", {"taskId": {"type": "string"}, "body": {"type": "string"}, "kind": {"type": "string"}, "meta": {"type": "object"}}, ["body"]),
        handler=lambda args, **kw: tool_post_message(args, **kw),
        requires_env=requires,
        description="Post portal task message.",
        emoji="✉️",
    )
    ctx.register_tool(
        "office_kanban_update_task",
        TOOLSET,
        _schema("office_kanban_update_task", "Patch a Hermes Portal task. Prefer expectedRevision when available.", {"taskId": {"type": "string"}, "patch": {"type": "object"}, "expectedRevision": {"type": "integer"}}, ["taskId", "patch"]),
        handler=lambda args, **kw: tool_update_task(args, **kw),
        requires_env=requires,
        description="Patch portal task.",
        emoji="🛠️",
    )

    ctx.register_command("plan", _cmd_plan, description="Create a proposed Hermes Office plan from a goal.", args_hint="<goal>")
    ctx.register_command("office-status", _cmd_status, description="Read Hermes Office portal status.")
    ctx.register_command("blockers", _cmd_blockers, description="Show Hermes Office blockers.")
    ctx.register_command("assign", _cmd_assign, description="Assign/update a portal task.", args_hint="<taskId> <agent>")
    ctx.register_hook("pre_gateway_dispatch", _pre_gateway_dispatch)

    skills_dir = PLUGIN_DIR / "skills"
    for skill_name in ("agent-command-pipeline", "kanban-orchestrator", "portal-inbox", "telegram-planning-contract"):
        path = skills_dir / skill_name / "SKILL.md"
        if path.exists():
            ctx.register_skill(skill_name, path, description=f"Hermes Office bundled skill: {skill_name}")
