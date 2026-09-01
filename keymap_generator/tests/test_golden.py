"""Golden regression tests against committed keymap outputs."""

from __future__ import annotations

from pathlib import Path

from keymap_generator.generate import (
    CombosGenerator,
    LayerGenerator,
    generate_keymap,
)
from keymap_generator.parser import parse_keymap
from keymap_generator.qmk import generate_qmk_combos, generate_qmk_layer
from keymap_generator.render import render_diagrams
from keymap_generator.zmk import generate_zmk_combos, generate_zmk_layer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent

ZMK_KEYMAP = REPO_ROOT / "config" / "shared_keymap.dtsi"
QMK_KEYMAP = REPO_ROOT / "dubu36-ergo/qmk/dubu36ergo/keymaps/default/keymap.c"
DIAGRAMS = REPO_ROOT / "diagrams"


def _generate(
    template: Path, layer_fn: LayerGenerator, combos_fn: CombosGenerator
) -> str:
    layers, combos = parse_keymap(REPO_ROOT / "keymap.txt")
    # The CLI prints the result, which appends a trailing newline matching
    # the committed keymap files produced by the Makefile.
    return generate_keymap(layers, combos, template, layer_fn, combos_fn) + "\n"


def test_zmk_output_matches_committed_shared_keymap() -> None:
    expected = ZMK_KEYMAP.read_text(encoding="utf-8")
    generated = _generate(
        PROJECT_ROOT / "zmk_template.dtsi", generate_zmk_layer, generate_zmk_combos
    )
    assert generated == expected


def test_qmk_output_matches_committed_keymap() -> None:
    expected = QMK_KEYMAP.read_text(encoding="utf-8")
    generated = _generate(
        PROJECT_ROOT / "qmk_template.c", generate_qmk_layer, generate_qmk_combos
    )
    assert generated == expected


def test_diagram_svgs_match_committed_diagrams(tmp_path: Path) -> None:
    # Only the SVGs are compared: PNG bytes depend on the cairo version, so
    # they would make this test fail for reasons unrelated to the keymap.
    written = render_diagrams(REPO_ROOT / "keymap.txt", tmp_path, no_png=True)
    assert written, "the renderer wrote no diagrams"
    for generated in written:
        committed = DIAGRAMS / generated.name
        assert committed.exists(), f"{generated.name} is not committed under diagrams/"
        assert generated.read_text(encoding="utf-8") == committed.read_text(
            encoding="utf-8"
        )
