"""Map parsed keys to QMK keycodes."""

from __future__ import annotations

from pathlib import Path

from keymap_generator.codes import KEY_PRESS_CODES, LAYER_LABELS, SPECIAL_LABELS
from keymap_generator.generate import generate_keymap
from keymap_generator.parser import Combo, Key, Layer, find_key_position

# QMK sizes its combo table with the compile time COMBO_COUNT, so the generated
# table always has this many entries and any spare slot is filled with a combo
# that cannot fire. Must match COMBO_COUNT in dubu36-ergo/qmk/dubu36ergo/config.h.
COMBO_SLOTS = 5


def get_qmk_key_press_code(label: str) -> str | None:
    if label.startswith("SHFT_"):
        return f"S({get_qmk_key_press_code(label.removeprefix('SHFT_'))})"
    if label.startswith("CMD_"):
        return f"G({get_qmk_key_press_code(label[4:])})"
    if label.startswith("HYP_"):
        return f"G(S(A(C({get_qmk_key_press_code(label[4:])}))))"
    if len(label) == 1 and (label.isalpha() or label.isdigit()):
        return f"KC_{label}"
    if label in KEY_PRESS_CODES:
        return KEY_PRESS_CODES[label].qmk
    return None


def qmk_mod_code(label: str) -> str:
    """`MOD_RGUI` for a modifier label such as `RGUI`."""
    code = get_qmk_key_press_code(label)
    if not code or not code.startswith("KC_"):
        raise KeyError(f"Cannot hold {label} as a QMK modifier.")
    return code.replace("KC_", "MOD_", 1)


def apply_layer_mods(text: str, layers: list[Layer]) -> str:
    """Fill `#LAYER_MODS#` so a layer hold also holds its declared modifier.

    QMK's `LT(layer, kc)` activates the layer and cannot hold a modifier at
    the same time. The generated function registers the modifier when that
    layer-tap is a hold, and counts overlapping holds of the same modifier.
    """
    counters: dict[str, str] = {}
    cases: list[str] = []
    for index, layer in enumerate(layers):
        if not layer.modifier:
            continue
        mod = qmk_mod_code(layer.modifier)
        counter = "holds_" + mod.removeprefix("MOD_").lower()
        counters[mod] = counter
        cases.append(
            "\n".join(
                [
                    f"    case {index}:",
                    f"        counted_mod(&{counter}, {mod}, record->event.pressed);",
                    "        break;",
                ]
            )
        )
    if not cases:
        body = "\n".join(
            [
                "static void process_layer_mod("
                "uint16_t keycode, keyrecord_t *record) {",
                "    (void)keycode;",
                "    (void)record;",
                "}",
            ]
        )
        return text.replace("#LAYER_MODS#", body)
    declarations = "\n".join(f"static uint8_t {name};" for name in counters.values())
    body = "\n".join(
        [
            declarations,
            "",
            "static void counted_mod(uint8_t *holds, uint8_t mod, bool pressed) {",
            "    if (pressed) {",
            "        if ((*holds)++ == 0) {",
            "            register_mods(mod);",
            "        }",
            "    } else if (*holds > 0 && --(*holds) == 0) {",
            "        unregister_mods(mod);",
            "    }",
            "}",
            "",
            "static void process_layer_mod(uint16_t keycode, keyrecord_t *record) {",
            "    if ((keycode & 0xF000) != QK_LAYER_TAP || record->tap.count) {",
            "        return;",
            "    }",
            "    switch ((keycode >> 8) & 0x0F) {",
            *cases,
            "    default:",
            "        break;",
            "    }",
            "}",
        ]
    )
    return text.replace("#LAYER_MODS#", body)


def generate_qmk_keymap(
    layers: list[Layer],
    combos: list[Combo],
    template_path: str | Path,
) -> str:
    """Fill the QMK template, including layer-modifier holds."""
    text = generate_keymap(
        layers,
        combos,
        template_path,
        generate_qmk_layer,
        generate_qmk_combos,
    )
    return apply_layer_mods(text, layers)


def map_key_label_to_qmk(label: str) -> str:
    code = get_qmk_key_press_code(label)
    if code:
        return code
    if label in LAYER_LABELS:
        return f"MO({LAYER_LABELS[label]})"
    if label in SPECIAL_LABELS:
        return SPECIAL_LABELS[label].qmk
    if not label:
        return "KC_NO"
    raise KeyError(f"Cannot map label {label} to qmk.")


def map_key_to_qmk(key: Key) -> str:
    if not key.hold:
        return map_key_label_to_qmk(key.tap)
    if not key.tap:
        return map_key_label_to_qmk(key.hold)

    # QMK has no per-key hold-tap flavors, so they are ignored here. OSM/OSL are
    # one-shot on tap and a plain modifier or layer shift when held.
    if key.hold in LAYER_LABELS:
        if key.is_oneshot:
            return f"OSL({LAYER_LABELS[key.hold]})"
        tap_code = get_qmk_key_press_code(key.tap)
        if tap_code:
            return f"LT({LAYER_LABELS[key.hold]},{tap_code})"
    else:
        # Fn is the Apple Globe key, a consumer usage, so MT() cannot hold
        # it. LT(0, kc) is the stand-in the template turns into "tap kc,
        # hold Fn".
        if key.hold == "FN" and not key.is_oneshot:
            tap_code = get_qmk_key_press_code(key.tap)
            if tap_code:
                return f"LT(0,{tap_code})"
        hold_code = get_qmk_key_press_code(key.hold)
        if hold_code:
            hold_code = hold_code.replace("KC_", "MOD_")
            if key.is_oneshot:
                return f"OSM({hold_code})"
            tap_code = get_qmk_key_press_code(key.tap)
            if tap_code:
                return f"MT({hold_code},{tap_code})"
    raise KeyError(f"Cannot map hold-tap key ({key.tap}, {key.hold}) to qmk.")


def generate_qmk_combo_trigger(combo: Combo | None, default_layer: Layer) -> str:
    """The keys a combo waits for, as QMK matches them.

    QMK compares a combo against the keycode the keymap holds, not the key press
    it eventually produces, so a home-row trigger has to be named by its whole
    mod-tap keycode. Naming it `KC_S` would leave the combo unable to ever fire.
    """
    if not combo:
        return "KC_NO"
    return ", ".join(
        map_key_to_qmk(default_layer.rows[y][x])
        for y, x in (
            find_key_position(default_layer, label) for label in (combo.a, combo.b)
        )
    )


def generate_qmk_combos(combos: list[Combo], default_layer: Layer) -> str:
    """Render the combo table, padded out to the slots COMBO_COUNT promises."""
    slots = [combos[i] if i < len(combos) else None for i in range(COMBO_SLOTS)]
    triggers = "\n".join(
        f"const uint16_t PROGMEM combo{i}[] = "
        f"{{{generate_qmk_combo_trigger(combo, default_layer)}, COMBO_END}};"
        for i, combo in enumerate(slots)
    )
    entries = ",\n".join(
        f"\tCOMBO(combo{i}, {map_key_label_to_qmk(combo.result) if combo else 'KC_NO'})"
        for i, combo in enumerate(slots)
    )
    return f"{triggers}\n\ncombo_t key_combos[COMBO_COUNT] = {{\n{entries}\n}};"


def generate_qmk_layer(layer: Layer) -> str:
    return ",\n".join(
        ", ".join(map_key_to_qmk(key) for key in row) for row in layer.rows
    )
