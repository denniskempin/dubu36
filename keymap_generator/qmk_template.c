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

bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    switch (keycode) {
#FN_CASES#
    default:
        break;
    }
    return true;
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
