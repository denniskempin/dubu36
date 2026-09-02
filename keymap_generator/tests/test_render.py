"""Tests for the Selenium-style SVG diagram renderer."""

from __future__ import annotations

from pathlib import Path

from keymap_generator.parser import (
    Combo,
    Key,
    Layer,
    find_key_position,
    parse_keymap,
)
from keymap_generator.render import (
    EXCLUDED_LAYERS,
    GLYPH_LEGEND,
    GLYPH_PATHS,
    KH,
    KW,
    LEGEND_GLYPH_STEP,
    LEGEND_ICON_COLS,
    LEGEND_WIDTH,
    RADIUS,
    TAP_GLYPHS,
    build_stacked_specs,
    combo_specs,
    grid_index,
    hold_flavor,
    layer_specs,
    ortho_positions,
    render_board,
    render_diagrams,
    render_legend,
    tap_display,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
KEYMAP = REPO_ROOT / "keymap.txt"


class TestTapDisplay:
    def test_glyph_for_known_tap(self) -> None:
        assert tap_display("TAB") == ("", "tab")
        assert tap_display("SHFT_TAB") == ("", "btab")
        assert tap_display("ALT_BKSP") == ("", "delete-word")
        assert tap_display("WORD_L") == ("", "word-left")
        assert tap_display("FWD") == ("", "hist-fwd")
        assert tap_display("TAB_L") == ("", "app-tab-prev")
        assert tap_display("TAB_R") == ("", "app-tab-next")

    def test_keyboard_tab_is_not_app_tab(self) -> None:
        assert tap_display("TAB") != tap_display("TAB_R")
        assert tap_display("SHFT_TAB") != tap_display("TAB_L")

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
        # Left inner thumb lwr/lwr (one-shot) and right inner thumb RET/rse:hp.
        assert specs[32]["hold"] == "LWR"
        assert specs[32]["accent"] == "sym"
        assert specs[32]["flavor"] == "oneshot"
        assert specs[33]["hold"] == "RSE"
        assert specs[33]["accent"] == "nav"
        assert specs[33]["flavor"] == "hold-preferred"
        # Space carries no hold at all, so nothing can shift under it.
        assert not specs[34]["hold"]

    def test_plain_modifier_hold_stays_grey(self) -> None:
        layers, _ = parse_keymap(KEYMAP)
        specs = build_stacked_specs(layers)
        # Home-row R/shft.
        assert specs[11]["hold"] == "SHFT"
        assert specs[11]["accent"] == "mod"
        assert specs[11]["flavor"] == "tap-preferred"

    def test_symbol_overlay_includes_tab_glyphs(self) -> None:
        layers, _ = parse_keymap(KEYMAP)
        specs = build_stacked_specs(layers)
        # Right thumbs: RET with SHFT_TAB on lwr, SPC with TAB on lwr.
        assert specs[33]["base_glyph"] == "return"
        assert specs[33]["sym_glyph"] == "btab"
        assert specs[34]["sym_glyph"] == "tab"
        # BKSP sits on the outer left thumb, opposite RET.
        assert specs[30]["base_glyph"] == "backspace"

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
        # Bottom row: previous/next app tab, not the Tab-key arrows.
        assert specs[25]["base_glyph"] == "app-tab-prev"
        assert specs[29]["base_glyph"] == "app-tab-next"


class TestComboMarks:
    def test_grid_index_matches_flatten_order(self) -> None:
        assert grid_index(0, 0) == 0
        assert grid_index(0, 9) == 9
        assert grid_index(2, 2) == 22
        assert grid_index(2, 3) == 23
        assert grid_index(3, 0) == 30
        assert grid_index(3, 5) == 35

    def test_esc_combo_sits_between_c_and_v(self) -> None:
        layers, combos = parse_keymap(KEYMAP)
        default = next(layer for layer in layers if layer.name == "default")
        marks = combo_specs(combos, default)
        assert len(marks) == 1
        mark = marks[0]
        assert mark["glyph"] == "escape"
        assert mark["text"] == ""
        positions = ortho_positions()
        c = positions[grid_index(*find_key_position(default, "C"))]
        v = positions[grid_index(*find_key_position(default, "V"))]
        assert mark["x"] == (c[0] + v[0] + KW) / 2
        assert mark["y"] == (c[1] + v[1] + KH) / 2

    def test_plain_label_combo_uses_text(self) -> None:
        layers, _ = parse_keymap(KEYMAP)
        default = next(layer for layer in layers if layer.name == "default")
        marks = combo_specs([Combo("Q", "W", "X")], default)
        assert marks[0]["text"] == "X"
        assert marks[0]["glyph"] is None

    def test_no_combos_renders_nothing(self) -> None:
        layers, _ = parse_keymap(KEYMAP)
        default = next(layer for layer in layers if layer.name == "default")
        assert combo_specs([], default) == []


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
        assert '<rect class="combo-badge"' not in svg

    def test_combo_mark_emits_badge_and_glyph(self) -> None:
        layer = Layer(
            "demo",
            [
                [Key("Q", "", None)] * 10,
                [Key("A", "SHFT", "tp")] * 10,
                [Key("Z", "", None)] * 10,
                [Key("ESC", "MOU", "hp")] * 5 + [Key("RSE", "RSE", None)],
            ],
        )
        svg = render_board(
            layer_specs(layer),
            "demo",
            combos=[{"x": 180.0, "y": 141.67, "text": "", "glyph": "escape"}],
        )
        assert (
            f'<rect class="combo-badge" x="-10.0" y="-9.5" '
            f'width="20.0" height="19.0" rx="{RADIUS}" ry="{RADIUS}"/>'
        ) in svg
        assert 'class="glyph combo"' in svg
        assert 'href="#glyph_escape"' in svg
        assert "translate(180.00,141.67)" in svg

    def test_combo_mark_falls_back_to_text(self) -> None:
        layer = Layer(
            "demo",
            [
                [Key("Q", "", None)] * 10,
                [Key("A", "", None)] * 10,
                [Key("Z", "", None)] * 10,
                [Key("SPC", "", None)] * 6,
            ],
        )
        svg = render_board(
            layer_specs(layer),
            "demo",
            combos=[{"x": 60.0, "y": 28.0, "text": "X", "glyph": None}],
        )
        assert '<rect class="combo-badge"' in svg
        assert ">X</text>" in svg

    def test_render_diagrams_writes_expected_files(self, tmp_path: Path) -> None:
        written = render_diagrams(KEYMAP, tmp_path, no_png=True)
        names = sorted(path.name for path in written)
        assert names == [
            "layer-default.svg",
            "layer-lwr.svg",
            "layer-mou.svg",
            "layer-rse.svg",
            "legend.svg",
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
        assert '<rect class="combo-badge"' in reference
        assert 'class="glyph combo"' in reference
        default_layer = (tmp_path / "layer-default.svg").read_text(encoding="utf-8")
        assert '<rect class="combo-badge"' not in default_layer
        legend = (tmp_path / "legend.svg").read_text(encoding="utf-8")
        assert legend == render_legend()


class TestRenderLegend:
    def test_glyph_legend_covers_every_icon(self) -> None:
        names = {name for glyphs, _ in GLYPH_LEGEND for name in glyphs}
        assert names == set(GLYPH_PATHS)
        assert set(TAP_GLYPHS.values()) <= set(GLYPH_PATHS)

    def test_legend_svg_covers_corners_flavors_and_icons(self) -> None:
        svg = render_legend()
        assert svg.startswith("<svg")
        assert ">Legend</text>" in svg
        assert ">Corners</text>" in svg
        assert ">base tap</text>" in svg
        assert ">hold</text>" in svg
        assert ">symbols (lwr)</text>" in svg
        assert ">numbers / nav (rse)</text>" in svg
        assert ">Hold flavors</text>" in svg
        assert ">tap-preferred</text>" in svg
        assert ">hold-preferred</text>" in svg
        assert ">one-shot</text>" in svg
        assert 'class="hold-box tap-preferred mod"' in svg
        assert 'class="hold-box hold-preferred nav"' in svg
        assert 'class="hold-box oneshot sym"' in svg
        assert ">Icons</text>" in svg
        for names, label in GLYPH_LEGEND:
            for name in names:
                assert f'href="#glyph_{name}"' in svg
            assert f">{label}</text>" in svg
        # Directional pairs share a label instead of listing each way.
        assert ">arrows</text>" in svg
        assert ">home / end</text>" in svg
        assert ">word</text>" in svg
        assert ">history</text>" in svg
        assert ">app tab</text>" in svg
        assert ">shift-tab</text>" not in svg
        assert ">word left</text>" not in svg
        assert ">history back</text>" not in svg
        assert ">Combos</text>" in svg
        assert ">combo</text>" in svg
        assert ">two-key chord</text>" in svg
        assert '<rect class="combo-badge"' in svg
        assert 'class="glyph combo"' in svg
        assert svg.index(">Combos</text>") < svg.index(">Icons</text>")

    def test_legend_icons_sit_on_a_column_grid(self) -> None:
        svg = render_legend()
        col_w = LEGEND_WIDTH / LEGEND_ICON_COLS
        for i, (names, _label) in enumerate(GLYPH_LEGEND):
            col = i % LEGEND_ICON_COLS
            group_w = (len(names) - 1) * LEGEND_GLYPH_STEP
            first_x = col * col_w + col_w / 2 - group_w / 2
            assert f'href="#glyph_{names[0]}" x="{first_x:.1f}"' in svg
