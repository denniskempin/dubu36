"""Allow `python -m keymap_generator`."""

from __future__ import annotations

import sys

from keymap_generator.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
