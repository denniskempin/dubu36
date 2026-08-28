BOARD=nice_nano
# Isolated west workspace so the cloned Zephyr tree does not collide with
# zephyr/module.yml at the repo root (same approach as ZMK's CI workflow).
ZMK_WS ?= $(abspath .zmk-workspace)
REPO_ROOT := $(abspath .)
ZMK_CMAKE=-DZMK_CONFIG="$(ZMK_WS)/config" -DZMK_EXTRA_MODULES="$(REPO_ROOT)"

all: keymaps diagrams build/dubu36t_left.uf2 build/dubu36t_right.uf2 build/dubu36e_left.uf2 build/dubu36e_right.uf2

keymaps: config/shared_keymap.dtsi

diagrams: diagrams/reference.svg

setup:
	mkdir -p "$(ZMK_WS)/config"
	cp -a config/. "$(ZMK_WS)/config/"
	cd "$(ZMK_WS)" && west init -l config || true
	cd "$(ZMK_WS)" && west update || exit
	cd "$(ZMK_WS)" && west zephyr-export || exit

clean:
	rm -rf build

config/shared_keymap.dtsi: keymap_generator/pyproject.toml keymap_generator/src/keymap_generator/*.py keymap.txt keymap_generator/zmk_template.dtsi
	uv run --directory keymap_generator generate-keymap zmk > $@.tmp
	mv $@.tmp $@

# Sync user config into the west workspace before each build.
define sync-config
	mkdir -p "$(ZMK_WS)/config"
	cp -a config/. "$(ZMK_WS)/config/"
endef

diagrams/reference.svg: keymap_generator/pyproject.toml keymap_generator/src/keymap_generator/*.py keymap.txt keymap_generator/uv.lock
	uv run --directory keymap_generator --group diagrams generate-keymap diagrams --out-dir ../diagrams

build/dubu36t_left.uf2: config/* config/shared_keymap.dtsi
	$(sync-config)
	cd "$(ZMK_WS)" && west build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b nice_nano -- -DSHIELD=corne_left $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36t_right.uf2: config/* config/shared_keymap.dtsi
	$(sync-config)
	cd "$(ZMK_WS)" && west build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b nice_nano -- -DSHIELD=corne_right $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36e_left.uf2: boards/shields/dubu36e/* config/shared_keymap.dtsi config/dubu36e.keymap config/dubu36e.conf
	$(sync-config)
	cd "$(ZMK_WS)" && west build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b nice_nano -- -DSHIELD=dubu36e_left $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36e_right.uf2: boards/shields/dubu36e/* config/shared_keymap.dtsi config/dubu36e.keymap config/dubu36e.conf
	$(sync-config)
	cd "$(ZMK_WS)" && west build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b nice_nano -- -DSHIELD=dubu36e_right $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

.PHONY: all keymaps diagrams setup clean
