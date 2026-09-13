#pragma once

#include "config_common.h"

#define VENDOR_ID       0x4653
#define PRODUCT_ID      0x0001
#define DEVICE_VER      0x0001
#define MANUFACTURER    denniskempin
#define PRODUCT         dubu36ergo

#define USE_SERIAL
#define SOFT_SERIAL_PIN D2
#define MASTER_LEFT

#define MATRIX_ROWS 8
#define MATRIX_COLS 5
#define MATRIX_ROW_PINS { D4, C6, D7, E6 }
#define MATRIX_COL_PINS { F5, F6, F7, B1, B3 }
#define DIODE_DIRECTION COL2ROW

#define DEBOUNCE 5

#define COMBO_COUNT 5

/* Matches the combo timeout ZMK is given, which is also QMK's own default. */
#define COMBO_TERM 50

/* Prefer tap, so home-row mods stay usable. QMK has no per-behavior flavors. */
#define TAPPING_TERM 200
#define IGNORE_MOD_TAP_INTERRUPT
