#!/usr/bin/env python3
"""Smoke-test hermes-office-kanban plugin discovery and registration."""

from __future__ import annotations

from types import SimpleNamespace

from hermes_cli.plugins import discover_plugins, get_plugin_commands, get_plugin_manager, invoke_hook
from tools.registry import registry

PLUGIN = "hermes-office-kanban"
TOOLS = [
    "office_kanban_get_status",
    "office_kanban_create_task",
    "office_kanban_create_plan",
    "office_kanban_post_message",
    "office_kanban_update_task",
]
COMMANDS = ["plan", "office-status", "blockers", "assign"]
SKILLS = [
    "agent-command-pipeline",
    "kanban-orchestrator",
    "portal-inbox",
    "telegram-planning-contract",
]


def main() -> None:
    discover_plugins(force=True)
    pm = get_plugin_manager()
    loaded = pm._plugins.get(PLUGIN)
    assert loaded is not None, f"{PLUGIN} not discovered"
    assert loaded.enabled, f"{PLUGIN} not enabled: {getattr(loaded, 'error', None)}"
    assert loaded.error is None, loaded.error

    missing_tools = [name for name in TOOLS if registry.get_entry(name) is None]
    assert not missing_tools, f"missing tools: {missing_tools}"

    commands = get_plugin_commands()
    missing_commands = [name for name in COMMANDS if commands.get(name, {}).get("plugin") != PLUGIN]
    assert not missing_commands, f"missing commands: {missing_commands}"

    available_skills = pm.list_plugin_skills(PLUGIN)
    missing_skills = [name for name in SKILLS if name not in available_skills]
    assert not missing_skills, f"missing skills: {missing_skills}"

    hook_result = invoke_hook(
        "pre_gateway_dispatch",
        event=SimpleNamespace(text="разбей цель сделать тестовый проект"),
        gateway=None,
        session_store=None,
    )
    assert hook_result and hook_result[0].get("action") == "rewrite", hook_result
    assert "office_kanban_create_plan" in hook_result[0].get("text", ""), hook_result

    print("OK hermes-office-kanban plugin smoke test passed")


if __name__ == "__main__":
    main()
