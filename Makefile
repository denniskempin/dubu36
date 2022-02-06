all: dubu36-ergo dubu36-travel

dubu36-ergo:
	make -C dubu36-ergo/qmk keymap
	make -C dubu36-ergo/zmk-config keymap

dubu36-travel:
	make -C dubu36-travel/zmk-config keymap

.PHONY: dubu36-ergo dubu36-travel