"""Map parsed keys to ZMK bindings."""

from __future__ import annotations

from keymap_generator.codes import (
    DEFAULT_FLAVOR,
    KEY_PRESS_CODES,
    LAYER_LABELS,
    SPECIAL_LABELS,
)
from keymap_generator.parser import ROW_SIZES, Combo, Key, Layer, find_key_position

# generate_zmk_layer pads each of the three main rows to the corne matrix.
MAIN_ROW_SIZES = ROW_SIZES[:3]
PADDED_ROW_WIDTH = MAIN_ROW_SIZES[0] + 2

COMBO_TIMEOUT_MS = 50
COMBO_LAYER = 0

# Idle-time guard before a combo may fire. 0 (ZMK's default, omitted from
# output) is only safe on pairs typing never rolls across. Raise it for a
# home-row pair; that then refuses to fire right after a burst of typing.
COMBO_PRIOR_IDLE_MS = 0


def get_zmk_key_press_code(label: str) -> str | None:
    if label.startswith("SHFT_"):
        return f"LS({get_zmk_key_press_code(label.removeprefix('SHFT_'))})"
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

    # Behaviors in the ZMK template: mt/lt by flavor; omt/olt one-shot on tap.
    if key.hold in LAYER_LABELS:
        layer = LAYER_LABELS[key.hold]
        if key.is_oneshot:
            return f"&olt_ {layer} {layer}"
        tap_code = get_zmk_key_press_code(key.tap)
        if tap_code:
            return f"&lt_{key.flavor or DEFAULT_FLAVOR} {layer} {tap_code}"
    else:
        hold_code = get_zmk_key_press_code(key.hold)
        if hold_code:
            if key.is_oneshot:
                return f"&omt_ {hold_code} {hold_code}"
            tap_code = get_zmk_key_press_code(key.tap)
            if tap_code:
                return f"&mt_{key.flavor or DEFAULT_FLAVOR} {hold_code} {tap_code}"
    raise KeyError(f"Cannot map hold-tap key ({key.tap}, {key.hold}) to zmk.")


def zmk_key_position(row: int, column: int) -> int:
    """Grid cell as a ZMK key-position, after `&trans` padding on each main row."""
    if row < len(MAIN_ROW_SIZES):
        return row * PADDED_ROW_WIDTH + 1 + column
    return len(MAIN_ROW_SIZES) * PADDED_ROW_WIDTH + column


def generate_zmk_combo(combo: Combo, default_layer: Layer, index: int) -> str:
    """Render one combo as a child of the `combos` node."""
    positions = " ".join(
        str(zmk_key_position(*find_key_position(default_layer, label)))
        for label in (combo.a, combo.b)
    )
    properties = [f"timeout-ms = <{COMBO_TIMEOUT_MS}>;"]
    if COMBO_PRIOR_IDLE_MS:
        properties.append(f"require-prior-idle-ms = <{COMBO_PRIOR_IDLE_MS}>;")
    properties += [
        f"key-positions = <{positions}>;",
        f"bindings = <{map_key_label_to_zmk(combo.result)}>;",
        f"layers = <{COMBO_LAYER}>;",
    ]
    return "\n".join(
        [
            f"        combo_{index} {{",
            *(f"            {property}" for property in properties),
            "        };",
        ]
    )


def generate_zmk_combos(combos: list[Combo], default_layer: Layer) -> str:
    """Render the `combos` node, or nothing at all when there are no combos."""
    if not combos:
        return ""
    children = "\n".join(
        generate_zmk_combo(combo, default_layer, index)
        for index, combo in enumerate(combos)
    )
    return "\n".join(
        ["    combos {", '        compatible = "zmk,combos";', children, "    };"]
    )


def generate_zmk_layer(layer: Layer) -> str:
    rows: list[str] = []
    for row in layer.rows[:3]:
        rows.append(
            "&trans " + " ".join(map_key_to_zmk(key) for key in row) + " &trans"
        )
    rows.append(" ".join(map_key_to_zmk(key) for key in layer.rows[3]))
    return "\n".join(rows)
