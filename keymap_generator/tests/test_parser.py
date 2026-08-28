"""Tests for the keymap grid parser."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from keymap_generator.parser import (
    Combo,
    Key,
    KeymapParser,
    ParseError,
    parse_keymap,
    split_unescaped,
    strip_comment,
    unescape,
)

# Minimal six-layer keymap that satisfies LAYER_LABELS ordering.
LAYER_NAMES = ("default", "rse", "lwr", "hyp", "adj", "mou")


def blank_layer(name: str, overlays: str = "") -> str:
    suffix = f": {overlays}" if overlays else ""
    return textwrap.dedent(
        f"""\
        layer {name}{suffix}
          _ _ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
          _ _ _ _ _   _ _ _ _ _
              _ _ _   _ _
        """
    )


def full_keymap(*extra_blocks: str) -> str:
    """A keymap with the required six layers, plus any extra blocks first."""
    layers = "".join(blank_layer(name) for name in LAYER_NAMES)
    return "\n".join([*extra_blocks, layers])


def parse_source(source: str, path: str = "keymap.txt") -> tuple:
    return KeymapParser(path).parse(source.splitlines(keepends=True))


class TestHelpers:
    def test_split_unescaped_first_separator(self) -> None:
        assert split_unescaped("a/b/c", "/") == ["a", "b/c"]

    def test_split_unescaped_respects_escape(self) -> None:
        assert split_unescaped(r"a\/b/c", "/") == [r"a\/b", "c"]

    def test_strip_comment(self) -> None:
        assert strip_comment("A B // note") == "A B "
        assert strip_comment(r"A \// B // note") == r"A \// B "

    def test_unescape(self) -> None:
        assert unescape(r"\/") == "/"
        assert unescape(r"\\") == "\\"
        assert unescape(r"a\:b") == "a:b"


class TestParseKeymapHappyPath:
    def test_overlay_and_hold_tap_flavor(self) -> None:
        source = textwrap.dedent(
            """\
            overlay homerow
              _ _ _ _ _   _ _ _ _ _
              hyp shft alt cmd ctrl   ctrl cmd alt shft hyp
              _ _ _ _ _   _ _ _ _ _
                  _ _ _   _ _

            layer default: homerow
              Q W F P G   J L U Y *
              A R S T D   H N E I O
              Z/adj X C V B   K M , . '/adj
                  ESC/mou:hp _/shft TAB/lwr:hp   RET/BKSP:hp SPC/rse:hp

            layer rse: homerow
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
                  _ _ _   _ _

            layer lwr: homerow
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
                  _ _ _   _ _

            layer hyp
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
                  _ _ _   _ _

            layer adj
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
                  _ _ _   _ _

            layer mou
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
                  _ _ _   _ _

            combos
              Q W -> ESC
            """
        )
        layers, combos = parse_source(source)

        assert [layer.name for layer in layers] == list(LAYER_NAMES)
        default = layers[0]

        # Home-row modifiers come from the overlay.
        assert default.rows[1][0] == Key("A", "HYP", None)
        assert default.rows[1][3] == Key("T", "CMD", None)

        # Explicit hold-tap with hold-preferred flavor.
        assert default.rows[3][0] == Key("ESC", "MOU", "hp")

        # Hold-only sticky shift on the thumb.
        assert default.rows[3][1] == Key("", "SHFT", None)

        # Sticky modifier (same label on both sides) from overlay-inherited hold
        # is not sticky here; Z/adj is an explicit layer hold-tap.
        assert default.rows[2][0] == Key("Z", "ADJ", None)

        assert combos == [Combo("Q", "W", "ESC")]

    def test_sticky_key_and_escape(self) -> None:
        source = textwrap.dedent(
            """\
            layer default
              Q W F P G   J L U Y *
              A R S T D   H N E I O
              Z X C V B   K M , . '
                  ESC shft/shft TAB   RET/BKSP SPC

            """
        ) + "".join(blank_layer(name) for name in LAYER_NAMES[1:])
        layers, _ = parse_source(source)
        sticky = layers[0].rows[3][1]
        assert sticky == Key("SHFT", "SHFT", None)
        assert sticky.is_sticky

    def test_escaped_symbols(self) -> None:
        source = textwrap.dedent(
            """\
            layer default
              ~ ^ @ $ %   & \\/ \\\\ PIPE `
              UML < [ ( {   - \\_ \\: ; #
              _ > ] ) }   + = ? ! "
                  _ _ _   _ _

            """
        ) + "".join(blank_layer(name) for name in LAYER_NAMES[1:])
        layers, _ = parse_source(source)
        row0 = layers[0].rows[0]
        assert row0[6].tap == "/"
        assert row0[7].tap == "\\"
        row1 = layers[0].rows[1]
        assert row1[6].tap == "_"
        assert row1[7].tap == ":"

    def test_parse_keymap_from_file(self, tmp_path: Path) -> None:
        path = tmp_path / "keymap.txt"
        path.write_text(full_keymap())
        layers, combos = parse_keymap(path)
        assert len(layers) == 6
        assert combos == []


class TestParseErrors:
    def test_unknown_overlay(self) -> None:
        source = blank_layer("default", "missing") + "".join(
            blank_layer(name) for name in LAYER_NAMES[1:]
        )
        with pytest.raises(ParseError, match="unknown overlay"):
            parse_source(source)

    def test_wrong_row_count(self) -> None:
        source = textwrap.dedent(
            """\
            layer default
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
            """
        ) + "".join(blank_layer(name) for name in LAYER_NAMES[1:])
        with pytest.raises(ParseError, match="has 3 rows"):
            parse_source(source)

    def test_wrong_cell_count(self) -> None:
        source = textwrap.dedent(
            """\
            layer default
              _ _ _ _ _   _ _ _ _
              _ _ _ _ _   _ _ _ _ _
              _ _ _ _ _   _ _ _ _ _
                  _ _ _   _ _
            """
        ) + "".join(blank_layer(name) for name in LAYER_NAMES[1:])
        with pytest.raises(ParseError, match="has 9 keys"):
            parse_source(source)

    def test_unknown_flavor(self) -> None:
        source = textwrap.dedent(
            """\
            layer default
              Q W F P G   J L U Y *
              A R S T D   H N E I O
              Z X C V B   K M , . '
                  ESC/mou:xx _ _   _ _

            """
        ) + "".join(blank_layer(name) for name in LAYER_NAMES[1:])
        with pytest.raises(ParseError, match="unknown flavor"):
            parse_source(source)

    def test_flavor_on_sticky_key(self) -> None:
        source = textwrap.dedent(
            """\
            layer default
              Q W F P G   J L U Y *
              A R S T D   H N E I O
              Z X C V B   K M , . '
                  ESC shft/shft:hp _   _ _

            """
        ) + "".join(blank_layer(name) for name in LAYER_NAMES[1:])
        with pytest.raises(ParseError, match="takes no flavor"):
            parse_source(source)

    def test_combos_cannot_have_name(self) -> None:
        source = full_keymap() + "combos chords\n"
        with pytest.raises(ParseError, match="take no name"):
            parse_source(source)

    def test_layer_needs_name(self) -> None:
        source = "layer\n  _\n"
        with pytest.raises(ParseError, match="need a name"):
            parse_source(source)

    def test_wrong_layer_order(self) -> None:
        # Swap rse and lwr so layer 1 is not named rse.
        source = (
            blank_layer("default")
            + blank_layer("lwr")
            + blank_layer("rse")
            + blank_layer("hyp")
            + blank_layer("adj")
            + blank_layer("mou")
        )
        with pytest.raises(ParseError, match="must be named 'rse'"):
            parse_source(source)

    def test_bad_combo_form(self) -> None:
        source = full_keymap() + "combos\n  Q W ESC\n"
        with pytest.raises(ParseError, match="expected a combo"):
            parse_source(source)

    def test_content_before_block(self) -> None:
        with pytest.raises(ParseError, match="expected an overlay"):
            parse_source("Q W F\n")
