#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the ZMK Dev Container image.
set -euo pipefail

export WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"
cd "$WORKSPACE_DIR"

# A west workspace at the repo root cannot build this firmware: the root is
# passed as ZMK_EXTRA_MODULES, and Zephyr then recursively sources Kconfig.
# Clear a leftover from an older bootstrap, then let make use .zmk-workspace/.
if [ -d .west ]; then
  rm -rf .west zmk modules tools
  find zephyr -mindepth 1 -maxdepth 1 -not -name module.yml -exec rm -rf {} +
fi
unset ZEPHYR_BASE

make setup

# diagrams group: make diagrams (via make all) and ty's cairosvg import.
# cairosvg also dlopens libcairo, which the firmware image does not ship.
if ! ldconfig -p 2>/dev/null | grep -q 'libcairo.so.2'; then
  apt-get update
  apt-get install -y --no-install-recommends libcairo2
  rm -rf /var/lib/apt/lists/*
fi
uv sync --directory keymap_generator --locked --group diagrams
