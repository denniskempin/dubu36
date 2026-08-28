"""Tests for QMK key mapping."""

from __future__ import annotations

import pytest

from keymap_generator.parser import Combo, Key, Layer
from keymap_generator.qmk import (
    generate_qmk_combo,
    generate_qmk_layer,
    get_qmk_key_press_code,
    map_key_label_to_qmk,
    map_key_to_qmk,
)


class TestQmkLabels:
    def test_letter_and_digit(self) -> None:
        assert get_qmk_key_press_code("A") == "KC_A"
        assert get_qmk_key_press_code("5") == "KC_5"

    def test_cmd_and_hyp_prefixes(self) -> None:
        assert get_qmk_key_press_code("CMD_Q") == "G(KC_Q)"
        assert get_qmk_key_press_code("HYP_LEFT") == "G(S(A(C(KC_LEFT))))"

    def test_special_and_blank(self) -> None:
        assert map_key_label_to_qmk("BT_0") == "KC_NO"
        assert map_key_label_to_qmk("") == "KC_NO"
        assert map_key_label_to_qmk("RSE") == "MO(1)"

    def test_unknown_label(self) -> None:
        with pytest.raises(KeyError, match="Cannot map label"):
            map_key_label_to_qmk("NOPE")


class TestQmkKeys:
    def test_tap_only(self) -> None:
        assert map_key_to_qmk(Key("A", "", None)) == "KC_A"

    def test_hold_only(self) -> None:
        assert map_key_to_qmk(Key("", "SHFT", None)) == "KC_LSFT"

    def test_mod_tap(self) -> None:
        assert map_key_to_qmk(Key("A", "CMD", None)) == "MT(MOD_LGUI,KC_A)"

    def test_layer_tap(self) -> None:
        assert map_key_to_qmk(Key("ESC", "MOU", "hp")) == "LT(5,KC_ESC)"

    def test_oneshot_mod(self) -> None:
        assert map_key_to_qmk(Key("SHFT", "SHFT", None)) == "OSM(MOD_LSFT)"

    def test_oneshot_layer(self) -> None:
        assert map_key_to_qmk(Key("RSE", "RSE", None)) == "OSL(1)"

    def test_unmappable_hold_tap(self) -> None:
        with pytest.raises(KeyError, match="Cannot map hold-tap"):
            map_key_to_qmk(Key("A", "NOPE", None))


class TestQmkGeneration:
    def test_combo_and_empty(self) -> None:
        assert generate_qmk_combo(None) == ("KC_NO", "KC_NO")
        assert generate_qmk_combo(Combo("Q", "W", "ESC")) == (
            "KC_Q, KC_W",
            "KC_ESC",
        )

    def test_layer(self) -> None:
        layer = Layer(
            "default",
            [
                [Key("Q", "", None), Key("W", "", None)],
                [Key("A", "CMD", None)],
            ],
        )
        assert generate_qmk_layer(layer) == "KC_Q, KC_W,\nMT(MOD_LGUI,KC_A)"
