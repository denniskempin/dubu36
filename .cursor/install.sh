#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the ZMK Dev Container image.
set -euo pipefail

export WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"
cd "$WORKSPACE_DIR"

# Earlier revisions of this script ran `west init -l config` here at the repo
# root. That layout cannot build the firmware: the repo root is passed to ZMK as
# an extra Zephyr module, so Zephyr resolves its Kconfig to the checked-out
# tree's own zephyr/Kconfig and dies with a recursive source of Kconfig.zephyr.
# Clear a root workspace left over from that, then let make build the isolated
# one under .zmk-workspace.
if [ -d .west ]; then
  rm -rf .west zmk modules tools
  find zephyr -mindepth 1 -maxdepth 1 -not -name module.yml -exec rm -rf {} +
fi
unset ZEPHYR_BASE

make setup

# The diagrams group is needed by `make diagrams`, which `make all` depends on,
# and by `ty` to resolve the cairosvg import in render.py. cairosvg also needs
# the system cairo library, which the firmware image does not ship.
if ! ldconfig -p 2>/dev/null | grep -q 'libcairo.so.2'; then
  apt-get update
  apt-get install -y --no-install-recommends libcairo2
  rm -rf /var/lib/apt/lists/*
fi
uv sync --directory keymap_generator --locked --group diagrams
