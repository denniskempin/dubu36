"""Map parsed keys to QMK keycodes."""

from __future__ import annotations

from keymap_generator.codes import KEY_PRESS_CODES, LAYER_LABELS, SPECIAL_LABELS
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


def qmk_instant_hold_name(key: Key) -> str:
    """C identifier for an instant-hold key, shared by the keymap and the handler.

    Derived from the tap and hold keycodes so two cells with the same pair
    name the same slot. A duplicate pair cannot be held independently.
    """
    hold_label = key.hold
    if not hold_label:
        raise KeyError(f"Cannot map instant-hold key ({key.tap}, {key.hold}) to qmk.")
    tap = get_qmk_key_press_code(key.tap)
    hold = get_qmk_key_press_code(hold_label)
    if not tap or not hold:
        raise KeyError(f"Cannot map instant-hold key ({key.tap}, {key.hold}) to qmk.")

    def ident(code: str) -> str:
        code = code.removeprefix("KC_")
        return "".join(ch if ch.isalnum() else "_" for ch in code)

    return f"IH_{ident(tap)}_{ident(hold)}"


def instant_hold_entries(layers: list[Layer]) -> list[tuple[str, str, str]]:
    """Each instant-hold key as `(c_name, hold_keycode, tap_keycode)`, in order."""
    entries: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for layer in layers:
        for row in layer.rows:
            for key in row:
                if key.flavor != "ih":
                    continue
                name = qmk_instant_hold_name(key)
                if name in seen:
                    raise KeyError(
                        f"instant-hold pair ({key.tap}, {key.hold}) is used twice; "
                        "the two keys would share one timer"
                    )
                seen.add(name)
                hold_label = key.hold or ""
                hold = get_qmk_key_press_code(hold_label)
                tap = get_qmk_key_press_code(key.tap)
                if not hold or not tap:
                    raise KeyError(
                        f"Cannot map instant-hold key ({key.tap}, {key.hold}) to qmk."
                    )
                entries.append((name, hold, tap))
    return entries


def generate_qmk_instant_holds(layers: list[Layer]) -> str:
    """The custom keycodes and handler for `ih` keys, or nothing if there are none.

    QMK's `MT()` waits to decide and only accepts a modifier, so F18/F19 use
    a handler: the hold key goes down on press, and a release inside
    `TAPPING_TERM` releases it and then taps the key. Other keys are not
    queued, so a shortcut sees the function key immediately.
    """
    entries = instant_hold_entries(layers)
    if not entries:
        return ""
    enum_lines = [
        f"\t{name} = SAFE_RANGE," if i == 0 else f"\t{name},"
        for i, (name, _, _) in enumerate(entries)
    ]
    table_lines = [
        f"\t[{name} - {entries[0][0]}] = {{{hold}, {tap}, 0, false}},"
        for name, hold, tap in entries
    ]
    first = entries[0][0]
    count = len(entries)
    return "\n".join(
        [
            "enum instant_hold_keycodes {",
            *enum_lines,
            "};",
            "",
            "typedef struct {",
            "\tuint16_t hold;",
            "\tuint16_t tap;",
            "\tuint16_t pressed_at;",
            "\tbool down;",
            "} instant_hold_t;",
            "",
            f"static instant_hold_t instant_holds[{count}] = {{",
            *table_lines,
            "};",
            "",
            "static uint8_t instant_hold_holders(uint16_t hold) {",
            "\tuint8_t count = 0;",
            f"\tfor (uint8_t i = 0; i < {count}; i++) {{",
            "\t\tif (instant_holds[i].down && instant_holds[i].hold == hold) {",
            "\t\t\tcount++;",
            "\t\t}",
            "\t}",
            "\treturn count;",
            "}",
            "",
            "bool process_record_user(uint16_t keycode, keyrecord_t *record) {",
            f"\tif (keycode < {first} || keycode >= {first} + {count}) {{",
            "\t\treturn true;",
            "\t}",
            f"\tinstant_hold_t *slot = &instant_holds[keycode - {first}];",
            "\tif (record->event.pressed) {",
            "\t\tif (instant_hold_holders(slot->hold) == 0) {",
            "\t\t\tregister_code16(slot->hold);",
            "\t\t}",
            "\t\tslot->down = true;",
            "\t\tslot->pressed_at = timer_read();",
            "\t} else {",
            "\t\tbool quick = timer_elapsed(slot->pressed_at) < TAPPING_TERM;",
            "\t\tslot->down = false;",
            "\t\tuint8_t rest = instant_hold_holders(slot->hold);",
            "\t\tif (quick) {",
            "\t\t\tunregister_code16(slot->hold);",
            "\t\t\ttap_code16(slot->tap);",
            "\t\t\tif (rest > 0) {",
            "\t\t\t\tregister_code16(slot->hold);",
            "\t\t\t}",
            "\t\t} else if (rest == 0) {",
            "\t\t\tunregister_code16(slot->hold);",
            "\t\t}",
            "\t}",
            "\treturn false;",
            "}",
            "",
        ]
    )


def map_key_to_qmk(key: Key) -> str:
    if not key.hold:
        return map_key_label_to_qmk(key.tap)
    if not key.tap:
        return map_key_label_to_qmk(key.hold)

    if key.flavor == "ih":
        return qmk_instant_hold_name(key)

    # QMK has no per-key hold-tap flavors, so they are ignored here. OSM/OSL are
    # one-shot on tap and a plain modifier or layer shift when held.
    if key.hold in LAYER_LABELS:
        if key.is_oneshot:
            return f"OSL({LAYER_LABELS[key.hold]})"
        tap_code = get_qmk_key_press_code(key.tap)
        if tap_code:
            return f"LT({LAYER_LABELS[key.hold]},{tap_code})"
    else:
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
