#!/usr/bin/env python3
"""Render keymap.yaml to SVG diagrams (per-layer + stacked reference card).

Uses the keymap-drawer library/format. The stacked view places:
  - Default tap/hold in the center and bottom
  - Lower (symbols) in the top-right corner
  - Raise (numbers + nav) in the bottom-right corner
  - Hyper in the top-left corner (non-empty cells only)
"""
from __future__ import annotations

import argparse
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
STACK_CORNERS = {
    "tl": "Hyper",
    "tr": "Lower",
    "br": "Raise",
}

NAV_GLYPHS = {
    "Up": "$$mdi:arrow-up$$",
    "Down": "$$mdi:arrow-down$$",
    "Left": "$$mdi:arrow-left$$",
    "Right": "$$mdi:arrow-right$$",
    "Home": "$$mdi:arrow-collapse-left$$",
    "End": "$$mdi:arrow-collapse-right$$",
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


def as_layout_key(spec) -> LayoutKey:
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


def legend_for_corner(spec, *, use_glyphs: bool, layer_name: str) -> str:
    tap = key_tap(spec)
    if not tap:
        return ""
    if use_glyphs and tap in NAV_GLYPHS:
        return NAV_GLYPHS[tap]
    # Hyper bindings are verbose (Hyp_Q); show the base legend on the card.
    if layer_name == "Hyper" and tap.lower().startswith("hyp_"):
        return tap.split("_", 1)[1]
    return tap


def build_stacked_keys(data: dict, use_glyphs: bool = True) -> list[LayoutKey]:
    layers = data["layers"]
    if STACK_CENTER not in layers:
        raise KeyError(f"Missing center layer {STACK_CENTER!r}")

    center_keys = flatten_keys(layers[STACK_CENTER])
    corner_keys = {
        corner: (name, flatten_keys(layers[name])) if name in layers else (name, [])
        for corner, name in STACK_CORNERS.items()
    }

    stacked: list[LayoutKey] = []
    for i, center in enumerate(center_keys):
        key = as_layout_key(center)
        fields = {"tap": key.tap, "hold": key.hold}
        for corner, (layer_name, keys) in corner_keys.items():
            if i < len(keys):
                legend = legend_for_corner(
                    keys[i], use_glyphs=use_glyphs, layer_name=layer_name
                )
                if legend:
                    fields[corner] = legend
        if not any(fields.values()):
            stacked.append(LayoutKey(type="trans"))
        else:
            stacked.append(LayoutKey(**fields))
    return stacked


def make_config(data: dict) -> Config:
    config = Config()
    draw_overrides = dict(data.get("draw_config") or {})
    # dark_mode + footer always on for this repo's diagrams
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
    out_path.write_text(buf.getvalue(), encoding="utf-8")


def _slug(name: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in name).strip("-").lower()


def draw_layers(data: dict, out_dir: Path) -> list[Path]:
    config = make_config(data)
    layout = make_layout(config, data)
    written = []
    for name, value in (data.get("layers") or {}).items():
        keys = [as_layout_key(k) for k in flatten_keys(value)]
        path = out_dir / f"layer-{_slug(name)}.svg"
        draw_board(config, layout, {name: keys}, path)
        written.append(path)
    return written


def draw_stacked(data: dict, out_dir: Path) -> Path:
    config = make_config(data)
    extra = config.draw_config.svg_extra_style or ""
    stacked_style = """
text.tr, use.tr { fill: #cba6f7; }
text.br, use.br { fill: #fab387; }
text.tl, use.tl { fill: #f38ba8; }
text.hold { fill: #a6adc8; }
rect.key { fill: #313244; stroke: #45475a; }
"""
    config.draw_config = config.draw_config.model_copy(
        update={
            "svg_extra_style": extra + "\n" + stacked_style,
            "footer_text": "Dubu36 reference",
        }
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
