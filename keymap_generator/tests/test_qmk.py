"""Tests for QMK key mapping."""

from __future__ import annotations

import pytest

from keymap_generator.parser import Combo, Key, Layer
from keymap_generator.qmk import (
    COMBO_SLOTS,
    apply_fn_chords,
    fn_enum_name,
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

    def test_function_key_chords(self) -> None:
        assert fn_enum_name("F18_Q") == "FN_F18_Q"
        assert fn_enum_name("F18_,") == "FN_F18_COMMA"
        assert fn_enum_name("F18_.") == "FN_F18_DOT"
        assert fn_enum_name("F18_'") == "FN_F18_SQT"
        assert fn_enum_name("F19_*") == "FN_F19_STAR"
        assert map_key_label_to_qmk("F18_Q") == "FN_F18_Q"
        assert map_key_label_to_qmk("F19_,") == "FN_F19_COMMA"
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


class TestFnChords:
    def test_enum_and_cases_follow_the_labels(self) -> None:
        layers = [
            Layer(
                "app",
                [[Key("F18_Q", "", None), Key("F19_,", "", None)]],
            )
        ]
        text = apply_fn_chords("#FN_ENUM#\n#FN_CASES#\n", layers)
        assert "FN_F18_Q," in text
        assert "FN_F19_COMMA," in text
        assert "case FN_F18_Q: fn_chord(KC_F18, KC_Q, record); return false;" in text
        assert (
            "case FN_F19_COMMA: fn_chord(KC_F19, KC_COMMA, record); return false;"
            in text
        )


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
