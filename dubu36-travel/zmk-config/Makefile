all: build/left.uf2 build/right.uf2

setup:
	west init -l config || exit
	west update || exit
	west zephyr-export || exit

clean:
	rm -rf build

keymap:
	python3 ../../generate_keymap.py zmk > corne.keymap

build/left.uf2: corne.keymap corne.conf
	west build -d build/left -s zmk/app -b nice_nano -- -DSHIELD=corne_left -DZMK_CONFIG="$(pwd)/config" || exit
	cp build/left/zephyr/zmk.uf2 build/left.uf2

build/right.uf2: corne.keymap corne.conf
	west build -d build/right -s zmk/app -b nice_nano -- -DSHIELD=corne_right -DZMK_CONFIG="$(pwd)/config" || exit
	cp build/right/zephyr/zmk.uf2 build/right.uf2

.PHONY: setup clean keymap