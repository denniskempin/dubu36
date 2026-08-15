#!/usr/bin/env python3
"""Render keymap.yaml to SVG diagrams (per-layer + stacked reference card).

Visual conventions (matching the Dubu36 reference card):
  - Primary tap legend top-left; hold binding boxed in the key center
  - Outline box = tap-preferred, solid box = hold-preferred, large box = sticky
  - Stacked card: Lower → top-right (purple), Raise → bottom-right (orange),
    Mouse → bottom-left (orange)
"""
from __future__ import annotations

import argparse
import re
import sys
from io import StringIO
from pathlib import Path

import yaml
from keymap_drawer.config import Config
from keymap_drawer.draw import KeymapDrawer
from keymap_drawer.keymap import LayoutKey
from keymap_drawer.physical_layout import PhysicalLayoutGenerator

ROOT = Path(__file__).resolve().parent
DEFAULT_KEYMAP = ROOT / "keymap.yaml"
DEFAULT_OUT = ROOT / "diagrams"

STACK_CENTER = "Default"
STACK_TR = "Lower"
STACK_BR = "Raise"
STACK_BL = "Mouse"

HOLD_BOX_TYPES = frozenset({"tap-preferred", "hold-preferred", "sticky"})

# Compact legends inside mod boxes (reference-card style).
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

LAYER_THUMB_CLASS = {
    "Raise": "thumb-raise",
    "Lower": "thumb-lower",
    "Hyper": "thumb-hyper",
    "Adjust": "thumb-adjust",
    "Mouse": "thumb-mouse",
}

NAV_GLYPHS = {
    "Up": "$$mdi:arrow-up$$",
    "Down": "$$mdi:arrow-down$$",
    "Left": "$$mdi:arrow-left$$",
    "Right": "$$mdi:arrow-right$$",
    "Home": "$$mdi:arrow-collapse-left$$",
    "End": "$$mdi:arrow-collapse-right$$",
    "WordL": "$$mdi:arrow-left-bold-outline$$",
    "WordR": "$$mdi:arrow-right-bold-outline$$",
}

# Mouse-layer legends → edit-action style labels on the stacked card.
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

# Box geometry centered on the key origin (where tap text is drawn).
BOX_SIZE = {
    "tap-preferred": (34, 15),
    "hold-preferred": (34, 15),
    "sticky": (46, 20),
}


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def key_tap(spec) -> str:
    if spec is None:
        return ""
    if isinstance(spec, str):
        return spec
    return str(spec.get("t", spec.get("tap", spec.get("center", ""))) or "")


def key_hold(spec) -> str:
    if not isinstance(spec, dict):
        return ""
    return str(spec.get("h", spec.get("hold", spec.get("bottom", ""))) or "")


def key_type(spec) -> str:
    if not isinstance(spec, dict):
        return ""
    return str(spec.get("type", "") or "")


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


def hold_box_type(type_str: str) -> str | None:
    for token in type_str.split():
        if token in HOLD_BOX_TYPES:
            return token
    return None


def display_hold(hold: str) -> str:
    return HOLD_DISPLAY.get(hold, hold)


def compose_type(*parts: str) -> str:
    tokens: list[str] = []
    for part in parts:
        for token in part.split():
            if token and token not in tokens:
                tokens.append(token)
    return " ".join(tokens)


def as_raw_layout_key(spec) -> LayoutKey:
    """Parse YAML key spec without visual transforms."""
    if isinstance(spec, LayoutKey):
        return spec
    if spec is None or spec == "":
        return LayoutKey(type="trans")
    if isinstance(spec, str):
        return LayoutKey(tap=spec)
    tap = str(spec.get("t", spec.get("tap", "")) or "")
    hold = str(spec.get("h", spec.get("hold", "")) or "")
    shifted = str(spec.get("s", spec.get("shifted", "")) or "")
    left = str(spec.get("left", "") or "")
    right = str(spec.get("right", "") or "")
    tl = str(spec.get("tl", "") or "")
    tr = str(spec.get("tr", "") or "")
    bl = str(spec.get("bl", "") or "")
    br = str(spec.get("br", "") or "")
    type_ = str(spec.get("type", "") or "")
    if not any((tap, hold, shifted, left, right, tl, tr, bl, br)):
        return LayoutKey(type="trans")
    return LayoutKey(
        tap=tap,
        hold=hold,
        shifted=shifted,
        left=left,
        right=right,
        tl=tl,
        tr=tr,
        bl=bl,
        br=br,
        type=type_,
    )


def for_display(spec, *, key_index: int | None = None, thumb_start: int = 30) -> LayoutKey:
    """Place hold in the center with a preference box; move tap to top-left."""
    raw = as_raw_layout_key(spec)
    if raw.type == "trans" and not any(
        (raw.tap, raw.hold, raw.shifted, raw.left, raw.right, raw.tl, raw.tr, raw.bl, raw.br)
    ):
        return raw

    box = hold_box_type(raw.type)
    hold = raw.hold
    tap = raw.tap
    type_ = raw.type
    on_thumb = key_index is not None and key_index >= thumb_start

    if hold and box:
        # Only tint actual thumb-cluster keys for layer activators.
        thumb = LAYER_THUMB_CLASS.get(hold, "") if on_thumb else ""
        type_ = compose_type(type_, thumb)
        if tap:
            return LayoutKey(
                tap=display_hold(hold),
                tl=tap,
                tr=raw.tr,
                bl=raw.bl,
                br=raw.br,
                left=raw.left,
                right=raw.right,
                shifted=raw.shifted,
                type=type_,
            )
        return LayoutKey(
            tap=display_hold(hold),
            tr=raw.tr,
            bl=raw.bl,
            br=raw.br,
            left=raw.left,
            right=raw.right,
            shifted=raw.shifted,
            type=type_,
        )

    if hold and not box:
        # Untyped hold: keep keymap-drawer default (tap center, hold bottom).
        return LayoutKey(
            tap=tap,
            hold=display_hold(hold),
            shifted=raw.shifted,
            left=raw.left,
            right=raw.right,
            tl=raw.tl,
            tr=raw.tr,
            bl=raw.bl,
            br=raw.br,
            type=type_,
        )

    return raw


def legend_for_layer(spec, *, layer_name: str, use_glyphs: bool) -> str:
    tap = key_tap(spec)
    if not tap:
        return ""
    if layer_name == "Mouse":
        return MOUSE_DISPLAY.get(tap, tap.replace("Cmd_", "").lower())
    if layer_name == "Hyper" and tap.lower().startswith("hyp_"):
        return tap.split("_", 1)[1]
    if use_glyphs and tap in NAV_GLYPHS:
        return NAV_GLYPHS[tap]
    return tap


def build_stacked_keys(data: dict, use_glyphs: bool = True) -> list[LayoutKey]:
    layers = data["layers"]
    if STACK_CENTER not in layers:
        raise KeyError(f"Missing center layer {STACK_CENTER!r}")

    layout = data.get("layout", {}).get("ortho_layout", {})
    columns = int(layout.get("columns", 5))
    thumbs = int(layout.get("thumbs", 3))
    thumb_start = columns * 2 * 3

    center_keys = flatten_keys(layers[STACK_CENTER])
    tr_keys = flatten_keys(layers.get(STACK_TR, []))
    br_keys = flatten_keys(layers.get(STACK_BR, []))
    bl_keys = flatten_keys(layers.get(STACK_BL, []))

    stacked: list[LayoutKey] = []
    for i, center in enumerate(center_keys):
        key = for_display(center, key_index=i, thumb_start=thumb_start)
        fields = {
            "tap": key.tap,
            "hold": key.hold,
            "tl": key.tl,
            "tr": key.tr,
            "bl": key.bl,
            "br": key.br,
            "left": key.left,
            "right": key.right,
            "shifted": key.shifted,
            "type": key.type,
        }
        if i < len(tr_keys):
            legend = legend_for_layer(tr_keys[i], layer_name=STACK_TR, use_glyphs=use_glyphs)
            if legend:
                fields["tr"] = legend
        if i < len(br_keys):
            legend = legend_for_layer(br_keys[i], layer_name=STACK_BR, use_glyphs=use_glyphs)
            if legend:
                fields["br"] = legend
        if i < len(bl_keys):
            legend = legend_for_layer(bl_keys[i], layer_name=STACK_BL, use_glyphs=use_glyphs)
            if legend:
                fields["bl"] = legend

        if not any(v for k, v in fields.items() if k != "type" and v):
            stacked.append(LayoutKey(type="trans"))
        else:
            stacked.append(LayoutKey(**fields))
    return stacked


def make_config(data: dict) -> Config:
    config = Config()
    draw_overrides = dict(data.get("draw_config") or {})
    draw_overrides.setdefault("dark_mode", True)
    draw_overrides.setdefault("n_columns", 1)
    draw_overrides.setdefault("footer_text", "Dubu36")
    if draw_overrides:
        config.draw_config = config.draw_config.model_copy(update=draw_overrides)
    return config


def make_layout(config: Config, data: dict):
    layout_cfg = data.get("layout") or {}
    return PhysicalLayoutGenerator(
        config=config,
        ortho_layout=layout_cfg.get("ortho_layout"),
        qmk_keyboard=layout_cfg.get("qmk_keyboard"),
        zmk_keyboard=layout_cfg.get("zmk_keyboard"),
        cols_thumbs_notation=layout_cfg.get("cols_thumbs_notation"),
        layout_name=layout_cfg.get("layout_name"),
    ).generate()


def inject_mod_boxes(svg: str) -> str:
    """Insert rounded rects behind center legends for tap/hold preference types."""

    def repl(match: re.Match[str]) -> str:
        g_open = match.group("open")
        body = match.group("body")
        box = hold_box_type(g_open)
        if not box:
            return match.group(0)
        # Only box keys that still have a center tap legend.
        if not re.search(r'class="[^"]*\btap\b', body):
            return match.group(0)
        if "mod-box" in body:
            return match.group(0)
        w, h = BOX_SIZE[box]
        rect = (
            f'<rect class="mod-box {box}" x="{-w / 2}" y="{-h / 2}" '
            f'width="{w}" height="{h}"/>\n'
        )
        # Place the box after the keycap rect, before legends.
        body_with_box = re.sub(
            r'(<rect\b[^>]*class="key[^"]*"[^>]*/>\n)',
            r"\1" + rect,
            body,
            count=1,
        )
        return f"{g_open}{body_with_box}</g>"

    # Non-greedy per top-level key group.
    pattern = re.compile(
        r"(?P<open><g\b[^>]*\bclass=\"key[^\"]*\"[^>]*>)(?P<body>.*?)</g>",
        re.DOTALL,
    )
    return pattern.sub(repl, svg)


def draw_board(config: Config, layout, layers: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    buf = StringIO()
    drawer = KeymapDrawer(
        config=config,
        out=buf,
        layers=layers,
        layout=layout,
        combos=[],
    )
    drawer.print_board()
    svg = inject_mod_boxes(buf.getvalue())
    out_path.write_text(svg, encoding="utf-8")


def _slug(name: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in name).strip("-").lower()


def draw_layers(data: dict, out_dir: Path) -> list[Path]:
    config = make_config(data)
    layout = make_layout(config, data)
    ortho = data.get("layout", {}).get("ortho_layout", {})
    thumb_start = int(ortho.get("columns", 5)) * 2 * 3
    written = []
    for name, value in (data.get("layers") or {}).items():
        keys = [
            for_display(k, key_index=i, thumb_start=thumb_start)
            for i, k in enumerate(flatten_keys(value))
        ]
        path = out_dir / f"layer-{_slug(name)}.svg"
        draw_board(config, layout, {name: keys}, path)
        written.append(path)
    return written


def draw_stacked(data: dict, out_dir: Path) -> Path:
    config = make_config(data)
    config.draw_config = config.draw_config.model_copy(
        update={"footer_text": "Dubu36 reference"}
    )
    layout = make_layout(config, data)
    path = out_dir / "reference.svg"
    draw_board(config, layout, {"Reference": build_stacked_keys(data)}, path)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", type=Path, default=DEFAULT_KEYMAP)
    parser.add_argument("-o", "--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--stacked-only", action="store_true")
    parser.add_argument("--layers-only", action="store_true")
    args = parser.parse_args(argv)

    data = load_yaml(args.input)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    if not args.stacked_only:
        written.extend(draw_layers(data, args.out_dir))
    if not args.layers_only:
        written.append(draw_stacked(data, args.out_dir))

    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
