"""Tests for the Selenium-style SVG diagram renderer."""

from __future__ import annotations

from pathlib import Path

from keymap_generator.parser import Key, Layer, parse_keymap
from keymap_generator.render import (
    EXCLUDED_LAYERS,
    build_stacked_specs,
    hold_flavor,
    layer_specs,
    render_board,
    render_diagrams,
    tap_display,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
KEYMAP = REPO_ROOT / "keymap.txt"


class TestTapDisplay:
    def test_glyph_for_known_tap(self) -> None:
        assert tap_display("TAB") == ("", "tab")
        assert tap_display("ALT_BKSP") == ("", "delete-word")
        assert tap_display("WORD_L") == ("", "word-left")
        assert tap_display("FWD") == ("", "hist-fwd")

    def test_symbol_aliases(self) -> None:
        assert tap_display("PIPE") == ("|", None)
        assert tap_display("UML") == ("uml", None)

    def test_plain_label_unchanged(self) -> None:
        assert tap_display("Q") == ("Q", None)
        assert tap_display("HYP_[") == ("HYP_[", None)


class TestHoldFlavor:
    def test_oneshot(self) -> None:
        assert hold_flavor(Key("SHFT", "SHFT", None)) == "oneshot"

    def test_hold_preferred(self) -> None:
        assert hold_flavor(Key("TAB", "LWR", "hp")) == "hold-preferred"

    def test_tap_preferred_explicit_and_default(self) -> None:
        assert hold_flavor(Key("A", "HYP", "tp")) == "tap-preferred"
        assert hold_flavor(Key("A", "HYP", None)) == "tap-preferred"

    def test_no_hold(self) -> None:
        assert hold_flavor(Key("Q", "", None)) is None
        assert hold_flavor(Key("Q", None, None)) is None


class TestSpecsFromKeymap:
    def test_stacked_specs_cover_all_keys(self) -> None:
        layers, _ = parse_keymap(KEYMAP)
        specs = build_stacked_specs(layers)
        assert len(specs) == 36

    def test_layer_change_holds_use_layer_accent(self) -> None:
        layers, _ = parse_keymap(KEYMAP)
        specs = build_stacked_specs(layers)
        # Left thumbs: dedicated sticky rse, shft, and lwr layer keys.
        assert specs[30]["hold"] == "RSE"
        assert specs[30]["accent"] == "nav"
        assert specs[30]["flavor"] == "sticky"
        assert specs[32]["hold"] == "LWR"
        assert specs[32]["accent"] == "sym"
        assert specs[32]["flavor"] == "sticky"
        assert specs[33]["base_glyph"] == "return"
        assert specs[34]["base_glyph"] == "space"
        assert specs[35]["hold"] == ""

    def test_plain_modifier_hold_stays_grey(self) -> None:
        layers, _ = parse_keymap(KEYMAP)
        specs = build_stacked_specs(layers)
        # Home-row R/shft.
        assert specs[11]["hold"] == "SHFT"
        assert specs[11]["accent"] == "mod"
        assert specs[11]["flavor"] == "tap-preferred"

    def test_symbol_overlay_includes_delete_word_glyph(self) -> None:
        layers, _ = parse_keymap(KEYMAP)
        specs = build_stacked_specs(layers)
        # Right-middle thumb: SPC on default, ALT_BKSP on lwr.
        assert specs[34]["base_glyph"] == "space"
        assert specs[34]["sym_glyph"] == "delete-word"

    def test_raise_layer_uses_distinct_nav_glyphs(self) -> None:
        layers, _ = parse_keymap(KEYMAP)
        rse = next(layer for layer in layers if layer.name == "rse")
        specs = layer_specs(rse)
        # Right half top row: HOME WORD_L UP WORD_R END
        assert specs[5]["base_glyph"] == "home"
        assert specs[6]["base_glyph"] == "word-left"
        assert specs[7]["base_glyph"] == "up"
        assert specs[8]["base_glyph"] == "word-right"
        assert specs[9]["base_glyph"] == "end"
        # Middle row nav: FWD LEFT DOWN RIGHT BCK
        assert specs[15]["base_glyph"] == "hist-fwd"
        assert specs[16]["base_glyph"] == "left"
        assert specs[19]["base_glyph"] == "hist-back"


class TestRenderOutput:
    def test_render_board_emits_svg(self) -> None:
        layer = Layer(
            "demo",
            [
                [Key("Q", "", None)] * 10,
                [Key("A", "SHFT", "tp")] * 10,
                [Key("Z", "", None)] * 10,
                [Key("ESC", "MOU", "hp")] * 5 + [Key("RSE", "RSE", None)],
            ],
        )
        svg = render_board(layer_specs(layer), "demo")
        assert svg.startswith("<svg")
        assert "demo" in svg
        assert 'class="hold-box tap-preferred mod"' in svg
        assert 'class="hold-box hold-preferred mod"' in svg
        assert 'class="hold-box oneshot nav"' in svg
        # One-shot keys draw only the left-bar label, not a duplicate base.
        assert svg.count(">RSE<") == 0
        assert 'class="oneshot nav"' in svg
        assert ">rse</text>" in svg

    def test_render_diagrams_writes_expected_files(self, tmp_path: Path) -> None:
        written = render_diagrams(KEYMAP, tmp_path, no_png=True)
        names = sorted(path.name for path in written)
        assert names == [
            "layer-default.svg",
            "layer-lwr.svg",
            "layer-mou.svg",
            "layer-rse.svg",
            "reference.svg",
        ]
        # Excluded layers must not appear as diagram files.
        assert frozenset({"hyp", "adj"}) == EXCLUDED_LAYERS
        assert not (tmp_path / "layer-hyp.svg").exists()
        assert not (tmp_path / "layer-adj.svg").exists()
        reference = (tmp_path / "reference.svg").read_text(encoding="utf-8")
        assert "Dubu36 reference" in reference
        assert 'class="sym"' in reference
        assert 'class="num"' in reference
