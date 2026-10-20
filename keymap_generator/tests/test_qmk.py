"""Tests for QMK key mapping."""

from __future__ import annotations

import pytest

from keymap_generator.parser import ROW_SIZES, Combo, Key, Layer
from keymap_generator.qmk import (
    COMBO_SLOTS,
    generate_qmk_combos,
    generate_qmk_instant_holds,
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
        assert map_key_to_qmk(Key("ESC", "MOU", "hp")) == "LT(4,KC_ESC)"

    def test_instant_hold_names(self) -> None:
        assert map_key_to_qmk(Key("A", "F18", "ih")) == "IH_A_F18"
        assert map_key_to_qmk(Key("O", "F18", "ih")) == "IH_O_F18"
        assert map_key_to_qmk(Key("Z", "F19", "ih")) == "IH_Z_F19"
        assert map_key_to_qmk(Key('"', "F19", "ih")) == "IH_DOUBLE_QUOTE_F19"

    def test_instant_hold_needs_key_presses(self) -> None:
        with pytest.raises(KeyError, match="instant-hold"):
            map_key_to_qmk(Key("A", "NOPE", "ih"))

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


class TestQmkInstantHolds:
    def test_handler_releases_the_hold_before_the_tap(self) -> None:
        layer = Layer(
            "default",
            [
                [Key("A", "F18", "ih"), Key("O", "F18", "ih")],
                [Key('"', "F19", "ih")],
            ],
        )
        rendered = generate_qmk_instant_holds([layer])
        assert "IH_A_F18 = SAFE_RANGE" in rendered
        assert "IH_O_F18," in rendered
        assert "IH_DOUBLE_QUOTE_F19," in rendered
        assert "{KC_F18, KC_A, 0, false}" in rendered
        assert "{KC_F19, KC_DOUBLE_QUOTE, 0, false}" in rendered
        # A quick release lifts the function key, taps, then restores the
        # function key if another key is still holding it.
        release = rendered.index("unregister_code16(slot->hold);")
        tap = rendered.index("tap_code16(slot->tap);")
        restore = rendered.index("register_code16(slot->hold);", tap)
        assert release < tap < restore
        assert "timer_elapsed(slot->pressed_at) < TAPPING_TERM" in rendered

    def test_no_instant_holds_emits_nothing(self) -> None:
        layer = Layer("default", [[Key("A", "", None) for _ in range(ROW_SIZES[0])]])
        assert generate_qmk_instant_holds([layer]) == ""

    def test_duplicate_pair_is_rejected(self) -> None:
        layer = Layer(
            "default",
            [[Key("A", "F18", "ih"), Key("A", "F18", "ih")]],
        )
        with pytest.raises(KeyError, match="used twice"):
            generate_qmk_instant_holds([layer])


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
