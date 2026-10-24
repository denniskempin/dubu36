"""Tests for QMK key mapping."""

from __future__ import annotations

import pytest

from keymap_generator.parser import Combo, Key, Layer
from keymap_generator.qmk import (
    COMBO_SLOTS,
    apply_layer_mods,
    generate_qmk_combos,
    generate_qmk_layer,
    get_qmk_key_press_code,
    map_key_label_to_qmk,
    map_key_to_qmk,
)


class TestQmkLabels:
    def test_letter_and_digit(self) -> None:
        assert get_qmk_key_press_code("A") == "KC_A"
        assert get_qmk_key_press_code("5") == "KC_5"

    def test_mod_prefixes(self) -> None:
        assert get_qmk_key_press_code("SHFT_TAB") == "S(KC_TAB)"
        assert get_qmk_key_press_code("CMD_Q") == "G(KC_Q)"
        assert get_qmk_key_press_code("HYP_LEFT") == "G(S(A(C(KC_LEFT))))"

    def test_function_and_layer_holds(self) -> None:
        assert map_key_label_to_qmk("FN") == "APPLE_FN"
        assert map_key_to_qmk(Key("X", "FN", None)) == "LT(0,KC_X)"
        assert map_key_to_qmk(Key(".", "FN", None)) == "LT(0,KC_DOT)"
        assert map_key_to_qmk(Key("C", "APP", None)) == "LT(6,KC_C)"
        assert map_key_to_qmk(Key("V", "OS", None)) == "LT(7,KC_V)"

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


def combo_layer() -> Layer:
    """A default layer with a plain key pair and a home-row mod-tap pair."""
    return Layer(
        "default",
        [
            [Key("Q", "", None), Key("W", "", None)],
            [Key("S", "ALT", None), Key("T", "CMD", None)],
        ],
    )


class TestQmkCombos:
    def test_plain_keys(self) -> None:
        rendered = generate_qmk_combos([Combo("Q", "W", "ESC")], combo_layer())
        assert "combo0[] = {KC_Q, KC_W, COMBO_END};" in rendered
        assert "COMBO(combo0, KC_ESC)" in rendered

    def test_home_row_trigger_keeps_the_mod_tap(self) -> None:
        # QMK matches the keycode the keymap holds, so a bare KC_S would never
        # match the MT() the home row actually contains.
        rendered = generate_qmk_combos([Combo("S", "T", "ESC")], combo_layer())
        assert (
            "combo0[] = {MT(MOD_LALT,KC_S), MT(MOD_LGUI,KC_T), COMBO_END};" in rendered
        )

    def test_spare_slots_cannot_fire(self) -> None:
        rendered = generate_qmk_combos([Combo("Q", "W", "ESC")], combo_layer())
        assert rendered.count("KC_NO, COMBO_END") == COMBO_SLOTS - 1
        assert rendered.count("COMBO(") == COMBO_SLOTS

    def test_no_combos_still_fills_every_slot(self) -> None:
        rendered = generate_qmk_combos([], combo_layer())
        assert rendered.count("KC_NO, COMBO_END") == COMBO_SLOTS

    def test_unknown_trigger_label(self) -> None:
        with pytest.raises(KeyError, match="taps NOPE"):
            generate_qmk_combos([Combo("NOPE", "W", "ESC")], combo_layer())


class TestLayerMods:
    def test_hold_registers_the_layers_modifier(self) -> None:
        layers = [
            Layer("default", []),
            Layer("app", [], "RGUI"),
            Layer("os", [], "RALT"),
        ]
        text = apply_layer_mods("#LAYER_MODS#", layers)
        assert "static uint8_t holds_rgui;" in text
        assert "static uint8_t holds_ralt;" in text
        assert "case 1:" in text
        assert "counted_mod(&holds_rgui, MOD_RGUI, record->event.pressed);" in text
        assert "counted_mod(&holds_ralt, MOD_RALT, record->event.pressed);" in text


class TestQmkGeneration:
    def test_layer(self) -> None:
        layer = Layer(
            "default",
            [
                [Key("Q", "", None), Key("W", "", None)],
                [Key("A", "CMD", None)],
            ],
        )
        assert generate_qmk_layer(layer) == "KC_Q, KC_W,\nMT(MOD_LGUI,KC_A)"
