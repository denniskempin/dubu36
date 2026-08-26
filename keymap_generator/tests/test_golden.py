"""Golden regression tests against committed keymap outputs."""

from __future__ import annotations

from pathlib import Path

from keymap_generator.generate import generate_keymap
from keymap_generator.parser import parse_keymap
from keymap_generator.zmk import generate_zmk_combo, generate_zmk_layer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent


def _generated_zmk() -> str:
    layers, combos = parse_keymap(REPO_ROOT / "keymap.txt")
    # The CLI prints the result, which appends a trailing newline matching
    # the committed keymap files produced by the Makefile.
    return (
        generate_keymap(
            layers,
            combos,
            PROJECT_ROOT / "zmk_template.dtsi",
            generate_zmk_layer,
            generate_zmk_combo,
        )
        + "\n"
    )


def test_zmk_output_matches_committed_shared_keymap() -> None:
    expected = (REPO_ROOT / "config" / "shared_keymap.dtsi").read_text(encoding="utf-8")
    assert _generated_zmk() == expected
