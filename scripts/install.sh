#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-default}"
PLUGIN_NAME="hermes-office-kanban"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ "$PROFILE" == "default" ]]; then
  HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
  HERMES_ARGS=()
else
  HERMES_HOME="${HERMES_HOME:-$HOME/.hermes/profiles/$PROFILE}"
  HERMES_ARGS=(--profile "$PROFILE")
fi

PLUGIN_DIR="$HERMES_HOME/plugins/$PLUGIN_NAME"
mkdir -p "$PLUGIN_DIR"

rsync -a --delete \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='*.pyc' \
  "$REPO_DIR/" "$PLUGIN_DIR/"

hermes "${HERMES_ARGS[@]}" plugins enable "$PLUGIN_NAME"

echo "Installed $PLUGIN_NAME to $PLUGIN_DIR"
echo "Restart the Hermes gateway or start a new session to load the plugin."
