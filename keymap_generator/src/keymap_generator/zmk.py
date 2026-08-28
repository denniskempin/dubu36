"""Map parsed keys to ZMK bindings."""

from __future__ import annotations

from keymap_generator.codes import (
    DEFAULT_FLAVOR,
    KEY_PRESS_CODES,
    LAYER_LABELS,
    SPECIAL_LABELS,
)
from keymap_generator.parser import Combo, Key, Layer


def get_zmk_key_press_code(label: str) -> str | None:
    if label.startswith("CMD_"):
        return f"LG({get_zmk_key_press_code(label[4:])})"
    if label.startswith("HYP_"):
        return f"LA(LS(LC(LG({get_zmk_key_press_code(label[4:])}))))"
    if label.isalpha() and len(label) == 1:
        return label
    if label.isdigit() and len(label) == 1:
        return f"N{label}"
    if label in KEY_PRESS_CODES:
        return KEY_PRESS_CODES[label].zmk
    return None


def map_key_label_to_zmk(label: str) -> str:
    code = get_zmk_key_press_code(label)
    if code:
        return f"&kp {code}"
    if label in LAYER_LABELS:
        return f"&mo {LAYER_LABELS[label]}"
    if label in SPECIAL_LABELS:
        return SPECIAL_LABELS[label].zmk
    if not label:
        return "&trans"
    raise KeyError(f"Cannot map label {label} to zmk.")


def map_key_to_zmk(key: Key) -> str:
    if not key.hold:
        return map_key_label_to_zmk(key.tap)
    if not key.tap:
        return map_key_label_to_zmk(key.hold)

    # All defined in the ZMK template: mt/lt hold a modifier/layer and are named
    # after their flavor, smt/slt additionally stick it on tap.
    if key.hold in LAYER_LABELS:
        layer = LAYER_LABELS[key.hold]
        if key.is_sticky:
            return f"&slt_ {layer} {layer}"
        tap_code = get_zmk_key_press_code(key.tap)
        if tap_code:
            return f"&lt_{key.flavor or DEFAULT_FLAVOR} {layer} {tap_code}"
    else:
        hold_code = get_zmk_key_press_code(key.hold)
        if hold_code:
            if key.is_sticky:
                return f"&smt_ {hold_code} {hold_code}"
            tap_code = get_zmk_key_press_code(key.tap)
            if tap_code:
                return f"&mt_{key.flavor or DEFAULT_FLAVOR} {hold_code} {tap_code}"
    raise KeyError(f"Cannot map hold-tap key ({key.tap}, {key.hold}) to zmk.")


def generate_zmk_combo(combo: Combo | None) -> tuple[str, str]:
    # TODO: Implement combos for ZMK
    return ("0 0", "&trans")


def generate_zmk_layer(layer: Layer) -> str:
    rows: list[str] = []
    for row in layer.rows[:3]:
        # Add padding since this is a 5 row layout with a 6 row corne firmware
        rows.append(
            "&trans " + " ".join(map_key_to_zmk(key) for key in row) + " &trans"
        )
    thumb_bindings = [map_key_to_zmk(key) for key in layer.rows[3]]
    # Corne's combined matrix still has six thumb positions; pad the dropped
    # outer-right slot with &none when the grid only defines five thumbs.
    if len(thumb_bindings) == 5:
        thumb_bindings.append("&none")
    rows.append(" ".join(thumb_bindings))
    return "\n".join(rows)
