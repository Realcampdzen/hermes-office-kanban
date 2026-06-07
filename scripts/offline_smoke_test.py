#!/usr/bin/env python3
"""Offline smoke test for CI.

This does not require Hermes Agent or a live Kanban Portal. It imports the plugin,
registers it against a tiny fake context, and verifies dry-run payloads and hook
rewrites.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


class FakeCtx:
    def __init__(self) -> None:
        self.tools: dict[str, dict] = {}
        self.commands: dict[str, dict] = {}
        self.hooks: dict[str, object] = {}
        self.skills: dict[str, Path] = {}

    def register_tool(self, name, toolset, schema, **kwargs):
        self.tools[name] = {"toolset": toolset, "schema": schema, **kwargs}

    def register_command(self, name, handler, **kwargs):
        self.commands[name] = {"handler": handler, **kwargs}

    def register_hook(self, name, handler):
        self.hooks[name] = handler

    def register_skill(self, name, path, **kwargs):
        self.skills[name] = Path(path)


def load_plugin():
    spec = importlib.util.spec_from_file_location("hermes_office_kanban", ROOT / "__init__.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    plugin = load_plugin()
    ctx = FakeCtx()
    plugin.register(ctx)

    expected_tools = {
        "office_kanban_get_status",
        "office_kanban_create_task",
        "office_kanban_create_plan",
        "office_kanban_post_message",
        "office_kanban_update_task",
    }
    expected_commands = {"plan", "office-status", "blockers", "assign"}
    expected_skills = {
        "agent-command-pipeline",
        "kanban-orchestrator",
        "portal-inbox",
        "telegram-planning-contract",
    }

    assert expected_tools <= set(ctx.tools), sorted(expected_tools - set(ctx.tools))
    assert expected_commands <= set(ctx.commands), sorted(expected_commands - set(ctx.commands))
    assert expected_skills <= set(ctx.skills), sorted(expected_skills - set(ctx.skills))
    assert "pre_gateway_dispatch" in ctx.hooks

    plan_raw = plugin.tool_create_plan({
        "goal": "CI dry run",
        "children": [
            {"title": "Backend", "assignedAgentId": "backend-api"},
            {"title": "QA", "assignedAgentId": "qa-engineer"},
        ],
        "dryRun": True,
    })
    plan = json.loads(plan_raw)
    assert plan["success"] is True and plan["dryRun"] is True
    assert len(plan["requests"]) == 4
    assert plan["requests"][0]["payload"]["task"]["workflowState"] == "proposed"
    assert plan["requests"][-1]["path"] == "/api/messages"
    assert plan["requests"][-1]["payload"]["kind"] == "plan"

    hook = ctx.hooks["pre_gateway_dispatch"](event=SimpleNamespace(text="разбей цель тест"))
    assert hook and hook["action"] == "rewrite"
    assert "office_kanban_create_plan" in hook["text"]

    print("OK offline smoke test passed")


if __name__ == "__main__":
    main()
