"""Tests for the Selenium-style SVG diagram renderer."""

from __future__ import annotations

import textwrap
from pathlib import Path

from keymap_generator.parser import Combo, Key, KeymapParser, Layer
from keymap_generator.render import (
    DEJAVU_FALLBACK_CHARS,
    EXCLUDED_LAYERS,
    FONT_SIZE_BASE,
    FONT_SIZE_COMBO,
    FONT_SIZE_HOLD_SYMBOL,
    FONT_SIZE_NUM,
    FONT_SIZE_SYM,
    GLYPH_EM,
    GLYPH_LEGEND,
    GLYPH_PATHS,
    GLYPH_SCALE,
    HOLD_GLYPHS,
    KH,
    KW,
    LEGEND_GLYPH_STEP,
    LEGEND_ICON_COLS,
    LEGEND_WIDTH,
    PAD,
    RADIUS,
    TAP_GLYPHS,
    TEXT_LEGEND,
    build_stacked_specs,
    combo_specs,
    dejavu_class,
    grid_index,
    hold_box_rect,
    hold_display,
    hold_flavor,
    layer_specs,
    ortho_positions,
    render_board,
    render_diagrams,
    render_legend,
    tap_display,
    use_glyph,
)


def sample_keymap() -> str:
    """A board used to exercise the renderer.

    Nothing here is the real keymap. Tests that need a grid build this, so
    editing keymap.txt does not move assertions around.
    """
    return textwrap.dedent(
        """\
        layer default
          Q W F/hyp P/cmd G/alt   J/ctrl L/adj _ _ _
          A/shft _ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
              BKSP SHFT/SHFT LWR/LWR   RSE/RSE SPC _
        layer rse
          _ 7 _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
              ESC _ RET   _ _ _
        layer lwr
          _ ^ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
              _ _ _   SHFT_TAB TAB _
        layer hyp
          _ _ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
              _ _ _   _ _ _
        layer adj
          _ _ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
              _ _ _   _ _ _
        layer mou
          _ _ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
              _ _ _   _ _ _
        combos
          Q W -> RET
        """
    )


def sample_layers() -> tuple[list[Layer], list[Combo]]:
    return KeymapParser("fixture").parse(sample_keymap().splitlines(keepends=True))


class TestTapDisplay:
    def test_glyph_for_known_tap(self) -> None:
        assert tap_display("TAB") == ("", "tab")
        assert tap_display("SHFT_TAB") == ("", "btab")
        assert tap_display("ALT_BKSP") == ("", "delete-word")
        assert tap_display("WORD_L") == ("", "word-left")
        assert tap_display("FWD") == ("", "hist-fwd")
        assert tap_display("TAB_L") == ("", "app-tab-prev")
        assert tap_display("TAB_R") == ("", "app-tab-next")
        assert tap_display("LWR") == ("⇊", None)
        assert tap_display("RSE") == ("⇈", None)
        assert tap_display("SHFT") == ("⇧", None)
        assert tap_display("CMD") == ("⌘", None)
        assert tap_display("ALT") == ("⌥", None)
        assert tap_display("CTRL") == ("⌃", None)
        assert tap_display("HYP") == ("✦", None)

    def test_keyboard_tab_is_not_app_tab(self) -> None:
        assert tap_display("TAB") != tap_display("TAB_R")
        assert tap_display("SHFT_TAB") != tap_display("TAB_L")

    def test_symbol_aliases(self) -> None:
        assert tap_display("PIPE") == ("|", None)
        assert tap_display("UML") == ("uml", None)

    def test_plain_label_unchanged(self) -> None:
        assert tap_display("Q") == ("Q", None)
        assert tap_display("HYP_[") == ("HYP_[", None)


class TestHoldDisplay:
    def test_layer_holds_use_unicode(self) -> None:
        assert hold_display("LWR") == ("⇊", None)
        assert hold_display("RSE") == ("⇈", None)
        assert "LWR" not in HOLD_GLYPHS
        assert "RSE" not in HOLD_GLYPHS

    def test_modifier_holds_use_unicode(self) -> None:
        assert hold_display("SHFT") == ("⇧", None)
        assert hold_display("CMD") == ("⌘", None)
        assert hold_display("ALT") == ("⌥", None)
        assert hold_display("CTRL") == ("⌃", None)
        assert not {"SHFT", "CMD", "ALT", "CTRL"} & HOLD_GLYPHS.keys()

    def test_hyper_hold_uses_star(self) -> None:
        assert hold_display("HYP") == ("✦", None)

    def test_adjust_hold_uses_bluetooth_glyph(self) -> None:
        assert hold_display("ADJ") == ("", "bluetooth")

    def test_other_holds_stay_text(self) -> None:
        assert hold_display("MOU") == ("mou", None)

    def test_empty_hold(self) -> None:
        assert hold_display("") == ("", None)


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
        layers, _ = sample_layers()
        assert len(build_stacked_specs(layers)) == 36

    def test_layer_change_holds_use_layer_accent(self) -> None:
        layers, _ = sample_layers()
        specs = build_stacked_specs(layers)
        # One-shot layer thumbs in the fixture: LWR at column 2, RSE at column 3.
        assert specs[32]["hold"] == "LWR"
        assert specs[32]["accent"] == "sym"
        assert specs[32]["flavor"] == "oneshot"
        assert specs[33]["hold"] == "RSE"
        assert specs[33]["accent"] == "nav"
        assert specs[33]["flavor"] == "oneshot"
        assert not specs[34]["hold"]

    def test_plain_modifier_hold_stays_grey(self) -> None:
        layers, _ = sample_layers()
        specs = build_stacked_specs(layers)
        assert specs[10]["hold"] == "SHFT"
        assert specs[10]["accent"] == "mod"
        assert specs[10]["flavor"] == "tap-preferred"

    def test_stacked_corners_come_from_lower_and_raise(self) -> None:
        layers, _ = sample_layers()
        specs = build_stacked_specs(layers)
        assert specs[33]["sym_glyph"] == "btab"
        assert specs[34]["sym_glyph"] == "tab"
        assert specs[30]["base_glyph"] == "backspace"
        assert specs[30]["num_glyph"] == "escape"
        assert specs[32]["num_glyph"] == "return"

    def test_stacked_board_puts_raise_above_lower(self) -> None:
        layers, _ = sample_layers()
        svg = render_board(build_stacked_specs(layers), "stacked")
        key = svg.split(f'<g transform="translate({KW:.2f},0.00)">', 1)[1]
        key = key.split("</g>", 1)[0]
        assert 'class="num" x="45.0" y="18.1344">7</text>' in key
        assert 'class="sym" x="45.0" y="45.336000000000006">^</text>' in key

    def test_layer_holds_emit_glyphs_not_letters(self) -> None:
        layers, _ = sample_layers()
        svg = render_board(build_stacked_specs(layers), "stacked")
        assert ">⇊</text>" in svg
        assert ">⇈</text>" in svg
        assert ">✦</text>" in svg
        assert ">⇧</text>" in svg
        assert ">⌘</text>" in svg
        assert ">⌥</text>" in svg
        assert ">⌃</text>" in svg
        assert 'href="#glyph_bluetooth"' in svg
        assert ">lwr</text>" not in svg
        assert ">rse</text>" not in svg
        assert ">hyp</text>" not in svg
        assert ">adj</text>" not in svg
        assert ">shft</text>" not in svg
        assert ">cmd</text>" not in svg
        assert 'href="#glyph_lwr"' not in svg
        assert 'href="#glyph_cmd"' not in svg


class TestComboMarks:
    def test_grid_index_matches_flatten_order(self) -> None:
        assert grid_index(0, 0) == 0
        assert grid_index(0, 9) == 9
        assert grid_index(2, 2) == 22
        assert grid_index(2, 3) == 23
        assert grid_index(3, 0) == 30
        assert grid_index(3, 5) == 35

    def test_combo_sits_on_the_seam_between_its_triggers(self) -> None:
        layers, _ = sample_layers()
        default = layers[0]
        marks = combo_specs([Combo("Q", "W", "RET")], default)
        assert len(marks) == 1
        assert marks[0]["glyph"] == "return"
        assert marks[0]["text"] == ""
        positions = ortho_positions()
        q = positions[grid_index(0, 0)]
        w = positions[grid_index(0, 1)]
        assert marks[0]["x"] == (q[0] + w[0] + KW) / 2
        assert marks[0]["y"] == (q[1] + w[1] + KH) / 2

    def test_plain_label_combo_uses_text(self) -> None:
        layers, _ = sample_layers()
        marks = combo_specs([Combo("Q", "W", "X")], layers[0])
        assert marks[0]["text"] == "X"
        assert marks[0]["glyph"] is None

    def test_no_combos_renders_nothing(self) -> None:
        layers, _ = sample_layers()
        assert combo_specs([], layers[0]) == []


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
        assert 'class="oneshot symbol nav dejavu"' in svg
        assert ">⇈</text>" in svg
        assert ">rse</text>" not in svg
        assert 'href="#glyph_rse"' not in svg
        assert '<rect class="combo-badge"' not in svg

    def test_hold_box_is_inset_to_centre_the_mark(self) -> None:
        hx, hy, hw, hh = hold_box_rect()
        assert hx == PAD
        assert hx + hw / 2 == KW * 0.25
        assert hy + hh / 2 == KH * 0.80
        ikh = KH - 2 * PAD
        assert hy + hh == PAD + ikh
        # Smaller than the full bottom-left quadrant on the top and right.
        assert hw < (KW - 2 * PAD) / 2
        assert hh < ikh / 2
        svg = render_legend()
        assert (
            f'<rect class="hold-box tap-preferred mod" x="{hx}" '
            f'y="{hy}" width="{hw}" height="{hh}" '
            f'rx="{RADIUS}" ry="{RADIUS}"/>'
        ) in svg

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
        keymap = tmp_path / "keymap.txt"
        keymap.write_text(sample_keymap(), encoding="utf-8")
        written = render_diagrams(keymap, tmp_path, no_png=True)
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
        assert set(HOLD_GLYPHS.values()) <= set(GLYPH_PATHS)
        # Unicode marks stay text; do not grow a custom path for them.
        assert not {
            "cmd",
            "lwr",
            "rse",
            "shft",
            "alt",
            "ctrl",
            "hyp",
        } & set(GLYPH_PATHS)

    def test_legend_svg_covers_corners_flavors_and_icons(self) -> None:
        svg = render_legend()
        assert svg.startswith("<svg")
        assert ">Legend</text>" in svg
        assert ">Corners</text>" in svg
        assert ">base tap</text>" in svg
        assert ">hold</text>" in svg
        assert ">numbers / nav (rse)</text>" in svg
        assert ">symbols (lwr)</text>" in svg
        # Raise sits top-right, lower bottom-right.
        rse_at = svg.index(">numbers / nav (rse)</text>")
        lwr_at = svg.index(">symbols (lwr)</text>")
        assert 'y="46.1">numbers / nav (rse)</text>' in svg
        assert 'y="73.3">symbols (lwr)</text>' in svg
        assert rse_at < lwr_at
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
        for char, label in TEXT_LEGEND:
            assert f">{char}</text>" in svg
            assert f">{label}</text>" in svg
        assert 'href="#glyph_bluetooth"' in svg
        assert 'href="#glyph_lwr"' not in svg
        assert 'href="#glyph_cmd"' not in svg
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


class TestFontAndGlyphMetrics:
    def test_dejavu_class_only_for_marks_inter_lacks(self) -> None:
        assert {"✦", "⇊", "⇈"} == DEJAVU_FALLBACK_CHARS
        assert dejavu_class("✦") == " dejavu"
        assert dejavu_class("⇊") == " dejavu"
        assert dejavu_class("⇈") == " dejavu"
        assert dejavu_class("⇧") == ""
        assert dejavu_class("⌘") == ""
        assert dejavu_class("⌥") == ""
        assert dejavu_class("⌃") == ""
        assert dejavu_class("A") == ""
        assert dejavu_class("") == ""

    def test_svg_leads_with_inter_and_dejavu_fallback(self) -> None:
        svg = render_legend()
        assert 'font-family: Inter, "DejaVu Sans"' in svg
        assert "text.dejavu" in svg

    def test_hold_marks_select_dejavu_when_inter_cannot_draw_them(self) -> None:
        layers, _ = sample_layers()
        svg = render_board(build_stacked_specs(layers), "stacked")
        assert 'class="oneshot symbol sym dejavu"' in svg
        assert 'class="oneshot symbol nav dejavu"' in svg
        shift_at = svg.index(">⇧</text>")
        assert "dejavu" not in svg[shift_at - 80 : shift_at]
        star_at = svg.index(">✦</text>")
        assert "dejavu" in svg[star_at - 80 : star_at]
        legend = render_legend()
        assert 'class="hold hold-preferred nav symbol dejavu"' in legend
        assert 'class="legend-symbol dejavu"' in legend
        hyper_at = legend.index(">✦</text>")
        assert "legend-symbol dejavu" in legend[hyper_at - 80 : hyper_at]
        shift_legend = legend.index(">⇧</text>")
        assert "dejavu" not in legend[shift_legend - 80 : shift_legend]

    def test_glyph_em_matches_base_text_size(self) -> None:
        assert GLYPH_SCALE == FONT_SIZE_BASE / GLYPH_EM
        svg = render_legend()
        assert f'transform="scale({GLYPH_SCALE:.6f}) translate(-24,-24)"' in svg

    def test_overlay_and_combo_glyphs_scale_to_their_text(self) -> None:
        layers, _ = sample_layers()
        svg = render_board(
            build_stacked_specs(layers),
            "stacked",
            combos=[{"x": 180.0, "y": 141.67, "text": "", "glyph": "escape"}],
        )
        overlay = FONT_SIZE_NUM / FONT_SIZE_BASE
        combo = FONT_SIZE_COMBO / FONT_SIZE_BASE
        assert overlay == FONT_SIZE_SYM / FONT_SIZE_BASE
        assert f"scale({overlay:g})" in svg
        assert f"scale({combo:g})" in svg
        hold = FONT_SIZE_HOLD_SYMBOL / FONT_SIZE_BASE
        assert f"scale({hold:g})" in svg

    def test_use_glyph_skips_scale_at_base_size(self) -> None:
        assert (
            use_glyph("return", "base", 15.0, 18.1344)
            == '<use class="glyph base" href="#glyph_return" x="15.0" y="18.1344"/>'
        )
        assert (
            use_glyph("escape", "combo", 0, 0, font_size=FONT_SIZE_COMBO)
            == '<g transform="scale(0.5625)"><use class="glyph combo" '
            'href="#glyph_escape"/></g>'
        )
