#include QMK_KEYBOARD_H

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
	[0] = LAYOUT(
#LAYER_0#
	),
	[1] = LAYOUT(
#LAYER_1#
	),
	[2] = LAYOUT(
#LAYER_2#
	)
};


const uint16_t PROGMEM combo0[] = {#COMBO_TRIGGER_0#, COMBO_END};
const uint16_t PROGMEM combo1[] = {#COMBO_TRIGGER_1#, COMBO_END};
const uint16_t PROGMEM combo2[] = {#COMBO_TRIGGER_2#, COMBO_END};
const uint16_t PROGMEM combo3[] = {#COMBO_TRIGGER_3#, COMBO_END};
const uint16_t PROGMEM combo4[] = {#COMBO_TRIGGER_4#, COMBO_END};

combo_t key_combos[COMBO_COUNT] = {
	COMBO(combo0, #COMBO_RESULT_0#),
	COMBO(combo1, #COMBO_RESULT_1#),
	COMBO(combo2, #COMBO_RESULT_2#),
	COMBO(combo3, #COMBO_RESULT_3#),
	COMBO(combo4, #COMBO_RESULT_4#)
};