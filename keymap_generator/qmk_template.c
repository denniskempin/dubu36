#include QMK_KEYBOARD_H

// One custom keycode per F18_/F19_ chord. The keymap names them FN_F18_Q and
// so on; process_record_user sends the function key and the inner key together.
enum fn_chords {
    FN_UNUSED = SAFE_RANGE,
#FN_ENUM#
};

static void fn_chord(uint16_t fn, uint16_t kc, keyrecord_t *record) {
    if (record->event.pressed) {
        register_code16(fn);
        register_code16(kc);
    } else {
        unregister_code16(kc);
        unregister_code16(fn);
    }
}

// LT(0, kc) is reserved for the F17 hold: QMK's MT() only holds modifiers.
// Tap sends kc. Hold registers F17 and leaves the rest of the board alone,
// which is what makes other keys chord with F17.
static bool process_f17_hold(uint16_t keycode, keyrecord_t *record) {
    if ((keycode & 0xF000) != QK_LAYER_TAP || ((keycode >> 8) & 0x0F) != 0) {
        return true;
    }
    uint8_t tap = keycode & 0xFF;
    if (tap == KC_NO) {
        return true;
    }
    if (record->tap.count && record->event.pressed) {
        tap_code16(tap);
    } else if (record->event.pressed) {
        register_code(KC_F17);
    } else if (!record->tap.count) {
        unregister_code(KC_F17);
    }
    return false;
}

bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    switch (keycode) {
#FN_CASES#
    default:
        break;
    }
    return process_f17_hold(keycode, record);
}

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
	[0] = LAYOUT(
#LAYER_0#
	),
	[1] = LAYOUT(
#LAYER_1#
	),
	[2] = LAYOUT(
#LAYER_2#
	),
	[3] = LAYOUT(
#LAYER_3#
	),
	[4] = LAYOUT(
#LAYER_4#
	),
	[5] = LAYOUT(
#LAYER_5#
	),
	[6] = LAYOUT(
#LAYER_6#
	),
	[7] = LAYOUT(
#LAYER_7#
	)
};


#COMBOS#
