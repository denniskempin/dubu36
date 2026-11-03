#pragma once

#include "config_common.h"

/* USB Device descriptor parameter */
#define VENDOR_ID       0x4653
#define PRODUCT_ID      0x0001
#define DEVICE_VER      0x0001
#define MANUFACTURER    denniskempin
#define PRODUCT         dubu36ergo

/* Serial */
#define USE_SERIAL
#define SOFT_SERIAL_PIN D2
#define MASTER_LEFT

/* Keyboard matrix wiring */
#define MATRIX_ROWS 8
#define MATRIX_COLS 5
#define MATRIX_ROW_PINS { D4, C6, D7, E6 }
#define MATRIX_COL_PINS { F5, F6, F7, B1, B3 }
#define DIODE_DIRECTION COL2ROW

/* Set 0 if debouncing isn't needed */
#define DEBOUNCE 5

#define COMBO_COUNT 5

/* Matches the combo timeout ZMK is given, which is also QMK's own default. */
#define COMBO_TERM 50

/* Match combo keys against layer 0 on every layer, so W+F and U+Y stay Esc
 * and Enter while another layer is active. Must match COMBO_ONLY_FROM_LAYER
 * in keymap_generator/src/keymap_generator/qmk.py. A define in keymap.c would
 * not reach process_combo.c. */
#define COMBO_ONLY_FROM_LAYER 0

/* 
 * Tap-Hold configuration
 * Strongly biased to prefer tap over hold to make home-row mods usable
 */
#define TAPPING_TERM 200
#define IGNORE_MOD_TAP_INTERRUPT
