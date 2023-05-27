BOARD=nice_nano

all: build/dubu36t_left.uf2 build/dubu36t_right.uf2

setup:
	west init -l config || exit
	west update || exit
	west zephyr-export || exit

clean:
	rm -rf build

config/corne.keymap: generate_keymap.py README.md
	python3 generate_keymap.py zmk > config/corne.keymap

build/dubu36t_left.uf2: config/*
	west build -d $(basename $@) -s zmk/app -b nice_nano -- -DSHIELD=corne_left -DZMK_CONFIG="`pwd`/config" || exit
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36t_right.uf2: config/*
	west build -d $(basename $@) -s zmk/app -b nice_nano -- -DSHIELD=corne_right -DZMK_CONFIG="`pwd`/config" || exit
	cp $(basename $@)/zephyr/zmk.uf2 $@

.PHONY: setup clean
