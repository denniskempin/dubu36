"""Tests for template filling."""

from __future__ import annotations

from pathlib import Path

from keymap_generator.generate import HEADER, generate_keymap
from keymap_generator.parser import Combo, Key, Layer


def test_generate_keymap_substitutes_placeholders(tmp_path: Path) -> None:
    template = tmp_path / "template.txt"
    template.write_text("L0=#LAYER_0#\nL1=#LAYER_1#\nC=#COMBOS#\n")
    layers = [
        Layer("default", [[Key("Q", "", None)]]),
        Layer("rse", [[Key("A", "", None)]]),
    ]
    combos = [Combo("Q", "W", "ESC")]

    def layer_fn(layer: Layer) -> str:
        return layer.name.upper()

    def combos_fn(rendered: list[Combo], default_layer: Layer) -> str:
        return f"{default_layer.name}:" + ",".join(
            f"{c.a}+{c.b}={c.result}" for c in rendered
        )

    result = generate_keymap(layers, combos, template, layer_fn, combos_fn)
    assert result.startswith(HEADER)
    assert "L0=DEFAULT" in result
    assert "L1=RSE" in result
    # The combo generator is handed the default layer to resolve labels against.
    assert "C=default:Q+W=ESC" in result
