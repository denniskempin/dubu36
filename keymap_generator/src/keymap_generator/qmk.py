"""Map parsed keys to QMK keycodes."""

from __future__ import annotations

from keymap_generator.codes import KEY_PRESS_CODES, LAYER_LABELS, SPECIAL_LABELS
from keymap_generator.parser import Combo, Key, Layer


def get_qmk_key_press_code(label: str) -> str | None:
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


def map_key_to_qmk(key: Key) -> str:
    if not key.hold:
        return map_key_label_to_qmk(key.tap)
    if not key.tap:
        return map_key_label_to_qmk(key.hold)

    # QMK has no per key hold-tap flavors, so they are ignored here. One shot
    # keycodes are the closest match for sticky keys: they stick on tap and act
    # as a plain modifier or layer shift when held.
    if key.hold in LAYER_LABELS:
        if key.is_sticky:
            return f"OSL({LAYER_LABELS[key.hold]})"
        tap_code = get_qmk_key_press_code(key.tap)
        if tap_code:
            return f"LT({LAYER_LABELS[key.hold]},{tap_code})"
    else:
        hold_code = get_qmk_key_press_code(key.hold)
        if hold_code:
            hold_code = hold_code.replace("KC_", "MOD_")
            if key.is_sticky:
                return f"OSM({hold_code})"
            tap_code = get_qmk_key_press_code(key.tap)
            if tap_code:
                return f"MT({hold_code},{tap_code})"
    raise KeyError(f"Cannot map hold-tap key ({key.tap}, {key.hold}) to qmk.")


def generate_qmk_combo(combo: Combo | None) -> tuple[str, str]:
    if not combo:
        return ("KC_NO", "KC_NO")
    return (
        ", ".join((map_key_label_to_qmk(combo.a), map_key_label_to_qmk(combo.b))),
        map_key_label_to_qmk(combo.result),
    )


def generate_qmk_layer(layer: Layer) -> str:
    return ",\n".join(
        ", ".join(map_key_to_qmk(key) for key in row) for row in layer.rows
    )
