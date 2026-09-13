# HWMv2: the revision picks the nice!nano v1 (plain nice_nano is now v2);
# //zmk carries ZMK's board defaults. xiao_ble//zmk was seeeduino_xiao_ble.
NICE_NANO := nice_nano@1.0.0//zmk
XIAO_BLE := xiao_ble//zmk

# Isolated west workspace: a Zephyr tree at zephyr/ would collide with
# zephyr/module.yml at the repo root. See AGENTS.md.
ZMK_WS ?= $(abspath .zmk-workspace)
REPO_ROOT := $(abspath .)
ZMK_CMAKE=-DZMK_CONFIG="$(ZMK_WS)/config" -DZMK_EXTRA_MODULES="$(REPO_ROOT)"

# Never inherit ZEPHYR_BASE: the container exports whichever tree it found,
# and a stale value fails later inside CMake.
WEST_SETUP := env -u ZEPHYR_BASE west
WEST_BUILD := env ZEPHYR_BASE="$(ZMK_WS)/zephyr" west

QMK_KEYMAP := dubu36-ergo/qmk/dubu36ergo/keymaps/default/keymap.c
GENERATOR := keymap_generator/pyproject.toml keymap_generator/src/keymap_generator/*.py keymap.txt

# One firmware per Prospector status screen: the Kconfig choice is compile-time.
DONGLE_SCREENS := classic radii field operator
DONGLE_UF2 := $(DONGLE_SCREENS:%=build/dubu36t_dongle_%.uf2)

all: keymaps diagrams build/dubu36t_left.uf2 build/dubu36t_right.uf2 build/dubu36t_left_peripheral.uf2 $(DONGLE_UF2) build/dubu36e_left.uf2 build/dubu36e_right.uf2

# All golden-test outputs. Regenerating only some of them fails the test.
generated: keymaps diagrams

keymaps: config/shared_keymap.dtsi $(QMK_KEYMAP)

diagrams: diagrams/reference.svg

setup:
	@if [ -d .west ]; then \
		echo "error: a west workspace at the repo root shadows $(ZMK_WS) and cannot build this firmware." >&2; \
		echo "       rm -rf .west zmk modules tools" >&2; \
		echo "       find zephyr -mindepth 1 -maxdepth 1 -not -name module.yml -exec rm -rf {} +" >&2; \
		exit 1; \
	fi
	mkdir -p "$(ZMK_WS)/config"
	cp -a config/. "$(ZMK_WS)/config/"
	cd "$(ZMK_WS)" && { [ -d .west ] || $(WEST_SETUP) init -l config; }
	cd "$(ZMK_WS)" && $(WEST_SETUP) update
	cd "$(ZMK_WS)" && $(WEST_SETUP) zephyr-export

clean:
	rm -rf build

# Also drops the west workspace; the next setup re-clones it.
distclean: clean
	rm -rf .zmk-workspace

config/shared_keymap.dtsi: $(GENERATOR) keymap_generator/zmk_template.dtsi
	uv run --directory keymap_generator generate-keymap zmk > $@.tmp
	mv $@.tmp $@

$(QMK_KEYMAP): $(GENERATOR) keymap_generator/qmk_template.c
	uv run --directory keymap_generator generate-keymap qmk > $@.tmp
	mv $@.tmp $@

define sync-config
	mkdir -p "$(ZMK_WS)/config"
	cp -a config/. "$(ZMK_WS)/config/"
endef

diagrams/reference.svg: $(GENERATOR) keymap_generator/uv.lock
	uv run --directory keymap_generator --group diagrams generate-keymap diagrams --out-dir ../diagrams

build/dubu36t_left.uf2: config/* config/shared_keymap.dtsi
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b $(NICE_NANO) -- -DSHIELD=corne_left $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36t_right.uf2: config/* config/shared_keymap.dtsi
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b $(NICE_NANO) -- -DSHIELD=corne_right $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36t_left_peripheral.uf2: config/* config/shared_keymap.dtsi
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b $(NICE_NANO) -- -DSHIELD=corne_left -DCONFIG_ZMK_SPLIT=y -DCONFIG_ZMK_SPLIT_ROLE_CENTRAL=n $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36t_dongle_%.uf2: boards/shields/corne_dongle/* config/* config/shared_keymap.dtsi
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b $(XIAO_BLE) -- -DSHIELD="corne_dongle prospector_adapter" -DCONFIG_PROSPECTOR_STATUS_SCREEN_$$(echo $* | tr 'a-z' 'A-Z')=y $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/settings_reset_nice_nano.uf2:
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b $(NICE_NANO) -- -DSHIELD=settings_reset $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/settings_reset_xiao_ble.uf2:
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b $(XIAO_BLE) -- -DSHIELD=settings_reset $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36e_left.uf2: boards/shields/dubu36e/* config/shared_keymap.dtsi config/dubu36e.keymap config/dubu36e.conf
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b $(NICE_NANO) -- -DSHIELD=dubu36e_left $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36e_right.uf2: boards/shields/dubu36e/* config/shared_keymap.dtsi config/dubu36e.keymap config/dubu36e.conf
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b $(NICE_NANO) -- -DSHIELD=dubu36e_right $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

.PHONY: all generated keymaps diagrams setup clean distclean
