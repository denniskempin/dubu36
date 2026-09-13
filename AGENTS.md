# Agent Guide

A personal 36-key keyboard layout. `keymap.txt` is the source of truth; `keymap_generator`
(Python, uv) renders it into a ZMK keymap, a QMK keymap and layout diagrams, all committed. The
travel board runs ZMK, dubu36-ergo runs wired QMK, which is why there are two keymaps.

## Writing style

Keep docs and comments short, and write new ones that way. Document only what the code cannot
show: constraints, gotchas, and the reason behind a choice that looks arbitrary. Do not restate
what a file or function plainly does, recount history, or repeat what the config being described
already says. Prefer a sentence to a paragraph, and deleting to rewording.

## After editing `keymap.txt` or the generator

```sh
make generated   # == make keymaps + make diagrams
```

`tests/test_golden.py` byte-compares the committed ZMK keymap, QMK keymap and `diagrams/*.svg`
against fresh output, so regenerating only some of them fails it. PNG bytes depend on the cairo
version and are not compared.

## Checks

From `keymap_generator/`, all five, before committing (seconds); the same list as
`.github/workflows/python-ci.yml`:

```sh
uv sync --locked --group diagrams
uv run ruff check src tests
uv run ruff format --check src tests
uv run ty check
uv run pytest
```

`--group diagrams` is not optional: without it `ty` cannot resolve `cairosvg` in `render.py`.

Code conventions: Python 3.12, `from __future__ import annotations`, full type annotations,
module and public-symbol docstrings, ruff (`E,F,I,UP,B,SIM`, 88 columns). Tests are pytest
classes grouped by behaviour.

## Paths worth knowing

- Generated, never hand-edited: `config/shared_keymap.dtsi`,
  `dubu36-ergo/qmk/dubu36ergo/keymaps/default/keymap.c`, `diagrams/`.
- Gitignored west checkouts and output: `zephyr/`, `zmk/`, `modules/`, `tools/`, `.west/`,
  `.zmk-workspace/`, `build/`. `zephyr/module.yml` is the exception: it is tracked, and it is
  what makes the repo root a Zephyr module.
- `dubu36-travel/case/` and `*.jpg` are binary; leave them alone.

## keymap.txt

Its header comment is the syntax reference. Layer order is load-bearing: `LAYER_LABELS` in
`codes.py` maps names to indices, and `KeymapParser.check_layers` rejects a file whose layers
are in another order.

## Generator notes

- A new label is usually one entry in `KEY_PRESS_CODES`, which both backends read. `CMD_*` and
  `HYP_*` are handled structurally in `get_*_key_press_code` and need no entry.
- Combos reach the two firmwares by different routes: ZMK addresses trigger keys by position, so
  `zmk_key_position` maps a grid cell through the `&trans` padding; QMK matches on keycode, so a
  home-row trigger must be named by its whole `MT(...)` keycode.
- What keeps a combo from firing while typing is the key pair, not timing. `M+,` (Enter) is
  adjacent, letter-then-punctuation, and never rolled in Colemak, unlike home-row pairs such as
  `st` or `ne`. `COMBO_PRIOR_IDLE_MS` in `zmk.py` is 0, and omitted from the output, because
  requiring idle time would stop Enter firing right after a burst of typing. Raise its value
  only if a riskier pair is ever added.
- `COMBO_SLOTS` in `qmk.py` and `COMBO_COUNT` in `dubu36-ergo/qmk/dubu36ergo/config.h` are
  hard-coded and must agree. ZMK emits only the combos that exist.
- `generate_zmk_layer` pads the three main rows with `&trans` on both ends to map the 36-key grid
  onto the corne's 42-key matrix.
- Deliberate gaps: `qmk_template.c` has only `#LAYER_0#`..`#LAYER_2#`, so QMK gets three layers;
  combos render only on the stacked reference card; `render.py` skips `hyp` and `adj`
  (`EXCLUDED_LAYERS`); `require-prior-idle-ms` and `quick-tap-ms` are ZMK-only, so a QMK thumb
  layer is easier to shift by accident.

## Firmware builds

`make all` produces nine `.uf2` in `build/`, under a minute per target on a warm tree. `make
setup` (already run by `.cursor/install.sh`) clones the west workspace in about 90 seconds;
re-run it after changing `config/west.yml`, as `make all` will not pull a new west project.
`make distclean` also drops `.zmk-workspace/`, so the next `setup` re-clones.

`make build/settings_reset_nice_nano.uf2` and `make build/settings_reset_xiao_ble.uf2` are
outside `all`. Flash them on every device before switching the travel board between standalone
and dongle firmware.

- Board targets carry Zephyr HWMv2 qualifiers: `nice_nano@1.0.0//zmk` (plain `nice_nano` now
  means v2) and `xiao_ble//zmk`. ZMK's reusable workflow fails outright if a board with a `zmk`
  variant is requested without it. `build.yaml` sets `artifact-name` per entry, because the
  default is derived from the board target and would put the qualifiers in firmware file names.
- `.devcontainer/Dockerfile`'s tag must match the Zephyr version ZMK is on (`zmk-dev-arm:4.1`
  ships the SDK Zephyr 4.1 wants). CI takes its image from ZMK's workflow, so the two are bumped
  separately.
- `config/west.yml` pins the Prospector module to `ed98221` on `feat/new-status-screens`, the
  only branch built against Zephyr 4.1. That branch also sets the display thread's stack size,
  so this repo does not.
- `boards/shields/corne_dongle/` is the Prospector acting as the dubu36-travel split central.
  The name is load-bearing: ZMK's config lookup strips `_dongle` and picks up
  `config/corne.keymap` and `config/corne.conf`; `config/corne_dongle.conf` merges after them
  and overrides `CONFIG_ZMK_SLEEP` for the USB-powered dongle.
- `PROSPECTOR_STATUS_SCREEN_LAYOUT` is a Kconfig choice, fixed at flash time, so all four screens
  get their own firmware (`DONGLE_SCREENS` drives a Makefile pattern rule, `build.yaml` has one
  entry each). Never select a screen in `config/corne_dongle.conf`; it would apply to every build.

### Why the west workspace is off to the side

`make setup` builds it in `.zmk-workspace/` rather than at the repo root, because the root is
passed as `ZMK_EXTRA_MODULES` so ZMK finds `boards/shields/`. If a real Zephyr tree is also
checked out at `zephyr/`, Zephyr resolves the root module's Kconfig to that tree's own and the
build dies with `recursive 'source' of 'Kconfig.zephyr' detected`. Two guards follow from this:
`make setup` refuses to run while `.west/` exists at the root, and the Makefile never inherits
`ZEPHYR_BASE` (a stale value fails much later, inside CMake, as `include could not find
requested file: zephyr_default`).
