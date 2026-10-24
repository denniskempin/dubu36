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


# Characters that cannot sit in a C identifier, spelled out so F18_, becomes
# FN_F18_COMMA. Anything else in an F18_/F19_ label is a generator bug.
_FN_SLUG = {
    ",": "COMMA",
    ".": "DOT",
    "'": "SQT",
    "*": "STAR",
    "/": "SLASH",
    "\\": "BSLH",
    ";": "SEMI",
    "-": "MINUS",
    "=": "EQUAL",
    "[": "LBKT",
    "]": "RBKT",
    "`": "GRAVE",
}

# F18_ and F19_ chord a function key with another key. QMK has no keycode for
# that, so each label becomes a custom keycode the template's
# process_record_user sends as the pair.
_FN_KEYS = (("F18_", "KC_F18"), ("F19_", "KC_F19"))


def fn_enum_name(label: str) -> str:
    """C identifier for an F18_/F19_ chord label, such as `FN_F18_Q`."""
    parts: list[str] = []
    for char in label:
        if char.isalnum() or char == "_":
            parts.append(char)
        elif char in _FN_SLUG:
            parts.append(_FN_SLUG[char])
        else:
            raise KeyError(f"Cannot name a QMK chord for {label!r}.")
    return "FN_" + "".join(parts)


def fn_chord(label: str) -> tuple[str, str, str] | None:
    """`(enum name, function key, inner key)` for an F18_/F19_ label."""
    for prefix, function_key in _FN_KEYS:
        if not label.startswith(prefix):
            continue
        inner = get_qmk_key_press_code(label.removeprefix(prefix))
        if inner is None:
            return None
        return fn_enum_name(label), function_key, inner
    return None


def fn_labels(layers: list[Layer]) -> list[str]:
    """Every F18_/F19_ label used in `layers`, in a stable order."""
    found: set[str] = set()
    for layer in layers:
        for row in layer.rows:
            for key in row:
                for label in (key.tap, key.hold or ""):
                    if fn_chord(label):
                        found.add(label)
    return sorted(found)


def apply_fn_chords(text: str, layers: list[Layer]) -> str:
    """Fill `#FN_ENUM#` and `#FN_CASES#` from the chords `layers` use."""
    enum_lines: list[str] = []
    case_lines: list[str] = []
    for label in fn_labels(layers):
        chord = fn_chord(label)
        if chord is None:
            continue
        name, function_key, inner = chord
        enum_lines.append(f"    {name},")
        case_lines.append(
            f"    case {name}: fn_chord({function_key}, {inner}, record); return false;"
        )
    return text.replace("#FN_ENUM#", "\n".join(enum_lines)).replace(
        "#FN_CASES#", "\n".join(case_lines)
    )


def generate_qmk_keymap(
    layers: list[Layer],
    combos: list[Combo],
    template_path: str | Path,
) -> str:
    """Fill the QMK template, including the function-key chord table."""
    text = generate_keymap(
        layers,
        combos,
        template_path,
        generate_qmk_layer,
        generate_qmk_combos,
    )
    return apply_fn_chords(text, layers)


def map_key_label_to_qmk(label: str) -> str:
    chord = fn_chord(label)
    if chord:
        return chord[0]
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
