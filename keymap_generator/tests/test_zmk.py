"""Tests for ZMK key mapping."""

from __future__ import annotations

import pytest

from keymap_generator.parser import ROW_SIZES, Combo, Key, Layer
from keymap_generator.zmk import (
    COMBO_PRIOR_IDLE_MS,
    COMBO_TIMEOUT_MS,
    generate_zmk_combos,
    generate_zmk_layer,
    get_zmk_key_press_code,
    map_key_label_to_zmk,
    map_key_to_zmk,
    zmk_key_position,
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


# Enough distinct one character labels to give all 36 keys their own, so a
# position can be traced back to exactly one key.
GRID_LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def grid_layer() -> Layer:
    """A layer whose keys each tap a distinct label, to pin down positions."""
    labels = iter(GRID_LABELS)
    return Layer(
        "default",
        [[Key(next(labels), "", None) for _ in range(width)] for width in ROW_SIZES],
    )


def binding_at(layer: Layer, position: int) -> str:
    """The rendered binding ZMK would find at `position` of `layer`."""
    rendered = generate_zmk_layer(layer).replace("\n", " ")
    return "&" + rendered.split("&")[position + 1].strip()


class TestZmkKeyPositions:
    def test_main_rows_skip_the_padding(self) -> None:
        # Each row of ten gains a &trans at both ends, so row N starts at 12N+1.
        assert zmk_key_position(0, 0) == 1
        assert zmk_key_position(0, 9) == 10
        assert zmk_key_position(1, 0) == 13
        assert zmk_key_position(2, 9) == 34

    def test_thumbs_follow_all_three_padded_rows(self) -> None:
        assert zmk_key_position(3, 0) == 36
        assert zmk_key_position(3, 5) == 41

    def test_positions_match_the_generated_bindings(self) -> None:
        layer = grid_layer()
        for y, row in enumerate(layer.rows):
            for x, key in enumerate(row):
                position = zmk_key_position(y, x)
                assert binding_at(layer, position) == map_key_label_to_zmk(key.tap)


class TestZmkCombos:
    # Row 1 of GRID_LABELS is "KLMNOPQRST", so M and N sit in columns 2 and 3.
    esc_combo = Combo("M", "N", "ESC")

    def test_no_combos_renders_nothing(self) -> None:
        assert generate_zmk_combos([], grid_layer()) == ""

    def test_combo_uses_padded_key_positions(self) -> None:
        rendered = generate_zmk_combos([self.esc_combo], grid_layer())
        assert 'compatible = "zmk,combos";' in rendered
        assert "key-positions = <15 16>;" in rendered
        assert "bindings = <&kp ESC>;" in rendered

    def test_combo_is_guarded_and_base_layer_only(self) -> None:
        rendered = generate_zmk_combos([self.esc_combo], grid_layer())
        assert f"timeout-ms = <{COMBO_TIMEOUT_MS}>;" in rendered
        assert f"require-prior-idle-ms = <{COMBO_PRIOR_IDLE_MS}>;" in rendered
        assert "layers = <0>;" in rendered

    def test_each_combo_gets_its_own_node(self) -> None:
        combos = [self.esc_combo, Combo("U", "V", "TAB")]
        rendered = generate_zmk_combos(combos, grid_layer())
        assert "combo_0 {" in rendered
        assert "combo_1 {" in rendered

    def test_unknown_trigger_label(self) -> None:
        with pytest.raises(KeyError, match="taps NOPE"):
            generate_zmk_combos([Combo("NOPE", "N", "ESC")], grid_layer())


class TestZmkGeneration:
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
