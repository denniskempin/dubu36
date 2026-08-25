"""Tests for template filling."""

from __future__ import annotations

from pathlib import Path

from keymap_generator.generate import HEADER, generate_keymap
from keymap_generator.parser import Combo, Key, Layer


def test_generate_keymap_substitutes_placeholders(tmp_path: Path) -> None:
    template = tmp_path / "template.txt"
    template.write_text(
        "L0=#LAYER_0#\n"
        "L1=#LAYER_1#\n"
        "T0=#COMBO_TRIGGER_0# R0=#COMBO_RESULT_0#\n"
        "T1=#COMBO_TRIGGER_1# R1=#COMBO_RESULT_1#\n"
    )
    layers = [
        Layer("default", [[Key("Q", "", None)]]),
        Layer("rse", [[Key("A", "", None)]]),
    ]
    combos = [Combo("Q", "W", "ESC")]

    def layer_fn(layer: Layer) -> str:
        return layer.name.upper()

    def combo_fn(combo: Combo | None) -> tuple[str, str]:
        if combo is None:
            return ("NONE", "NONE")
        return (f"{combo.a}+{combo.b}", combo.result)

    result = generate_keymap(layers, combos, template, layer_fn, combo_fn)
    assert result.startswith(HEADER)
    assert "L0=DEFAULT" in result
    assert "L1=RSE" in result
    assert "T0=Q+W R0=ESC" in result
    assert "T1=NONE R1=NONE" in result
