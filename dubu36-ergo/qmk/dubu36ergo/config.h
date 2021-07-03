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
