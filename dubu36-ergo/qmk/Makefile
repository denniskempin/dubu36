all: build

qmk_firmware/keyboards/dubu36ergo:
	ln -sf ../../dubu36ergo qmk_firmware/keyboards/dubu36ergo 	

keymap: qmk_firmware/keyboards/dubu36ergo
	python3 ../../generate_keymap.py qmk > dubu36ergo/keymaps/default/keymap.c

setup:
	qmk setup -H qmk_firmware

build: keymap 
	make -C qmk_firmware dubu36ergo:default

flash: keymap 
	make -C qmk_firmware dubu36ergo:default::avrdude-split-left
	
flash-right: keymap 
	make -C qmk_firmware dubu36ergo:default::avrdude-split-right


.PHONY: setup build flash flash-right keymap