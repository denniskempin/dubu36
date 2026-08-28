all: build

# Delegated to the root Makefile so there is one definition of how the keymap
# is generated, and so it works without a qmk_firmware checkout.
keymap:
	$(MAKE) -C ../.. dubu36-ergo/qmk/dubu36ergo/keymaps/default/keymap.c

setup:
	qmk setup -H qmk_firmware

# Only building needs the keyboard linked into the qmk_firmware checkout.
qmk_firmware/keyboards/dubu36ergo:
	ln -sf ../../dubu36ergo qmk_firmware/keyboards/dubu36ergo

build: keymap qmk_firmware/keyboards/dubu36ergo
	make -C qmk_firmware dubu36ergo:default

flash: keymap qmk_firmware/keyboards/dubu36ergo
	make -C qmk_firmware dubu36ergo:default::avrdude-split-left

flash-right: keymap qmk_firmware/keyboards/dubu36ergo
	make -C qmk_firmware dubu36ergo:default::avrdude-split-right

.PHONY: all setup build flash flash-right keymap
