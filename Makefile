BOARD=nice_nano
# Isolated west workspace so the cloned Zephyr tree does not collide with
# zephyr/module.yml at the repo root (same approach as ZMK's CI workflow).
ZMK_WS ?= $(abspath .zmk-workspace)
REPO_ROOT := $(abspath .)
ZMK_CMAKE=-DZMK_CONFIG="$(ZMK_WS)/config" -DZMK_EXTRA_MODULES="$(REPO_ROOT)"

# The dev container exports ZEPHYR_BASE for whichever tree it finds, and a stale
# value fails deep inside CMake, so never inherit it: west finds the workspace
# from the working directory during setup, and builds are pinned to its Zephyr.
WEST_SETUP := env -u ZEPHYR_BASE west
WEST_BUILD := env ZEPHYR_BASE="$(ZMK_WS)/zephyr" west

QMK_KEYMAP := dubu36-ergo/qmk/dubu36ergo/keymaps/default/keymap.c
GENERATOR := keymap_generator/pyproject.toml keymap_generator/src/keymap_generator/*.py keymap.txt

all: keymaps diagrams build/dubu36t_left.uf2 build/dubu36t_right.uf2 build/dubu36e_left.uf2 build/dubu36e_right.uf2

# Everything the golden tests check against keymap.txt. Regenerate all of it
# after editing keymap.txt, or the tests fail on whatever was left behind.
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

# Also drops the west workspace, which make setup needs a couple of minutes to
# clone again.
distclean: clean
	rm -rf .zmk-workspace

config/shared_keymap.dtsi: $(GENERATOR) keymap_generator/zmk_template.dtsi
	uv run --directory keymap_generator generate-keymap zmk > $@.tmp
	mv $@.tmp $@

$(QMK_KEYMAP): $(GENERATOR) keymap_generator/qmk_template.c
	uv run --directory keymap_generator generate-keymap qmk > $@.tmp
	mv $@.tmp $@

# Sync user config into the west workspace before each build.
define sync-config
	mkdir -p "$(ZMK_WS)/config"
	cp -a config/. "$(ZMK_WS)/config/"
endef

diagrams/reference.svg: $(GENERATOR) keymap_generator/uv.lock
	uv run --directory keymap_generator --group diagrams generate-keymap diagrams --out-dir ../diagrams

build/dubu36t_left.uf2: config/* config/shared_keymap.dtsi
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b nice_nano -- -DSHIELD=corne_left $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36t_right.uf2: config/* config/shared_keymap.dtsi
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b nice_nano -- -DSHIELD=corne_right $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36e_left.uf2: boards/shields/dubu36e/* config/shared_keymap.dtsi config/dubu36e.keymap config/dubu36e.conf
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b nice_nano -- -DSHIELD=dubu36e_left $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

build/dubu36e_right.uf2: boards/shields/dubu36e/* config/shared_keymap.dtsi config/dubu36e.keymap config/dubu36e.conf
	$(sync-config)
	cd "$(ZMK_WS)" && $(WEST_BUILD) build -d "$(REPO_ROOT)/$(basename $@)" -s zmk/app -b nice_nano -- -DSHIELD=dubu36e_right $(ZMK_CMAKE) || exit
	mkdir -p build
	cp $(basename $@)/zephyr/zmk.uf2 $@

.PHONY: all generated keymaps diagrams setup clean distclean
