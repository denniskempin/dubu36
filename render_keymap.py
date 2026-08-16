#!/usr/bin/env python3
"""Render keymap.yaml to SVG diagrams using Selenium-style key anatomy.

Per-key legend layout (matches https://onedeadkey.github.io/selenium/):
  Top-left     base layer
  Bottom-left  hold binding (boxed)
  Top-right    symbol layer (Lower)
  Bottom-right number/nav layer (Raise)

Hold box flavors:
  tap-preferred  — outline box in the bottom-left quadrant
  hold-preferred — solid box in the bottom-left quadrant
  sticky         — solid bar covering the full left half (TL+BL)
"""
from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
DEFAULT_KEYMAP = ROOT / "keymap.yaml"
DEFAULT_OUT = ROOT / "diagrams"

# Physical key size (Selenium uses 60×56.67).
KW = 60.0
KH = 56.67
PAD = 1.0
RADIUS = 4.0
SPLIT_GAP = 30.0

STACK_BASE = "Default"
STACK_SYM = "Lower"
STACK_NUM = "Raise"
# Optional BL shortcuts overlay on the stacked card (Selenium puts nav shortcuts there).
STACK_EDIT = "Mouse"

HOLD_FLAVORS = frozenset({"tap-preferred", "hold-preferred", "sticky"})

HOLD_DISPLAY = {
    "Shift": "shft",
    "Alt": "alt",
    "Cmd": "cmd",
    "Ctrl": "ctrl",
    "Hyper": "hyp",
    "Adjust": "adj",
    "Lower": "lwr",
    "Raise": "rse",
    "Mouse": "mou",
}

# Layer accent used for hold box / sticky fill colors.
HOLD_ACCENT = {
    "Shift": "mod",
    "Alt": "mod",
    "Cmd": "mod",
    "Ctrl": "mod",
    "Hyper": "fun",
    "Adjust": "fun",
    "Lower": "sym",
    "Raise": "nav",
    "Mouse": "nav",
}

MOUSE_DISPLAY = {
    "Cmd_Z": "undo",
    "Cmd_X": "cut",
    "Cmd_C": "copy",
    "Cmd_V": "paste",
    "Cmd_Q": "quit",
    "Cmd_W": "close",
    "Cmd_S": "save",
    "Cmd_T": "tab",
}

NAV_GLYPHS = {
    "Up": "up",
    "Down": "down",
    "Left": "left",
    "Right": "right",
    "Home": "home",
    "End": "end",
    "WordL": "left",
    "WordR": "right",
    "Bksp": "backspace",
    "Ret": "return",
    "Tab": "tab",
    "Esc": "escape",
    "Spc": "space",
    "Fwd": "right",
    "Bck": "left",
    "TabL": "btab",
    "TabR": "tab",
}

GLYPH_PATHS = {
    "backspace": "M22,19l10,10 M22,29l10-10 M6,24l10,13h26v-26h-26z",
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
}


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def flatten_keys(layer_value) -> list:
    keys = []

    def walk(node):
        if isinstance(node, list):
            for item in node:
                walk(item)
        else:
            keys.append(node)

    walk(layer_value)
    return keys


def key_field(spec, *names: str) -> str:
    if spec is None:
        return ""
    if isinstance(spec, str):
        return spec if "t" in names or "tap" in names else ""
    for name in names:
        if name in spec and spec[name] is not None:
            return str(spec[name])
    return ""


def key_tap(spec) -> str:
    return key_field(spec, "t", "tap", "center")


def key_hold(spec) -> str:
    return key_field(spec, "h", "hold", "bottom")


def key_type(spec) -> str:
    return key_field(spec, "type")


def hold_flavor(type_str: str) -> str | None:
    for token in type_str.split():
        if token in HOLD_FLAVORS:
            return token
    return None


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def ortho_positions(columns: int = 5, thumbs: int = 3):
    """Return (x, y) for each of the 36 key indices (left then right per row)."""
    positions = []
    # Main matrix: 3 rows × (left cols + right cols)
    for row in range(3):
        y = row * KH
        for col in range(columns):
            positions.append((col * KW, y))
        for col in range(columns):
            positions.append((columns * KW + SPLIT_GAP + col * KW, y))
    # Thumbs under each half, inward-biased like Selenium ortho.
    thumb_y = 3 * KH + 8
    left_thumb_xs = [(columns - thumbs + i) * KW for i in range(thumbs)]
    right_thumb_xs = [
        columns * KW + SPLIT_GAP + i * KW for i in range(thumbs)
    ]
    for x in left_thumb_xs + right_thumb_xs:
        positions.append((x, thumb_y))
    return positions


def board_size(columns: int = 5, thumbs: int = 3) -> tuple[float, float]:
    width = columns * 2 * KW + SPLIT_GAP + 20
    height = 3 * KH + KH + 40
    return width, height


def legend_for_corner(spec, *, role: str) -> tuple[str, str | None]:
    """Return (text, glyph_id_or_None) for a stacked corner."""
    tap = key_tap(spec)
    if not tap:
        return "", None
    if role == "edit":
        return MOUSE_DISPLAY.get(tap, tap.replace("Cmd_", "").lower()), None
    if role == "num" and tap in NAV_GLYPHS:
        return "", NAV_GLYPHS[tap]
    if role == "num" and tap.lower().startswith("hyp_"):
        return tap.split("_", 1)[1], None
    return tap, None


def build_stacked_specs(data: dict) -> list[dict]:
    """Project semantic layers into per-key visual specs for the reference card."""
    layers = data["layers"]
    base = flatten_keys(layers[STACK_BASE])
    sym = flatten_keys(layers.get(STACK_SYM, []))
    num = flatten_keys(layers.get(STACK_NUM, []))
    edit = flatten_keys(layers.get(STACK_EDIT, []))

    specs = []
    for i, b in enumerate(base):
        hold = key_hold(b)
        flavor = hold_flavor(key_type(b))
        sym_text = key_tap(sym[i]) if i < len(sym) else ""
        num_raw = num[i] if i < len(num) else ""
        num_tap = key_tap(num_raw)
        if num_tap in NAV_GLYPHS:
            num_text, num_glyph = "", NAV_GLYPHS[num_tap]
        else:
            num_text, num_glyph = num_tap, None

        edit_text = ""
        if i < len(edit) and not hold:
            edit_text = MOUSE_DISPLAY.get(
                key_tap(edit[i]), key_tap(edit[i]).replace("Cmd_", "").lower()
            )

        specs.append(
            {
                "base": key_tap(b),
                "hold": hold,
                "flavor": flavor,
                "accent": HOLD_ACCENT.get(hold, "mod"),
                "sym": sym_text,
                "sym_glyph": None,
                "num": num_text,
                "num_glyph": num_glyph,
                "edit": edit_text,
            }
        )
    return specs


def layer_specs(layer_value) -> list[dict]:
    specs = []
    for raw in flatten_keys(layer_value):
        hold = key_hold(raw)
        flavor = hold_flavor(key_type(raw))
        tap = key_tap(raw)
        glyph = NAV_GLYPHS.get(tap)
        specs.append(
            {
                "base": "" if glyph else tap,
                "base_glyph": glyph,
                "hold": hold,
                "flavor": flavor,
                "accent": HOLD_ACCENT.get(hold, "mod"),
                "sym": "",
                "sym_glyph": None,
                "num": "",
                "num_glyph": None,
                "edit": "",
            }
        )
    return specs


def svg_style() -> str:
    return """
    svg.keymap { background: #1e1e2e; font-family: sans-serif; }
    rect.keycap { fill: #333333; stroke: #555555; stroke-width: 0.5px; }
    text { fill: #c8c8c8; text-anchor: middle; dominant-baseline: central; }
    text.base { font-size: 16px; font-weight: 600; fill: #dddddd; }
    text.hold { font-size: 11px; }
    text.sym { font-size: 13px; fill: #9999ff; }
    text.num { font-size: 13px; fill: #ee9944; }
    text.edit { font-size: 9px; fill: #ee9944; }
    text.sticky { font-size: 12px; font-weight: 600; }
    use.glyph { fill: none; stroke: #c8c8c8; stroke-width: 2.5px;
                stroke-linecap: round; stroke-linejoin: round; }
    use.glyph.sym { stroke: #9999ff; }
    use.glyph.num { stroke: #ee9944; }
    use.glyph.base { stroke: #dddddd; }
    rect.hold-box { stroke-width: 1.2px; }
    rect.hold-box.tap-preferred.mod { fill: none; stroke: #c8c8c8; }
    rect.hold-box.tap-preferred.sym { fill: none; stroke: #9999ff; }
    rect.hold-box.tap-preferred.nav { fill: none; stroke: #ee9944; }
    rect.hold-box.tap-preferred.fun { fill: none; stroke: #ee7777; }
    rect.hold-box.hold-preferred.mod { fill: #666666; stroke: #666666; }
    rect.hold-box.hold-preferred.sym { fill: #6666bb; stroke: #6666bb; }
    rect.hold-box.hold-preferred.nav { fill: #aa7755; stroke: #aa7755; }
    rect.hold-box.hold-preferred.fun { fill: #995555; stroke: #995555; }
    rect.hold-box.sticky.mod { fill: #666666; stroke: #666666; }
    rect.hold-box.sticky.sym { fill: #6666bb; stroke: #6666bb; }
    rect.hold-box.sticky.nav { fill: #aa7755; stroke: #aa7755; }
    rect.hold-box.sticky.fun { fill: #995555; stroke: #995555; }
    text.hold.hold-preferred.mod, text.sticky.mod { fill: #eeeeee; font-weight: 700; }
    text.hold.hold-preferred.sym, text.sticky.sym,
    text.hold.hold-preferred.nav, text.sticky.nav,
    text.hold.hold-preferred.fun, text.sticky.fun { fill: #1a1a1a; font-weight: 700; }
    text.hold.tap-preferred { fill: #c8c8c8; }
    text.title { font-size: 14px; fill: #888888; text-anchor: start; }
    """.strip()


def glyph_defs() -> str:
    parts = ['<defs>']
    for name, d in GLYPH_PATHS.items():
        parts.append(
            f'<path id="glyph_{name}" class="symbol" '
            f'transform="scale(0.4) translate(-24,-30)" d="{d}"/>'
        )
    parts.append("</defs>")
    return "\n".join(parts)


def draw_key(x: float, y: float, spec: dict) -> str:
    ikw = KW - 2 * PAD
    ikh = KH - 2 * PAD
    parts = [f'<g transform="translate({x:.2f},{y:.2f})">']
    parts.append(
        f'<rect class="keycap" x="{PAD}" y="{PAD}" width="{ikw}" height="{ikh}" '
        f'rx="{RADIUS}" ry="{RADIUS}"/>'
    )

    hold = spec.get("hold") or ""
    flavor = spec.get("flavor")
    accent = spec.get("accent") or "mod"
    hold_label = HOLD_DISPLAY.get(hold, hold.lower() if hold else "")

    # Hold / sticky boxes (Selenium geometry).
    if hold and flavor == "sticky":
        parts.append(
            f'<rect class="hold-box sticky {accent}" x="{PAD}" y="{PAD}" '
            f'width="{ikw / 2}" height="{ikh}" rx="{RADIUS}" ry="{RADIUS}"/>'
        )
    elif hold and flavor in ("tap-preferred", "hold-preferred"):
        parts.append(
            f'<rect class="hold-box {flavor} {accent}" x="{PAD}" y="{PAD + ikh / 2}" '
            f'width="{ikw / 2}" height="{ikh / 2}" rx="{RADIUS}" ry="{RADIUS}"/>'
        )

    # Legend anchors (Selenium drawLabels).
    x_left = KW * 0.25
    x_right = KW * 0.75
    y_top = KH * 0.32
    y_bot = KH * 0.80

    base = spec.get("base") or ""
    base_glyph = spec.get("base_glyph")
    if flavor == "sticky" and hold:
        # Rotated label in the left bar.
        parts.append(
            f'<text class="sticky {accent}" transform="translate({PAD + ikw / 4},{KH / 2}) '
            f'rotate(-90)">{esc(hold_label)}</text>'
        )
        if base:
            # Base legend sits to the right of the sticky bar.
            parts.append(
                f'<text class="base" x="{KW * 0.72}" y="{y_top}">{esc(base)}</text>'
            )
        elif base_glyph:
            parts.append(
                f'<use class="glyph base" href="#glyph_{base_glyph}" '
                f'x="{KW * 0.72}" y="{y_top}"/>'
            )
    else:
        if base:
            parts.append(f'<text class="base" x="{x_left}" y="{y_top}">{esc(base)}</text>')
        elif base_glyph:
            parts.append(
                f'<use class="glyph base" href="#glyph_{base_glyph}" x="{x_left}" y="{y_top}"/>'
            )
        if hold and flavor:
            parts.append(
                f'<text class="hold {flavor} {accent}" x="{x_left}" y="{y_bot}">{esc(hold_label)}</text>'
            )
        elif hold:
            parts.append(f'<text class="hold" x="{x_left}" y="{y_bot}">{esc(hold_label)}</text>')

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

    # Edit shortcut in BL when no hold occupies that corner.
    edit = spec.get("edit") or ""
    if edit and not hold:
        parts.append(f'<text class="edit" x="{x_left}" y="{y_bot}">{esc(edit)}</text>')

    parts.append("</g>")
    return "\n".join(parts)


def render_board(specs: list[dict], title: str, columns: int = 5, thumbs: int = 3) -> str:
    positions = ortho_positions(columns, thumbs)
    if len(specs) != len(positions):
        raise ValueError(f"Expected {len(positions)} keys, got {len(specs)}")
    width, height = board_size(columns, thumbs)
    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" class="keymap" '
        f'width="{width:.0f}" height="{height:.0f}" viewBox="-10 -24 {width} {height}">',
        f"<style>{svg_style()}</style>",
        glyph_defs(),
        f'<text class="title" x="0" y="-8">{esc(title)}</text>',
    ]
    for spec, (x, y) in zip(specs, positions):
        body.append(draw_key(x, y, spec))
    body.append("</svg>")
    return "\n".join(body)


def _slug(name: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in name).strip("-").lower()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", type=Path, default=DEFAULT_KEYMAP)
    parser.add_argument("-o", "--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--stacked-only", action="store_true")
    parser.add_argument("--layers-only", action="store_true")
    args = parser.parse_args(argv)

    data = load_yaml(args.input)
    ortho = data.get("layout", {}).get("ortho_layout", {})
    columns = int(ortho.get("columns", 5))
    thumbs = int(ortho.get("thumbs", 3))
    args.out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    if not args.stacked_only:
        for name, value in (data.get("layers") or {}).items():
            path = args.out_dir / f"layer-{_slug(name)}.svg"
            path.write_text(
                render_board(layer_specs(value), name, columns, thumbs),
                encoding="utf-8",
            )
            written.append(path)

    if not args.layers_only:
        path = args.out_dir / "reference.svg"
        path.write_text(
            render_board(
                build_stacked_specs(data),
                "Dubu36 reference",
                columns,
                thumbs,
            ),
            encoding="utf-8",
        )
        written.append(path)

    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
