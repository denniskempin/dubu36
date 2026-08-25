"""Shared label vocabulary for QMK and ZMK keymaps."""

from __future__ import annotations

# Maps labels from the keymap grid to key press codes in ZMK and QMK.
# "LABEL": ("ZMK CODE", "QMK CODE")
KEY_PRESS_CODES: dict[str, tuple[str, str]] = {
    # Special Keys
    "ESC": ("ESC", "KC_ESC"),
    "RET": ("RET", "KC_ENT"),
    "TAB": ("TAB", "KC_TAB"),
    "SPC": ("SPC", "KC_SPC"),
    "BKSP": ("BKSP", "KC_BSPC"),
    "CMD_RET": ("LG(RET)", "S(KC_ENT)"),
    "ALT_BKSP": ("LA(BKSP)", "A(KC_BSPC)"),
    # Text Navigatioh Keys
    "LEFT": ("LEFT", "KC_LEFT"),
    "RIGHT": ("RIGHT", "KC_RIGHT"),
    "UP": ("UP", "KC_UP"),
    "DOWN": ("DOWN", "KC_DOWN"),
    "WORD_L": ("LA(LEFT)", "A(KC_LEFT)"),
    "WORD_R": ("LA(RIGHT)", "A(KC_RIGHT)"),
    "HOME": ("HOME", "KC_HOME"),
    "END": ("END", "KC_END"),
    # UI Navigation Keys
    "SPC_L": ("LC(LEFT)", "C(KC_LEFT)"),
    "SPC_R": ("LC(RIGHT)", "C(KC_RIGHT)"),
    "NXT_WIN": ("LC(F4)", "C(KC_F4)"),
    # Forward / Backwards (GUI + Bracket)
    "FWD": ("LG(LBKT)", "G(KC_LBRC)"),
    "BCK": ("LG(RBKT)", "G(KC_RBRC)"),
    # Prev / Next Tab (GUI + Shift Bracket)
    "TAB_L": ("LG(LS(LBKT))", "G(S(KC_LBRC))"),
    "TAB_R": ("LG(LS(RBKT))", "G(S(KC_RBRC))"),
    # Umlaut key
    "UML": ("LA(U)", "A(KC_U)"),
    # Symbols
    "`": ("GRAVE", "KC_GRAVE"),
    "~": ("LS(GRAVE)", "KC_TILDE"),
    "!": ("LS(N1)", "KC_EXCLAIM"),
    "@": ("LS(N2)", "KC_AT"),
    "#": ("LS(N3)", "KC_HASH"),
    "$": ("LS(N4)", "KC_DOLLAR"),
    "%": ("LS(N5)", "KC_PERCENT"),
    "^": ("LS(N6)", "KC_CIRCUMFLEX"),
    "&": ("LS(N7)", "KC_AMPERSAND"),
    "*": ("LS(N8)", "KC_ASTERISK"),
    "(": ("LS(N9)", "KC_LEFT_PAREN"),
    ")": ("LS(N0)", "KC_RIGHT_PAREN"),
    "-": ("KP_MINUS", "KC_MINUS"),
    "_": ("LS(MINUS)", "KC_UNDERSCORE"),
    "=": ("EQUAL", "KC_EQUAL"),
    "+": ("LS(EQUAL)", "KC_PLUS"),
    "[": ("LBKT", "KC_LBRC"),
    "{": ("LS(LBKT)", "KC_LCBR"),
    "]": ("RBKT", "KC_RBRC"),
    "}": ("LS(RBKT)", "KC_RCBR"),
    "\\": ("BSLH", "KC_BSLASH"),
    "PIPE": ("LS(BSLH)", "KC_PIPE"),
    ";": ("SEMI", "KC_SCOLON"),
    ":": ("LS(SEMI)", "KC_COLON"),
    "'": ("SQT", "KC_QUOTE"),
    '"': ("LS(SQT)", "KC_DOUBLE_QUOTE"),
    ",": ("COMMA", "KC_COMMA"),
    "<": ("LS(COMMA)", "KC_LEFT_ANGLE_BRACKET"),
    ".": ("DOT", "KC_DOT"),
    ">": ("LS(DOT)", "KC_RIGHT_ANGLE_BRACKET"),
    "/": ("FSLH", "KC_SLASH"),
    "?": ("LS(FSLH)", "KC_QUESTION"),
    # Modifiers
    "CMD": ("LGUI", "KC_LGUI"),
    "SHFT": ("LSHFT", "KC_LSFT"),
    "CTRL": ("LCTRL", "KC_LCTL"),
    "ALT": ("LALT", "KC_LALT"),
}

# Maps labels from the keymap grid to special instructions for ZMK and QMK.
# "LABEL": ("ZMK", "QMK")
SPECIAL_LABELS: dict[str, tuple[str, str]] = {
    # Bluetooth
    "BT_CLR": ("&bt BT_CLR", "KC_NO"),
    "BT_0": ("&bt BT_SEL 0", "KC_NO"),
    "BT_1": ("&bt BT_SEL 1", "KC_NO"),
    "BT_2": ("&bt BT_SEL 2", "KC_NO"),
    "BT_3": ("&bt BT_SEL 3", "KC_NO"),
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
# home-row; the thumb keys ask for 'hold preferred'. Sticky keys have a single
# behavior and take no flavor.
FLAVORS: tuple[str, ...] = ("tp", "hp")
DEFAULT_FLAVOR: str = "tp"
