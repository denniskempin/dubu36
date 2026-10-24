#include QMK_KEYBOARD_H

// APPLE_FN is the Apple Fn / Globe key. Each F18_/F19_ chord is one more
// custom keycode, named FN_F18_Q and so on; process_record_user sends the
// function key and the inner key together.
//
// Fn is Consumer AC Next Keyboard Layout Select (0x029D), not one of QMK's
// eight modifiers, so MT() cannot hold it. A plain Fn key uses APPLE_FN.
// A tap-preferred hold is LT(0, kc): tap sends kc, hold sends Fn. The count
// keeps the report down while either of the two Fn holds is still pressed.
#define APPLE_FN_USAGE 0x029D

enum fn_chords {
    FN_UNUSED = SAFE_RANGE,
    APPLE_FN,
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

static uint8_t apple_fn_holds;

static void apple_fn_set(bool pressed) {
    if (pressed) {
        if (apple_fn_holds++ == 0) {
            host_consumer_send(APPLE_FN_USAGE);
        }
    } else if (apple_fn_holds > 0 && --apple_fn_holds == 0) {
        host_consumer_send(0);
    }
}

static bool process_apple_fn_hold(uint16_t keycode, keyrecord_t *record) {
    if ((keycode & 0xF000) != QK_LAYER_TAP || ((keycode >> 8) & 0x0F) != 0) {
        return true;
    }
    uint8_t tap = keycode & 0xFF;
    if (tap == KC_NO) {
        return true;
    }
    if (record->tap.count) {
        if (record->event.pressed) {
            tap_code16(tap);
        }
    } else {
        apple_fn_set(record->event.pressed);
    }
    return false;
}

bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    if (keycode == APPLE_FN) {
        apple_fn_set(record->event.pressed);
        return false;
    }
    switch (keycode) {
#FN_CASES#
    default:
        break;
    }
    return process_apple_fn_hold(keycode, record);
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
