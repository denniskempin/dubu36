"""Render keymap.txt to Selenium-style SVG (and PNG) diagrams.

Per-key legend layout (matches https://onedeadkey.github.io/selenium/):
  Top-left     base layer tap (grey)
  Bottom-left  hold binding (grey by default, boxed)
  Top-right    symbol layer (lwr) — purple
  Bottom-right number/nav layer (rse) — orange

Hold box flavors (from the keymap's hold-tap flavor / one-shot form):
  tp (tap-preferred)  — outline box in the bottom-left quadrant
  hp (hold-preferred) — solid box in the bottom-left quadrant
  oneshot             — solid bar covering the full left half (TL+BL):
                        one-shot modifier/layer on tap, momentary on hold

Hold labels/boxes are grey by default. A hold binding that itself switches
to the symbol (lwr) or number/nav (rse) layer is colored like that layer
instead, so layer-change labels always read as purple/orange.

The hyp and adj layers are excluded from diagram generation (their
mod-tap holds still render elsewhere, just in the default grey).

Combos render on the stacked reference card only: a small rounded box
sits on the seam between the two trigger keys and shows the result,
using the same glyphs as taps. Per-layer boards omit them.

Well-known taps (TAB, RET, BKSP, ESC, SPC, arrows, HOME/END, …) render as
icons instead of text — see TAP_GLYPHS / GLYPH_PATHS. `render_legend` draws
those icons plus the corner and hold-flavor keycaps into diagrams/legend.svg.
"""

from __future__ import annotations

import html
from pathlib import Path

from keymap_generator.parser import (
    ROW_SIZES,
    Combo,
    Key,
    Layer,
    find_key_position,
    parse_keymap,
)

DEFAULT_KEYMAP = Path("keymap.txt")
DEFAULT_OUT = Path("diagrams")

# PNG raster scale relative to the SVG's native (CSS-pixel) size — 3x gives
# crisp previews on retina displays without huge file sizes.
PNG_SCALE = 3.0

# Physical key size (Selenium uses 60×56.67).
KW = 60.0
KH = 56.67
PAD = 1.0
RADIUS = 4.0
SPLIT_GAP = 30.0

# Combo marks sit on the seam between the two trigger keys. The box is
# a compact keycap (same corner radius) so it reads as part of the board.
COMBO_W = 20.0
COMBO_H = 19.0
COMBO_GLYPH_SCALE = 0.55

STACK_BASE = "default"
STACK_SYM = "lwr"
STACK_NUM = "rse"

# Layers excluded from diagram generation (still usable as hold targets
# elsewhere, but they don't get their own reference/layer boards).
EXCLUDED_LAYERS = frozenset({"hyp", "adj"})

# Short hold labels shown in the bottom-left quadrant.
HOLD_DISPLAY = {
    "SHFT": "shft",
    "ALT": "alt",
    "CMD": "cmd",
    "CTRL": "ctrl",
    "HYP": "hyp",
    "ADJ": "adj",
    "LWR": "lwr",
    "RSE": "rse",
    "MOU": "mou",
}

# Hold-box / hold-label accent. Only holds that themselves switch to the
# symbol (lwr) or number/nav (rse) layer borrow that layer's color, so the
# diagram legend stays visually tied to the two colored quadrants. Every
# other hold (plain modifiers, hyp, adj, mou, …) falls back to the neutral
# grey used for the base layer legend.
HOLD_ACCENT = {
    "LWR": "sym",
    "RSE": "nav",
}
DEFAULT_HOLD_ACCENT = "mod"

# Tap labels that get replaced with an icon (see GLYPH_PATHS) instead of
# text, wherever they appear (base/sym/num quadrants, any layer board).
TAP_GLYPHS = {
    "TAB": "tab",
    "SHFT_TAB": "btab",
    "RET": "return",
    "BKSP": "backspace",
    "ALT_BKSP": "delete-word",
    "ESC": "escape",
    "SPC": "space",
    "UP": "up",
    "DOWN": "down",
    "LEFT": "left",
    "RIGHT": "right",
    "HOME": "home",
    "END": "end",
    "WORD_L": "word-left",
    "WORD_R": "word-right",
    "FWD": "hist-fwd",
    "BCK": "hist-back",
    "TAB_L": "btab",
    "TAB_R": "tab",
}

# A few labels that read better as glyphs/symbols than as their raw codes.
TAP_DISPLAY = {
    "PIPE": "|",
    "UML": "uml",
}

# Icon-legend entries: one or more glyphs sharing a label, in display
# order. Directional pairs (and the four arrows) share a label. Every
# GLYPH_PATHS key must appear here so a new icon cannot silently skip the
# README legend.
GLYPH_LEGEND: tuple[tuple[tuple[str, ...], str], ...] = (
    (("escape",), "escape"),
    (("tab", "btab"), "tab"),
    (("return",), "return"),
    (("backspace",), "backspace"),
    (("delete-word",), "delete word"),
    (("space",), "space"),
    (("up", "down", "left", "right"), "arrows"),
    (("home", "end"), "home / end"),
    (("word-left", "word-right"), "word"),
    (("hist-back", "hist-fwd"), "history"),
)

GLYPH_PATHS = {
    "backspace": "M22,19l10,10 M22,29l10-10 M6,24l10,13h26v-26h-26z",
    # The backspace box's own point already reads as one chevron; add a
    # second, matching chevron just outside it to turn that into a double
    # chevron (delete "further back") while keeping the X for "delete".
    "delete-word": ("M22,19l10,10 M22,29l10-10 M6,24l10,13h26v-26h-26z M6,17l-6,7,6,7"),
    "return": "M42,13V27H6 m8-8l-8,8l8,8",
    "space": "M42,24V32H6V24",
    "escape": "M24,24l-18-18 m0,10v-10h10 M24,6A18,18,0,1,1,6,24",
    "up": "M24,42v-36 m-8,6l8-8l8,8",
    "down": "M24,6v36 m-8,-6l8,8l8-8",
    "left": "M42,24h-36 m6-8l-8,8l8,8",
    "right": "M6,24h36 m-6-8l8,8l-8,8",
    "tab": "M6,24h27 m-6-8l8,8l-8,8 M42,12V36",
    "btab": "M42,24h-27 m6-8l-8,8l8,8 M6,12V36",
    "home": "M42,42l-28-28 m0,10v-10h10 m8-8h-26v26",
    "end": "M6,6l28,28 m0-10v10h-10 m-8,8h26v-26",
    # Double chevron ("»"/"«") for word-jump — visually distinct from the
    # single-chevron cursor arrows above.
    "word-right": "M8,13l10,11-10,11 M24,13l10,11-10,11",
    "word-left": "M40,13l-10,11,10,11 M24,13l-10,11,10,11",
    # Curved hook for browser history nav — distinct from both the
    # straight cursor arrows and the word-jump chevrons.
    "hist-fwd": "M10,32A16,14,0,1,0,36,18 m-2,-8l2,8l-8,2",
    "hist-back": "M38,32A16,14,0,1,1,12,18 m2,-8l-2,8l8,2",
}


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def tap_display(label: str) -> tuple[str, str | None]:
    """Return (text, glyph): glyph is set (and text cleared) for known icons."""
    if label in TAP_GLYPHS:
        return "", TAP_GLYPHS[label]
    return TAP_DISPLAY.get(label, label), None


def hold_flavor(key: Key) -> str | None:
    """Map a parsed key to a diagram hold-box flavor, or None if no hold."""
    hold = key.hold or ""
    if not hold:
        return None
    if key.is_oneshot:
        return "oneshot"
    if key.flavor == "hp":
        return "hold-preferred"
    # Explicit tp, or an inherited/default hold with no flavor → outline box.
    return "tap-preferred"


def flatten_layer(layer: Layer) -> list[Key]:
    """Flatten a layer's rows into the 36-key ortho index order."""
    return [key for row in layer.rows for key in row]


def grid_index(row: int, column: int) -> int:
    """Flatten a (row, column) cell into the 36-key ortho index."""
    return sum(ROW_SIZES[:row]) + column


def layers_by_name(layers: list[Layer]) -> dict[str, Layer]:
    return {layer.name: layer for layer in layers}


def ortho_positions(columns: int = 5, thumbs: int = 3) -> list[tuple[float, float]]:
    """Return (x, y) for each of the 36 key indices (left then right per row)."""
    positions: list[tuple[float, float]] = []
    for row in range(3):
        y = row * KH
        for col in range(columns):
            positions.append((col * KW, y))
        for col in range(columns):
            positions.append((columns * KW + SPLIT_GAP + col * KW, y))
    thumb_y = 3 * KH + 8
    left_thumb_xs = [(columns - thumbs + i) * KW for i in range(thumbs)]
    right_thumb_xs = [columns * KW + SPLIT_GAP + i * KW for i in range(thumbs)]
    for x in left_thumb_xs + right_thumb_xs:
        positions.append((x, thumb_y))
    return positions


def board_size(columns: int = 5, thumbs: int = 3) -> tuple[float, float]:
    width = columns * 2 * KW + SPLIT_GAP + 20
    height = 3 * KH + KH + 40
    return width, height


def build_stacked_specs(layers: list[Layer]) -> list[dict]:
    """Project semantic layers into per-key visual specs for the reference card.

    Every key uses the same corners:
      TL base (default), BL hold, TR symbols (lwr), BR numbers/nav (rse).
    """
    by_name = layers_by_name(layers)
    base = flatten_layer(by_name[STACK_BASE])
    sym = flatten_layer(by_name[STACK_SYM]) if STACK_SYM in by_name else []
    num = flatten_layer(by_name[STACK_NUM]) if STACK_NUM in by_name else []

    specs: list[dict] = []
    for i, key in enumerate(base):
        hold = key.hold or ""
        flavor = hold_flavor(key)
        base_text, base_glyph = tap_display(key.tap)
        sym_key = sym[i] if i < len(sym) else Key("", "", None)
        sym_text, sym_glyph = tap_display(sym_key.tap)
        num_key = num[i] if i < len(num) else Key("", "", None)
        num_text, num_glyph = tap_display(num_key.tap)
        specs.append(
            {
                "base": base_text,
                "base_glyph": base_glyph,
                "hold": hold,
                "flavor": flavor,
                "accent": HOLD_ACCENT.get(hold, DEFAULT_HOLD_ACCENT),
                "sym": sym_text,
                "sym_glyph": sym_glyph,
                "num": num_text,
                "num_glyph": num_glyph,
            }
        )
    return specs


def combo_specs(
    combos: list[Combo],
    default_layer: Layer,
    columns: int = 5,
    thumbs: int = 3,
) -> list[dict]:
    """Place each combo at the midpoint of its two trigger keys.

    Combos name those keys by the label they tap on the default layer, the
    same way the firmware generators resolve them.
    """
    positions = ortho_positions(columns, thumbs)
    marks: list[dict] = []
    for combo in combos:
        x1, y1 = positions[grid_index(*find_key_position(default_layer, combo.a))]
        x2, y2 = positions[grid_index(*find_key_position(default_layer, combo.b))]
        text, glyph = tap_display(combo.result)
        marks.append(
            {
                "x": (x1 + x2 + KW) / 2,
                "y": (y1 + y2 + KH) / 2,
                "text": text,
                "glyph": glyph,
            }
        )
    return marks


def layer_specs(layer: Layer) -> list[dict]:
    """Per-layer view: that layer's tap at TL, hold at BL (same anchors)."""
    specs: list[dict] = []
    for key in flatten_layer(layer):
        hold = key.hold or ""
        flavor = hold_flavor(key)
        base_text, base_glyph = tap_display(key.tap)
        specs.append(
            {
                "base": base_text,
                "base_glyph": base_glyph,
                "hold": hold,
                "flavor": flavor,
                "accent": HOLD_ACCENT.get(hold, DEFAULT_HOLD_ACCENT),
                "sym": "",
                "sym_glyph": None,
                "num": "",
                "num_glyph": None,
            }
        )
    return specs


def svg_style(*, combos: bool = False) -> str:
    style = """
    svg.keymap { background: #1e1e2e; font-family: sans-serif; }
    rect.keycap { fill: #333333; stroke: #555555; stroke-width: 0.5px; }
    text { fill: #c8c8c8; text-anchor: middle; dominant-baseline: central; }
    text.base { font-size: 16px; font-weight: 600; fill: #dddddd; }
    text.hold { font-size: 11px; }
    text.sym { font-size: 13px; fill: #9999ff; }
    text.num { font-size: 13px; fill: #ee9944; }
    text.oneshot { font-size: 12px; font-weight: 600; }
    use.glyph { fill: none; stroke: #c8c8c8; stroke-width: 2.5px;
                stroke-linecap: round; stroke-linejoin: round; }
    use.glyph.base { stroke: #dddddd; stroke-width: 3px; }
    use.glyph.sym { stroke: #9999ff; }
    use.glyph.num { stroke: #ee9944; }
    rect.hold-box { stroke-width: 1.2px; }
    rect.hold-box.tap-preferred.mod { fill: none; stroke: #c8c8c8; }
    rect.hold-box.tap-preferred.sym { fill: none; stroke: #9999ff; }
    rect.hold-box.tap-preferred.nav { fill: none; stroke: #ee9944; }
    rect.hold-box.hold-preferred.mod { fill: #666666; stroke: #666666; }
    rect.hold-box.hold-preferred.sym { fill: #6666bb; stroke: #6666bb; }
    rect.hold-box.hold-preferred.nav { fill: #aa7755; stroke: #aa7755; }
    rect.hold-box.oneshot.mod { fill: #666666; stroke: #666666; }
    rect.hold-box.oneshot.sym { fill: #6666bb; stroke: #6666bb; }
    rect.hold-box.oneshot.nav { fill: #aa7755; stroke: #aa7755; }
    text.hold.hold-preferred.mod, text.oneshot.mod { fill: #eeeeee; font-weight: 700; }
    text.hold.hold-preferred.sym, text.oneshot.sym,
    text.hold.hold-preferred.nav, text.oneshot.nav { fill: #1a1a1a; font-weight: 700; }
    text.hold.tap-preferred { fill: #c8c8c8; }
    text.title { font-size: 14px; fill: #888888; text-anchor: start; }
    """.strip()
    if combos:
        style += """
    rect.combo-badge { fill: #4a8f7a; stroke: #4a8f7a; }
    use.glyph.combo { stroke: #1a1a1a; stroke-width: 3.5px; }
    text.combo { font-size: 9px; font-weight: 700; fill: #1a1a1a; }"""
    return style


def legend_style() -> str:
    """Extra CSS for the standalone legend SVG (not inlined into the boards)."""
    return """
    text.section { font-size: 12px; fill: #888888; text-anchor: start;
                   font-weight: 600; }
    text.callout { font-size: 11px; fill: #c8c8c8; }
    text.callout.end { text-anchor: end; }
    text.callout.start { text-anchor: start; }
    text.callout.sym { fill: #9999ff; }
    text.callout.num { fill: #ee9944; }
    text.caption { font-size: 11px; fill: #aaaaaa; text-anchor: middle; }
    text.caption.sub { font-size: 10px; fill: #777777; }
    text.glyph-label { font-size: 11px; fill: #c8c8c8; text-anchor: start; }
    """.strip()


def key_spec(
    *,
    base: str = "",
    base_glyph: str | None = None,
    hold: str = "",
    flavor: str | None = None,
    accent: str = DEFAULT_HOLD_ACCENT,
    sym: str = "",
    sym_glyph: str | None = None,
    num: str = "",
    num_glyph: str | None = None,
) -> dict:
    """Build a draw_key spec with every quadrant filled in or empty."""
    return {
        "base": base,
        "base_glyph": base_glyph,
        "hold": hold,
        "flavor": flavor,
        "accent": accent,
        "sym": sym,
        "sym_glyph": sym_glyph,
        "num": num,
        "num_glyph": num_glyph,
    }


def glyph_defs() -> str:
    parts = ["<defs>"]
    for name, d in GLYPH_PATHS.items():
        parts.append(
            f'<path id="glyph_{name}" class="symbol" '
            f'transform="scale(0.4) translate(-24,-30)" d="{d}"/>'
        )
    parts.append("</defs>")
    return "\n".join(parts)


def draw_key(x: float, y: float, spec: dict) -> str:
    """Draw one key with fixed legend anchors on every key.

    Top-left      base
    Bottom-left   hold (outline / solid / one-shot left bar)
    Top-right     symbol
    Bottom-right  number / nav
    """
    ikw = KW - 2 * PAD
    ikh = KH - 2 * PAD
    parts = [f'<g transform="translate({x:.2f},{y:.2f})">']
    parts.append(
        f'<rect class="keycap" x="{PAD}" y="{PAD}" width="{ikw}" height="{ikh}" '
        f'rx="{RADIUS}" ry="{RADIUS}"/>'
    )

    hold = spec.get("hold") or ""
    flavor = spec.get("flavor")
    accent = spec.get("accent") or DEFAULT_HOLD_ACCENT
    hold_label = HOLD_DISPLAY.get(hold, hold.lower() if hold else "")

    if hold and flavor == "oneshot":
        parts.append(
            f'<rect class="hold-box oneshot {accent}" x="{PAD}" y="{PAD}" '
            f'width="{ikw / 2}" height="{ikh}" rx="{RADIUS}" ry="{RADIUS}"/>'
        )
    elif hold and flavor in ("tap-preferred", "hold-preferred"):
        parts.append(
            f'<rect class="hold-box {flavor} {accent}" x="{PAD}" '
            f'y="{PAD + ikh / 2}" width="{ikw / 2}" height="{ikh / 2}" '
            f'rx="{RADIUS}" ry="{RADIUS}"/>'
        )

    x_left = KW * 0.25
    x_right = KW * 0.75
    y_top = KH * 0.32
    y_bot = KH * 0.80

    # One-shot keys use the left-bar label alone: tap and hold are the same
    # label, so drawing base as well would duplicate it.
    if flavor != "oneshot":
        base = spec.get("base") or ""
        if base:
            parts.append(
                f'<text class="base" x="{x_left}" y="{y_top}">{esc(base)}</text>'
            )
        elif spec.get("base_glyph"):
            parts.append(
                f'<use class="glyph base" href="#glyph_{spec["base_glyph"]}" '
                f'x="{x_left}" y="{y_top}"/>'
            )

    if hold and flavor == "oneshot":
        parts.append(
            f'<text class="oneshot {accent}" '
            f'transform="translate({PAD + ikw / 4},{KH / 2}) rotate(-90)">'
            f"{esc(hold_label)}</text>"
        )
    elif hold and flavor:
        parts.append(
            f'<text class="hold {flavor} {accent}" x="{x_left}" y="{y_bot}">'
            f"{esc(hold_label)}</text>"
        )
    elif hold:
        parts.append(
            f'<text class="hold" x="{x_left}" y="{y_bot}">{esc(hold_label)}</text>'
        )

    sym = spec.get("sym") or ""
    if sym:
        parts.append(f'<text class="sym" x="{x_right}" y="{y_top}">{esc(sym)}</text>')
    elif spec.get("sym_glyph"):
        parts.append(
            f'<use class="glyph sym" href="#glyph_{spec["sym_glyph"]}" '
            f'x="{x_right}" y="{y_top}"/>'
        )

    num = spec.get("num") or ""
    if num:
        parts.append(f'<text class="num" x="{x_right}" y="{y_bot}">{esc(num)}</text>')
    elif spec.get("num_glyph"):
        parts.append(
            f'<use class="glyph num" href="#glyph_{spec["num_glyph"]}" '
            f'x="{x_right}" y="{y_bot}"/>'
        )

    parts.append("</g>")
    return "\n".join(parts)


def draw_combo_mark(mark: dict) -> str:
    """Draw the combo result as a small rounded box at the seam of its triggers."""
    text = mark.get("text") or ""
    glyph = mark.get("glyph")
    parts = [
        f'<g class="combo" transform="translate({mark["x"]:.2f},{mark["y"]:.2f})">',
        f'<rect class="combo-badge" x="{-COMBO_W / 2}" y="{-COMBO_H / 2}" '
        f'width="{COMBO_W}" height="{COMBO_H}" rx="{RADIUS}" ry="{RADIUS}"/>',
    ]
    if glyph:
        parts.append(
            f'<g transform="scale({COMBO_GLYPH_SCALE})">'
            f'<use class="glyph combo" href="#glyph_{glyph}"/>'
            f"</g>"
        )
    elif text:
        parts.append(f'<text class="combo">{esc(text)}</text>')
    parts.append("</g>")
    return "\n".join(parts)


def render_board(
    specs: list[dict],
    title: str,
    columns: int = 5,
    thumbs: int = 3,
    combos: list[dict] | None = None,
) -> str:
    positions = ortho_positions(columns, thumbs)
    if len(specs) != len(positions):
        raise ValueError(f"Expected {len(positions)} keys, got {len(specs)}")
    width, height = board_size(columns, thumbs)
    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" class="keymap" '
        f'width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="-10 -24 {width} {height}">',
        f"<style>{svg_style(combos=bool(combos))}</style>",
        glyph_defs(),
        f'<text class="title" x="0" y="-8">{esc(title)}</text>',
    ]
    for spec, (x, y) in zip(specs, positions, strict=True):
        body.append(draw_key(x, y, spec))
    for mark in combos or []:
        body.append(draw_combo_mark(mark))
    body.append("</svg>")
    return "\n".join(body)


def slug(name: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in name).strip("-").lower()


def render_legend() -> str:
    """SVG legend for the stacked reference drawing: corners, flavors, icons."""
    # Match the reference board's width so the two images line up in the README.
    width = 650.0
    key_y = 28.0
    corner_x = 100.0
    flavor_x = 325.0
    flavor_gap = 100.0
    icon_row_h = 28.0

    parts = [
        draw_key(
            corner_x,
            key_y,
            key_spec(
                base="A",
                hold="CMD",
                flavor="tap-preferred",
                sym="@",
                num="8",
            ),
        )
    ]
    y_top = key_y + KH * 0.32
    y_bot = key_y + KH * 0.80
    parts.extend(
        [
            '<text class="section" x="0" y="10">Corners</text>',
            f'<text class="callout end" x="{corner_x - 8:.1f}" y="{y_top:.1f}">'
            "base tap</text>",
            f'<text class="callout end" x="{corner_x - 8:.1f}" y="{y_bot:.1f}">'
            "hold</text>",
            f'<text class="callout start sym" x="{corner_x + KW + 8:.1f}" '
            f'y="{y_top:.1f}">symbols (lwr)</text>',
            f'<text class="callout start num" x="{corner_x + KW + 8:.1f}" '
            f'y="{y_bot:.1f}">numbers / nav (rse)</text>',
        ]
    )

    flavors: tuple[tuple[dict, str, str], ...] = (
        (
            key_spec(base="A", hold="CMD", flavor="tap-preferred"),
            "tap-preferred",
            "outline · home row",
        ),
        (
            key_spec(
                base_glyph="return",
                hold="RSE",
                flavor="hold-preferred",
                accent="nav",
            ),
            "hold-preferred",
            "solid · thumbs",
        ),
        (
            key_spec(hold="LWR", flavor="oneshot", accent="sym"),
            "one-shot",
            "left bar · sticky tap",
        ),
    )
    parts.append(f'<text class="section" x="{flavor_x:.1f}" y="10">Hold flavors</text>')
    for i, (spec, title, subtitle) in enumerate(flavors):
        x = flavor_x + i * flavor_gap
        cx = x + KW / 2
        parts.append(draw_key(x, key_y, spec))
        parts.append(
            f'<text class="caption" x="{cx:.1f}" y="{key_y + KH + 14:.1f}">'
            f"{esc(title)}</text>"
        )
        parts.append(
            f'<text class="caption sub" x="{cx:.1f}" y="{key_y + KH + 26:.1f}">'
            f"{esc(subtitle)}</text>"
        )

    icon_title_y = key_y + KH + 48.0
    icon_y = icon_title_y + 20.0
    parts.append(f'<text class="section" x="0" y="{icon_title_y:.1f}">Icons</text>')
    glyph_step = 22.0
    # Pack groups left-to-right so a 4-arrow cluster can be wider than a
    # single icon without forcing a rigid column grid.
    x = 0.0
    row = 0
    n_icon_rows = 1
    for names, label in GLYPH_LEGEND:
        first_gx = 12.0
        label_x = first_gx + (len(names) - 1) * glyph_step + 16.0
        # 11px sans-serif is roughly 6.4px per character.
        item_w = label_x + max(len(label) * 6.4, 24.0) + 16.0
        if x > 0.0 and x + item_w > width:
            x = 0.0
            row += 1
        n_icon_rows = row + 1
        y = icon_y + row * icon_row_h
        for j, name in enumerate(names):
            gx = x + first_gx + j * glyph_step
            parts.append(
                f'<use class="glyph base" href="#glyph_{name}" '
                f'x="{gx:.1f}" y="{y:.1f}"/>'
            )
        parts.append(
            f'<text class="glyph-label" x="{x + label_x:.1f}" y="{y:.1f}">'
            f"{esc(label)}</text>"
        )
        x += item_w

    # viewBox origin is ( -10, -24 ); height includes that top inset.
    height = round(icon_y + n_icon_rows * icon_row_h + 16.0 + 24.0, 2)
    header = [
        f'<svg xmlns="http://www.w3.org/2000/svg" class="keymap" '
        f'width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="-10 -24 {width} {height}">',
        f"<style>{svg_style()}\n{legend_style()}</style>",
        glyph_defs(),
        '<text class="title" x="0" y="-8">Legend</text>',
    ]
    return "\n".join([*header, *parts, "</svg>"])


def render_png(svg_path: Path) -> Path:
    """Render svg_path to a same-named .png next to it, and return its path."""
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError(
            "cairosvg is required to render PNGs (uv sync --group diagrams)"
        ) from exc

    png_path = svg_path.with_suffix(".png")
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), scale=PNG_SCALE)
    return png_path


def render_diagrams(
    keymap_path: Path,
    out_dir: Path,
    *,
    stacked_only: bool = False,
    layers_only: bool = False,
    no_png: bool = False,
) -> list[Path]:
    """Render SVG (+ optional PNG) diagrams for `keymap_path` into `out_dir`."""
    layers, combos = parse_keymap(keymap_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    if not stacked_only:
        for layer in layers:
            if layer.name in EXCLUDED_LAYERS:
                continue
            path = out_dir / f"layer-{slug(layer.name)}.svg"
            path.write_text(
                render_board(layer_specs(layer), layer.name),
                encoding="utf-8",
            )
            written.append(path)

    if not layers_only:
        path = out_dir / "reference.svg"
        default = layers_by_name(layers)[STACK_BASE]
        path.write_text(
            render_board(
                build_stacked_specs(layers),
                "Dubu36 reference",
                combos=combo_specs(combos, default),
            ),
            encoding="utf-8",
        )
        written.append(path)
        path = out_dir / "legend.svg"
        path.write_text(render_legend(), encoding="utf-8")
        written.append(path)

    if not no_png:
        for path in list(written):
            written.append(render_png(path))

    return written
