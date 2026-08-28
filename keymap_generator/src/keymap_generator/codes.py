"""Shared label vocabulary for QMK and ZMK keymaps."""

from __future__ import annotations

from typing import NamedTuple


class FirmwareCodes(NamedTuple):
    """The same key expressed in each firmware's binding syntax."""

    zmk: str
    qmk: str


# Maps labels from the keymap grid to the key press code in each firmware.
KEY_PRESS_CODES: dict[str, FirmwareCodes] = {
    # Special Keys
    "ESC": FirmwareCodes("ESC", "KC_ESC"),
    "RET": FirmwareCodes("RET", "KC_ENT"),
    "TAB": FirmwareCodes("TAB", "KC_TAB"),
    "SPC": FirmwareCodes("SPC", "KC_SPC"),
    "BKSP": FirmwareCodes("BKSP", "KC_BSPC"),
    "CMD_RET": FirmwareCodes("LG(RET)", "S(KC_ENT)"),
    "ALT_BKSP": FirmwareCodes("LA(BKSP)", "A(KC_BSPC)"),
    # Text Navigation Keys
    "LEFT": FirmwareCodes("LEFT", "KC_LEFT"),
    "RIGHT": FirmwareCodes("RIGHT", "KC_RIGHT"),
    "UP": FirmwareCodes("UP", "KC_UP"),
    "DOWN": FirmwareCodes("DOWN", "KC_DOWN"),
    "WORD_L": FirmwareCodes("LA(LEFT)", "A(KC_LEFT)"),
    "WORD_R": FirmwareCodes("LA(RIGHT)", "A(KC_RIGHT)"),
    "HOME": FirmwareCodes("HOME", "KC_HOME"),
    "END": FirmwareCodes("END", "KC_END"),
    # UI Navigation Keys
    "SPC_L": FirmwareCodes("LC(LEFT)", "C(KC_LEFT)"),
    "SPC_R": FirmwareCodes("LC(RIGHT)", "C(KC_RIGHT)"),
    "NXT_WIN": FirmwareCodes("LC(F4)", "C(KC_F4)"),
    # Forward / Backwards (GUI + Bracket)
    "FWD": FirmwareCodes("LG(LBKT)", "G(KC_LBRC)"),
    "BCK": FirmwareCodes("LG(RBKT)", "G(KC_RBRC)"),
    # Prev / Next Tab (GUI + Shift Bracket)
    "TAB_L": FirmwareCodes("LG(LS(LBKT))", "G(S(KC_LBRC))"),
    "TAB_R": FirmwareCodes("LG(LS(RBKT))", "G(S(KC_RBRC))"),
    # Umlaut key
    "UML": FirmwareCodes("LA(U)", "A(KC_U)"),
    # Symbols
    "`": FirmwareCodes("GRAVE", "KC_GRAVE"),
    "~": FirmwareCodes("LS(GRAVE)", "KC_TILDE"),
    "!": FirmwareCodes("LS(N1)", "KC_EXCLAIM"),
    "@": FirmwareCodes("LS(N2)", "KC_AT"),
    "#": FirmwareCodes("LS(N3)", "KC_HASH"),
    "$": FirmwareCodes("LS(N4)", "KC_DOLLAR"),
    "%": FirmwareCodes("LS(N5)", "KC_PERCENT"),
    "^": FirmwareCodes("LS(N6)", "KC_CIRCUMFLEX"),
    "&": FirmwareCodes("LS(N7)", "KC_AMPERSAND"),
    "*": FirmwareCodes("LS(N8)", "KC_ASTERISK"),
    "(": FirmwareCodes("LS(N9)", "KC_LEFT_PAREN"),
    ")": FirmwareCodes("LS(N0)", "KC_RIGHT_PAREN"),
    "-": FirmwareCodes("KP_MINUS", "KC_MINUS"),
    "_": FirmwareCodes("LS(MINUS)", "KC_UNDERSCORE"),
    "=": FirmwareCodes("EQUAL", "KC_EQUAL"),
    "+": FirmwareCodes("LS(EQUAL)", "KC_PLUS"),
    "[": FirmwareCodes("LBKT", "KC_LBRC"),
    "{": FirmwareCodes("LS(LBKT)", "KC_LCBR"),
    "]": FirmwareCodes("RBKT", "KC_RBRC"),
    "}": FirmwareCodes("LS(RBKT)", "KC_RCBR"),
    "\\": FirmwareCodes("BSLH", "KC_BSLASH"),
    "PIPE": FirmwareCodes("LS(BSLH)", "KC_PIPE"),
    ";": FirmwareCodes("SEMI", "KC_SCOLON"),
    ":": FirmwareCodes("LS(SEMI)", "KC_COLON"),
    "'": FirmwareCodes("SQT", "KC_QUOTE"),
    '"': FirmwareCodes("LS(SQT)", "KC_DOUBLE_QUOTE"),
    ",": FirmwareCodes("COMMA", "KC_COMMA"),
    "<": FirmwareCodes("LS(COMMA)", "KC_LEFT_ANGLE_BRACKET"),
    ".": FirmwareCodes("DOT", "KC_DOT"),
    ">": FirmwareCodes("LS(DOT)", "KC_RIGHT_ANGLE_BRACKET"),
    "/": FirmwareCodes("FSLH", "KC_SLASH"),
    "?": FirmwareCodes("LS(FSLH)", "KC_QUESTION"),
    # Modifiers
    "CMD": FirmwareCodes("LGUI", "KC_LGUI"),
    "SHFT": FirmwareCodes("LSHFT", "KC_LSFT"),
    "CTRL": FirmwareCodes("LCTRL", "KC_LCTL"),
    "ALT": FirmwareCodes("LALT", "KC_LALT"),
}

# Maps labels from the keymap grid to a ready-made binding in each firmware,
# used for keys that are not a simple key press (e.g. Bluetooth controls).
SPECIAL_LABELS: dict[str, FirmwareCodes] = {
    # Bluetooth
    "BT_CLR": FirmwareCodes("&bt BT_CLR", "KC_NO"),
    "BT_0": FirmwareCodes("&bt BT_SEL 0", "KC_NO"),
    "BT_1": FirmwareCodes("&bt BT_SEL 1", "KC_NO"),
    "BT_2": FirmwareCodes("&bt BT_SEL 2", "KC_NO"),
    "BT_3": FirmwareCodes("&bt BT_SEL 3", "KC_NO"),
}

# Maps labels from the keymap grid to layer numbers.
LAYER_LABELS: dict[str, int] = {
    "RSE": 1,
    "LWR": 2,
    "HYP": 3,
    "ADJ": 4,
    "MOU": 5,
}

# Hold-tap flavors a key may ask for, matching the suffix of the behaviors in
# `zmk_template.dtsi`. Keys default to 'tap preferred', which suits the
# home-row; the thumb keys ask for 'hold preferred'. One-shot keys have a
# single behavior and take no flavor.
FLAVORS: tuple[str, ...] = ("tp", "hp")
DEFAULT_FLAVOR: str = "tp"
