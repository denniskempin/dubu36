#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the ZMK Dev Container image.
set -euo pipefail

export WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"
cd "$WORKSPACE_DIR"

if [ ! -d .west ]; then
  west init -l config
fi
west update
west zephyr-export

if [ -f "$WORKSPACE_DIR/zephyr/zephyr-env.sh" ]; then
  # shellcheck disable=SC1091
  source "$WORKSPACE_DIR/zephyr/zephyr-env.sh"
fi

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

uv sync --directory keymap_generator --locked
