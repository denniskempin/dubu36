BOARD=nice_nano

all: keymaps diagrams build/dubu36t_left.uf2 build/dubu36t_right.uf2 build/dubu36e_left.uf2 build/dubu36e_right.uf2

keymaps: config/corne.keymap config/boards/shields/dubu36e/dubu36e.keymap

diagrams: diagrams/reference.svg

setup:
	west init -l config || exit
	west update || exit
	west zephyr-export || exit

clean:
	rm -rf build

config/corne.keymap: generate_keymap.py keymap.yaml
	python3 generate_keymap.py zmk > $@

config/boards/shields/dubu36e/dubu36e.keymap: generate_keymap.py keymap.yaml
	python3 generate_keymap.py zmk > $@

diagrams/reference.svg: render_keymap.py keymap.yaml requirements.txt
	python3 render_keymap.py -o diagrams

build/dubu36t_left.uf2: config/* config/corne.keymap
	west build -d $(basename $@) -s zmk/app -b nice_nano -- -DSHIELD=corne_left -DZMK_CONFIG="`pwd`/config" || exit
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36t_right.uf2: config/* config/corne.keymap
	west build -d $(basename $@) -s zmk/app -b nice_nano -- -DSHIELD=corne_right -DZMK_CONFIG="`pwd`/config" || exit
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36e_left.uf2: config/boards/shields/dubu36e/*
	west build -d $(basename $@) -s zmk/app -b nice_nano -- -DSHIELD=dubu36e_left -DZMK_CONFIG="`pwd`/config" || exit
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36e_right.uf2: config/boards/shields/dubu36e/*
	west build -d $(basename $@) -s zmk/app -b nice_nano -- -DSHIELD=dubu36e_right -DZMK_CONFIG="`pwd`/config" || exit
	cp $(basename $@)/zephyr/zmk.uf2 $@

.PHONY: all keymaps diagrams setup clean
