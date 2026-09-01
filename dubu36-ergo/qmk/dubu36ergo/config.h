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

/*
 * Combos sit on home-row keys that ordinary typing rolls across, so both keys
 * have to go down almost together for one to count. QMK has no equivalent of
 * ZMK's require-prior-idle-ms, so this is the only guard on this side and it is
 * tighter than the 50ms default.
 */
#define COMBO_TERM 35

/* 
 * Tap-Hold configuration
 * Strongly biased to prefer tap over hold to make home-row mods usable
 */
#define TAPPING_TERM 200
#define IGNORE_MOD_TAP_INTERRUPT
