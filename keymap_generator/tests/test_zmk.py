"""Tests for ZMK key mapping."""

from __future__ import annotations

import pytest

from keymap_generator.parser import Combo, Key, Layer
from keymap_generator.zmk import (
    generate_zmk_combo,
    generate_zmk_layer,
    get_zmk_key_press_code,
    map_key_label_to_zmk,
    map_key_to_zmk,
)


class TestZmkLabels:
    def test_letter_and_digit(self) -> None:
        assert get_zmk_key_press_code("A") == "A"
        assert get_zmk_key_press_code("5") == "N5"

    def test_mod_prefixes(self) -> None:
        assert get_zmk_key_press_code("SHFT_TAB") == "LS(TAB)"
        assert get_zmk_key_press_code("CMD_Q") == "LG(Q)"
        assert get_zmk_key_press_code("HYP_LEFT") == "LA(LS(LC(LG(LEFT))))"

    def test_special_and_blank(self) -> None:
        assert map_key_label_to_zmk("BT_0") == "&bt BT_SEL 0"
        assert map_key_label_to_zmk("") == "&trans"
        assert map_key_label_to_zmk("RSE") == "&mo 1"

    def test_unknown_label(self) -> None:
        with pytest.raises(KeyError, match="Cannot map label"):
            map_key_label_to_zmk("NOPE")


class TestZmkKeys:
    def test_tap_only(self) -> None:
        assert map_key_to_zmk(Key("A", "", None)) == "&kp A"

    def test_hold_only(self) -> None:
        assert map_key_to_zmk(Key("", "SHFT", None)) == "&kp LSHFT"

    def test_mod_tap_default_flavor(self) -> None:
        assert map_key_to_zmk(Key("A", "CMD", None)) == "&mt_tp LGUI A"

    def test_layer_tap_hold_preferred(self) -> None:
        assert map_key_to_zmk(Key("ESC", "MOU", "hp")) == "&lt_hp 5 ESC"

    def test_oneshot_mod(self) -> None:
        assert map_key_to_zmk(Key("SHFT", "SHFT", None)) == "&omt_ LSHFT LSHFT"

    def test_oneshot_layer(self) -> None:
        assert map_key_to_zmk(Key("RSE", "RSE", None)) == "&olt_ 1 1"

    def test_unmappable_hold_tap(self) -> None:
        with pytest.raises(KeyError, match="Cannot map hold-tap"):
            map_key_to_zmk(Key("A", "NOPE", None))


class TestZmkGeneration:
    def test_combo_stub(self) -> None:
        assert generate_zmk_combo(None) == ("0 0", "&trans")
        assert generate_zmk_combo(Combo("Q", "W", "ESC")) == ("0 0", "&trans")

    def test_layer_padding(self) -> None:
        layer = Layer(
            "default",
            [
                [Key("Q", "", None)] * 10,
                [Key("A", "", None)] * 10,
                [Key("Z", "", None)] * 10,
                [Key("ESC", "", None)] * 6,
            ],
        )
        rendered = generate_zmk_layer(layer)
        lines = rendered.splitlines()
        assert lines[0].startswith("&trans &kp Q")
        assert lines[0].endswith("&kp Q &trans")
        assert lines[3] == " ".join(["&kp ESC"] * 6)
