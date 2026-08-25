# Dubu36 Keyboard Layout

This repository contains my work-in-progress keyboard layout for 36-key keyboards.

The keymap is specified in firmware-independent YAML ([`keymap.yaml`](keymap.yaml)).
That file is the source of truth for:

- ZMK and QMK firmware (`python3 generate_keymap.py zmk|qmk`)
- SVG diagrams (`python3 render_keymap.py`) — per-layer boards plus a stacked reference card

```bash
pip install -r requirements.txt
make keymaps    # regenerate ZMK keymaps from keymap.yaml
make diagrams   # regenerate diagrams/*.svg (+ a .png next to each, for easy previewing)
```

Pass `--no-png` to `render_keymap.py` to skip the PNG export.

## Layout diagrams

Stacked reference card legend positions:

| Position | Content | Color |
| -------- | ------- | ----- |
| Top-left | Base (Default) tap | Grey |
| Bottom-left | Hold binding | Grey by default; purple/orange if the hold itself switches to Lower/Raise |
| Top-right | Symbols (Lower) | Purple |
| Bottom-right | Numbers / nav (Raise) | Orange |

Hold box styling (diagram `type` on a key):

| Type | Style |
| ---- | ----- |
| `tap-preferred` | Outline box in the bottom-left quadrant |
| `hold-preferred` | Solid box in the bottom-left quadrant |
| `sticky` | Solid bar covering the full left half (top-left + bottom-left), so the label reads across both quadrants |

Hold labels/boxes are grey by default (this covers plain modifiers like
Shift/Alt/Cmd/Ctrl, as well as Hyper/Adjust/Mouse). A hold that itself is a
layer-change — `Lower` or `Raise` — is colored to match that layer instead,
so it reads purple or orange like the corresponding quadrant.

![Dubu36 reference keymap](diagrams/reference.svg)

| Layer | Diagram |
| ----- | ------- |
| Default | ![Default](diagrams/layer-default.svg) |
| Raise (nav + numbers) | ![Raise](diagrams/layer-raise.svg) |
| Lower (symbols) | ![Lower](diagrams/layer-lower.svg) |
| Mouse (left-hand shortcuts) | ![Mouse](diagrams/layer-mouse.svg) |

Hyper and Adjust are omitted from the diagrams (they're rarely used
reference layers), though their mod-tap holds still show up — in the
default grey — on the layers above.

## Design notes

The default layer is Colemak, with symbols remapped toward day-to-day writing.

Modifiers used primarily in shortcuts live on the home row. Modifiers and layer
shifts used primarily in fluent writing stay on thumb keys to reduce hold-tap
timing issues.

## Keymap format

[`keymap.yaml`](keymap.yaml) is a small ortholinear keymap schema (inspired by
[keymap-drawer](https://github.com/caksoylar/keymap-drawer), but diagrams are
rendered by a custom Selenium-style SVG generator — keymap-drawer cannot express
the hold-box / sticky left-half styling).

- `layout.ortho_layout` — 3×5 split + 3 thumbs per side
- `layers` — ordered mapping; order defines firmware layer indices
- keys are either a string (`"Q"`) or `{t: Tab, h: Lower, type: hold-preferred}`
- hold `type` is diagram-only (`tap-preferred` / `hold-preferred` / `sticky`)
- `combos` — reserved for future combo definitions

Firmware-specific codes are **not** stored in the YAML. [`generate_keymap.py`](generate_keymap.py)
maps labels such as `WordL`, `Hyp_Q`, `Bt0`, and layer holds (`Raise`, `Lower`, …) to ZMK/QMK.

To edit the layout: change `keymap.yaml`, then run `make keymaps diagrams`.

## Keyboards

I use this layout on these keyboards.

### dubu36-travel

A wireless Corne build with a custom designed case that folds up and sits on top of a standard 19mm
pitch laptop keyboard (e.g. a MacBook). It can easily be used on the go and does not slide around.

![dubu36-travel picture](dubu36-travel/dubu36-travel.jpg)

Specs:

- 3x5 [Corne Keyboard](https://github.com/foostan/crkbd) PCB
- [nice!nano](https://nicekeyboards.com/nice-nano/) MCU
- [Kailh Choc](https://mkultra.click/choc-switches) Brown switches
- [NuType F1](https://nuphy.com/collections/shop/products/nutype-f1-aw20-late-summer-night-ver-keycaps)
  Keycaps
- Custom printed [travel case](dubu36-travel/case)

### dubu36-ergo

A more ergonomic dactyl style version for the desk. Due to chip shortages, it is currently wired and
running QMK instead of wireless ZMK, until I can get my hands on more nice!nano MCUs.

![dubu36-ergo](dubu36-ergo/dubu36-ergo.jpg)

Specs:

- Bastardkb's [Skeletyl](https://github.com/Bastardkb/Skeletyl) frame
- Some cheap Pro Micro MCU I had lying around
- Printed in
  [SpiderMaker Matte PLA](https://www.amazon.com/SPIDER-MAKER-Matte-Printer-Filament/dp/B07HWNK53C?th=1)
  (Iron Blue)
- Wired using Bastardkb's [flexible PCB](https://bastardkb.com/product/flexible-pcb/)
- Zeal [Zilent V2](https://zealpc.net/products/zilent?variant=5894832324646) switches
- [YMDK DSA Profile 9009](https://kbdfans.com/products/dsa-9009-keycaps-set) Keycaps
