"""Command-line entry point for the keymap generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from keymap_generator.generate import generate_keymap
from keymap_generator.parser import parse_keymap
from keymap_generator.qmk import generate_qmk_combo, generate_qmk_layer
from keymap_generator.zmk import generate_zmk_combo, generate_zmk_layer

# cli.py -> keymap_generator -> src -> keymap_generator/ (project root)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _PROJECT_ROOT.parent

DEFAULT_KEYMAP = _REPO_ROOT / "keymap.txt"
DEFAULT_QMK_TEMPLATE = _PROJECT_ROOT / "qmk_template.c"
DEFAULT_ZMK_TEMPLATE = _PROJECT_ROOT / "zmk_template.dtsi"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate-keymap",
        description="Generate a QMK or ZMK keymap from keymap.txt.",
    )
    parser.add_argument(
        "firmware",
        choices=("qmk", "zmk"),
        help="Target firmware to generate a keymap for.",
    )
    parser.add_argument(
        "--keymap",
        type=Path,
        default=DEFAULT_KEYMAP,
        help="Path to the keymap grid (default: ../keymap.txt).",
    )
    parser.add_argument(
        "--qmk-template",
        type=Path,
        default=DEFAULT_QMK_TEMPLATE,
        help="QMK template path (default: qmk_template.c).",
    )
    parser.add_argument(
        "--zmk-template",
        type=Path,
        default=DEFAULT_ZMK_TEMPLATE,
        help="ZMK template path (default: zmk_template.dtsi).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    layers, combos = parse_keymap(args.keymap)
    if args.firmware == "zmk":
        template, layer_fn, combo_fn = (
            args.zmk_template,
            generate_zmk_layer,
            generate_zmk_combo,
        )
    else:
        template, layer_fn, combo_fn = (
            args.qmk_template,
            generate_qmk_layer,
            generate_qmk_combo,
        )
    print(generate_keymap(layers, combos, template, layer_fn, combo_fn))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
