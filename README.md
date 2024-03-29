# Dubu36 Keyboard Layout

This repository contains my work-in-progress keyboard layout for 36 key keyboards.

The keyboard layout is specified in markdown below, and converted into ZMK and QMK keymaps using the
`generate_keymaps.py` script.

## Default Layer

The default layer is Colemak. With special characters remapped to prioritize commonly used
characters in day-to-day writing.

|     |     |     |     |     |     |     |     |      |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ---- | --- | --- |
| Q   | W   | F   | P   | G   |     | J   | L   | U    | Y   | \*  |
| A   | R   | S   | T   | D   |     | H   | N   | E    | I   | O   |
| Z   | X   | C   | V   | B   |     | K   | M   | ,    | .   | '   |
|     |     | ESC | ☐   | TAB |     | RET | SPC | BKSP |     |     |

### Default Layer Hold

Modifiers used primarily in shortcuts have been mapped to the home-row. The modifiers and layer
shifts used primarily in fluent writing remain on thumb keys to reduce issues hold-tap timing.

|     |      |     |      |      |     |      |     |     |      |     |
| --- | ---- | --- | ---- | ---- | --- | ---- | --- | --- | ---- | --- |
| ☐   | ☐    | ☐   | ☐    | ☐    |     | ☐    | ☐   | ☐   | ☐    | ☐   |
| hyp | shft | alt | cmd  | ctrl |     | ctrl | cmd | alt | shft | hyp |
| adj | ☐    | ☐   | ☐    | ☐    |     | ☐    | ☐   | ☐   | ☐    | adj |
|     |      | mou | shft | lwr  |     | ☐    | rse | hyp |      |     |

### Default Layer (Combos)

|     |     |     |     |
| --- | --- | --- | --- |

## Raise Layer (Navigation + Numbers)

|     |     |     |     |     |     |       |        |        |        |       |
| --- | --- | --- | --- | --- | --- | ----- | ------ | ------ | ------ | ----- |
| ☐   | 7   | 8   | 9   | ☐   |     | HOME  | WORD_L | UP     | WORD_R | END   |
| ☐   | 4   | 5   | 6   | ☐   |     | FWD   | LEFT   | DOWN   | RIGHT  | BCK   |
| 0   | 1   | 2   | 3   | ☐   |     | TAB_L | HYP\_[ | HYP\_\ | HYP\_] | TAB_R |
|     |     | ☐   | ☐   | ☐   |     | ☐     | ☐      | ☐      |        |       |

## Raise Layer Hold

|     |      |     |     |      |     |      |     |     |      |     |
| --- | ---- | --- | --- | ---- | --- | ---- | --- | --- | ---- | --- |
| ☐   | ☐    | ☐   | ☐   | ☐    |     | ☐    | ☐   | ☐   | ☐    | ☐   |
| hyp | shft | alt | cmd | ctrl |     | ctrl | cmd | alt | shft | hyp |
| ☐   | ☐    | ☐   | ☐   | ☐    |     | ☐    | ☐   | ☐   | ☐    | ☐   |
|     |      | ☐   | ☐   | ☐    |     | ☐    | ☐   | ☐   |      |     |

## Lower Layer (Symbols)

|     |     |     |     |     |     |     |     |          |      |     |
| --- | --- | --- | --- | --- | --- | --- | --- | -------- | ---- | --- |
| ~   | ^   | @   | $   | %   |     | &   | /   | \        | PIPE | `   |
| UML | <   | [   | (   | {   |     | -   | \_  | :        | ;    | #   |
| ☐   | >   | ]   | )   | }   |     | +   | =   | ?        | !    | "   |
|     |     | ☐   | ☐   | ☐   |     | ☐   | ☐   | ALT_BKSP |      |     |

## Lower Layer Hold

|     |      |     |     |      |     |      |     |     |      |     |
| --- | ---- | --- | --- | ---- | --- | ---- | --- | --- | ---- | --- |
| ☐   | ☐    | ☐   | ☐   | ☐    |     | ☐    | ☐   | ☐   | ☐    | ☐   |
| hyp | shft | alt | cmd | ctrl |     | ctrl | cmd | alt | shft | hyp |
| ☐   | ☐    | ☐   | ☐   | ☐    |     | ☐    | ☐   | ☐   | ☐    | ☐   |
|     |      | ☐   | ☐   | ☐    |     | ☐    | ☐   | ☐   |      |     |

## Hyper Layer

|       |       |         |       |         |     |         |          |          |           |       |
| ----- | ----- | ------- | ----- | ------- | --- | ------- | -------- | -------- | --------- | ----- |
| HYP_Q | HYP_W | HYP_F   | HYP_P | HYP_G   |     | HYP_1   | HYP_2    | HYP_3    | HYP_4     | HYP_5 |
| HYP_A | HYP_R | HYP_S   | HYP_T | HYP_D   |     | ☐       | HYP_LEFT | HYP_UP   | HYP_RIGHT | ☐     |
| HYP_Z | HYP_X | HYP_C   | HYP_V | HYP_B   |     | ☐       | HYP\_;   | HYP_DOWN | HYP\_'    | ☐     |
|       |       | HYP_ESC | ☐     | HYP_TAB |     | HYP_RET | HYP_SPC  | HYP_BKSP |           |       |

## Adjust Layer (Bluetooth)

|        |      |      |     |     |     |     |     |     |     |     |
| ------ | ---- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
| BT_0   | BT_1 | BT_2 | ☐   | ☐   |     | ☐   | ☐   | ☐   | ☐   | ☐   |
| BT_CLR | ☐    | ☐    | ☐   | ☐   |     | ☐   | ☐   | ☐   | ☐   | ☐   |
| ☐      | ☐    | ☐    | ☐   | ☐   |     | ☐   | ☐   | ☐   | ☐   | ☐   |
|        |      | ☐    | ☐   | ☐   |     | ☐   | ☐   | ☐   |     |     |

## Mouse Layer (Left hand only keyboard shortcuts)

|       |       |       |       |     |     |     |     |     |     |     |
| ----- | ----- | ----- | ----- | --- | --- | --- | --- | --- | --- | --- |
| CMD_Q | CMD_W | ☐     | ☐     | ☐   |     | ☐   | ☐   | ☐   | ☐   | ☐   |
| ☐     | ☐     | CMD_S | CMD_T | ☐   |     | ☐   | ☐   | ☐   | ☐   | ☐   |
| CMD_Z | CMD_X | CMD_C | CMD_V | ☐   |     | ☐   | ☐   | ☐   | ☐   | ☐   |
|       |       | ☐     | ☐     | ☐   |     | ☐   | ☐   | ☐   |     |     |

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
