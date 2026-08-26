"""Golden regression tests against committed keymap outputs."""

from __future__ import annotations

from pathlib import Path

from keymap_generator.generate import (
    ComboGenerator,
    LayerGenerator,
    generate_keymap,
)
from keymap_generator.parser import parse_keymap
from keymap_generator.qmk import generate_qmk_combo, generate_qmk_layer
from keymap_generator.zmk import generate_zmk_combo, generate_zmk_layer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent

ZMK_KEYMAP = REPO_ROOT / "config" / "shared_keymap.dtsi"
QMK_KEYMAP = REPO_ROOT / "dubu36-ergo/qmk/dubu36ergo/keymaps/default/keymap.c"


def _generate(
    template: Path, layer_fn: LayerGenerator, combo_fn: ComboGenerator
) -> str:
    layers, combos = parse_keymap(REPO_ROOT / "keymap.txt")
    # The CLI prints the result, which appends a trailing newline matching
    # the committed keymap files produced by the Makefile.
    return generate_keymap(layers, combos, template, layer_fn, combo_fn) + "\n"


def test_zmk_output_matches_committed_shared_keymap() -> None:
    expected = ZMK_KEYMAP.read_text(encoding="utf-8")
    generated = _generate(
        PROJECT_ROOT / "zmk_template.dtsi", generate_zmk_layer, generate_zmk_combo
    )
    assert generated == expected


def test_qmk_output_matches_committed_keymap() -> None:
    expected = QMK_KEYMAP.read_text(encoding="utf-8")
    generated = _generate(
        PROJECT_ROOT / "qmk_template.c", generate_qmk_layer, generate_qmk_combo
    )
    assert generated == expected
