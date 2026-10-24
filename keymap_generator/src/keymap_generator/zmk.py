"""Map parsed keys to ZMK bindings."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from keymap_generator.codes import (
    DEFAULT_FLAVOR,
    KEY_PRESS_CODES,
    LAYER_LABELS,
    SPECIAL_LABELS,
)
from keymap_generator.generate import generate_keymap
from keymap_generator.parser import ROW_SIZES, Combo, Key, Layer, find_key_position

# The three main rows of the grid, and how wide each becomes once
# `generate_zmk_layer` has padded it out to the corne's matrix.
MAIN_ROW_SIZES = ROW_SIZES[:3]
PADDED_ROW_WIDTH = MAIN_ROW_SIZES[0] + 2

# Both keys of a combo have to go down within COMBO_TIMEOUT_MS of each other,
# and COMBO_LAYER keeps combos off every layer but the base one.
COMBO_TIMEOUT_MS = 50
COMBO_LAYER = 0

# How long the board must have been idle before a combo may fire at all. Zero
# lets one fire mid-word. That is safe for W+F (Esc), which Colemak does not
# roll. U+Y (Enter) does occur in "buy" and "guy"; the guard stays off anyway,
# because turning it on would also stop Esc, and would stop Enter from firing
# straight after a burst of typing. A home-row combo such as `st` would need
# this raised. Omitted from the output when zero, as that is ZMK's default.
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


def map_key_to_zmk(key: Key, layer_mods: Mapping[str, str] | None = None) -> str:
    """Bind one key.

    `layer_mods` maps a layer's hold label to the modifier that layer holds
    for its whole lifetime, as declared with `layer name + MOD`. A hold of
    such a layer uses the generated `&lt_<name>` behavior instead of `&lt_`.
    """
    if not key.hold:
        return map_key_label_to_zmk(key.tap)
    if not key.tap:
        return map_key_label_to_zmk(key.hold)

    # All defined in the ZMK template: mt/lt hold a modifier/layer and are named
    # after their flavor; omt/olt hold it and one-shot it on tap. A layer that
    # declares a modifier uses the hold-tap generated for that layer.
    if key.hold in LAYER_LABELS:
        layer = LAYER_LABELS[key.hold]
        if key.is_oneshot:
            return f"&olt_ {layer} {layer}"
        modifier = (layer_mods or {}).get(key.hold, "")
        tap_code = get_zmk_key_press_code(key.tap)
        if modifier and tap_code:
            if (key.flavor or DEFAULT_FLAVOR) != "tp":
                raise KeyError(
                    f"Layer {key.hold.lower()} holds {modifier}, which is "
                    "tap-preferred only."
                )
            return f"&lt_{key.hold.lower()} {layer} {tap_code}"
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
    """Index of a grid cell in the padded matrix ZMK counts key-positions in.

    `generate_zmk_layer` pads each of the three main rows with a `&trans` on
    both ends to fill the corne's wider matrix, so a row of ten keys takes up
    twelve positions and the thumbs only start after all three.
    """
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


def generate_zmk_layer(
    layer: Layer, layer_mods: Mapping[str, str] | None = None
) -> str:
    rows: list[str] = []
    for row in layer.rows[:3]:
        # Add padding since this is a 5 row layout with a 6 row corne firmware
        rows.append(
            "&trans "
            + " ".join(map_key_to_zmk(key, layer_mods) for key in row)
            + " &trans"
        )
    rows.append(" ".join(map_key_to_zmk(key, layer_mods) for key in layer.rows[3]))
    return "\n".join(rows)


def _modified_layers(layers: list[Layer]) -> list[tuple[Layer, str]]:
    """Layers that hold a modifier, with that modifier's ZMK keycode."""
    found: list[tuple[Layer, str]] = []
    for layer in layers:
        if not layer.modifier:
            continue
        code = get_zmk_key_press_code(layer.modifier)
        if code is None:
            raise KeyError(f"Cannot hold {layer.modifier} with layer {layer.name}.")
        found.append((layer, code))
    return found


def _layer_mod_macro(name: str, code: str) -> str:
    """A macro that holds `code` for as long as layer parameter 1 is held."""
    return "\n".join(
        [
            f"        {name}_lm: {name}_lm {{",
            '            compatible = "zmk,behavior-macro-one-param";',
            "            #binding-cells = <1>;",
            "            wait-ms = <0>;",
            "            tap-ms = <0>;",
            "            bindings",
            "                = <&macro_param_1to1>",
            "                , <&macro_press &mo MACRO_PLACEHOLDER>",
            f"                , <&macro_press &kp {code}>",
            "                , <&macro_pause_for_release>",
            f"                , <&macro_release &kp {code}>",
            "                , <&macro_param_1to1>",
            "                , <&macro_release &mo MACRO_PLACEHOLDER>",
            "                ;",
            "        };",
        ]
    )


def generate_layer_mod_macros(layers: list[Layer]) -> str:
    """The `macros` node for layers declared with `+ MOD`, or nothing."""
    modified = _modified_layers(layers)
    if not modified:
        return ""
    bodies = "\n".join(_layer_mod_macro(layer.name, code) for layer, code in modified)
    return "\n".join(["    macros {", bodies, "    };"])


def generate_layer_mod_holds(layers: list[Layer]) -> str:
    """Tap-preferred hold-taps whose hold side is that layer's macro."""
    return "\n".join(
        "\n".join(
            [
                f"        lt_{layer.name}: lt_{layer.name} {{",
                '            compatible = "zmk,behavior-hold-tap";',
                "            #binding-cells = <2>;",
                '            flavor = "tap-preferred";',
                "            tapping-term-ms = <200>;",
                f"            bindings = <&{layer.name}_lm>, <&kp>;",
                "        };",
            ]
        )
        for layer, _code in _modified_layers(layers)
    )


def generate_zmk_keymap(
    layers: list[Layer],
    combos: list[Combo],
    template_path: str | Path,
) -> str:
    """Fill the ZMK template, including layer-modifier hold behaviors."""
    mods = {layer.name.upper(): layer.modifier for layer in layers if layer.modifier}

    def layer_fn(layer: Layer) -> str:
        return generate_zmk_layer(layer, mods)

    text = generate_keymap(layers, combos, template_path, layer_fn, generate_zmk_combos)
    return text.replace("#LAYER_MOD_HOLDS#", generate_layer_mod_holds(layers)).replace(
        "#LAYER_MOD_MACROS#", generate_layer_mod_macros(layers)
    )
