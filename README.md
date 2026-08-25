# Dubu36 Keyboard Layout

This repository contains my work-in-progress keyboard layout for 36 key keyboards.

The keyboard layout is specified in [`keymap.txt`](keymap.txt), and converted into ZMK and QMK
keymaps using the `generate_keymap.py` script.

## Keymap

Each layer is a grid of the 36 keys, laid out the way they sit on the keyboard: three rows of ten
keys, then the six thumb keys. Every whitespace separated cell is one key:

```
layer default: homerow
  Q      W     F     P     G           J     L     U     Y     *
  A      R     S     T     D           H     N     E     I     O
  Z/adj  X     C     V     B           K     M     ,     .     '/adj
                ESC/mou  _/shft  TAB/lwr   RET  SPC/rse  BKSP/hyp
```

A cell is either a label, or a `TAP/HOLD` pair for keys that do something else when held, such as
`Z/adj` which types a `Z` when tapped and shifts to the adjust layer while held. `_` marks a key
that does nothing, and a `:FLAVOR` suffix picks the hold-tap flavor to use for that key:

```
  T/cmd:hp     hold-preferred instead of the default tap-preferred
  shft/shft    a sticky shift when tapped, a plain shift when held
```

Holds shared by several layers are written once as an `overlay`, which a layer picks up by listing
it after its name, as `homerow` is listed above. This is how the home-row modifiers are shared
between layers without repeating them; a cell can still define its own hold to override the
inherited one, or use `/_` to drop it.

The default layer is Colemak, with special characters remapped to prioritize commonly used
characters in day-to-day writing. Holding a key on the home-row gives the modifiers used in
shortcuts; the modifiers and layer shifts used in fluent writing sit on the thumbs instead, to
reduce issues with hold-tap timing. The remaining layers cover navigation and numbers, symbols,
window management, bluetooth, and left hand only shortcuts for when the right hand is on the mouse.

## Keyboards

I use this layout on these keyboards

### dubu36-travel

A wireless corne build with a custom designed case that folds up and sits on top of a standard 19mm
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
