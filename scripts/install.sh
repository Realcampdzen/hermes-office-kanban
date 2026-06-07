#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-default}"
PLUGIN_NAME="hermes-office-kanban"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

resolve_hermes_home() {
  if [[ -n "${HERMES_HOME:-}" ]]; then
    printf '%s\n' "$HERMES_HOME"
    return 0
  fi

  if command_exists hermes; then
    local config_path=""
    if [[ "$PROFILE" == "default" ]]; then
      config_path="$(hermes config path 2>/dev/null || true)"
    else
      config_path="$(hermes --profile "$PROFILE" config path 2>/dev/null || true)"
    fi
    if [[ -n "$config_path" && "$config_path" == */config.yaml ]]; then
      dirname "$config_path"
      return 0
    fi
  fi

  if [[ "$PROFILE" == "default" ]]; then
    printf '%s\n' "$HOME/.hermes"
  else
    printf '%s\n' "$HOME/.hermes/profiles/$PROFILE"
  fi
}

if [[ "$PROFILE" == "default" ]]; then
  HERMES_ARGS=()
else
  HERMES_ARGS=(--profile "$PROFILE")
fi

HERMES_HOME_RESOLVED="$(resolve_hermes_home)"
PLUGIN_DIR="$HERMES_HOME_RESOLVED/plugins/$PLUGIN_NAME"
mkdir -p "$PLUGIN_DIR"

if command_exists rsync; then
  rsync -a --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    "$REPO_DIR/" "$PLUGIN_DIR/"
else
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  cp -a "$REPO_DIR/." "$tmp_dir/"
  rm -rf "$tmp_dir/.git" "$tmp_dir/__pycache__" "$tmp_dir/.pytest_cache"
  find "$tmp_dir" -name '*.pyc' -delete
  rm -rf "$PLUGIN_DIR"
  mkdir -p "$PLUGIN_DIR"
  cp -a "$tmp_dir/." "$PLUGIN_DIR/"
fi

if command_exists hermes; then
  hermes "${HERMES_ARGS[@]}" plugins enable "$PLUGIN_NAME"
else
  echo "WARNING: hermes CLI not found; copied plugin but could not enable it." >&2
fi

cat <<EOF
Installed $PLUGIN_NAME to $PLUGIN_DIR

Next steps:
  1. Ensure the target profile .env contains KANBAN_PORTAL_AGENT_TOKEN.
  2. Restart the gateway or start a new Hermes session:
     hermes ${HERMES_ARGS[*]} gateway restart
  3. Verify:
     hermes ${HERMES_ARGS[*]} plugins list
     HERMES_PROFILE=$PROFILE PYTHONPATH=/usr/local/lib/hermes-agent \\
       /usr/local/lib/hermes-agent/venv/bin/python scripts/smoke_test.py
EOF
