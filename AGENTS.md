# Agent Guide

A personal 36-key keyboard layout. `keymap.txt` is the single source of truth; a small Python
tool (`keymap_generator`) renders it into a ZMK keymap, a QMK keymap and a set of layout
diagrams, all of which are committed.

## Layout of the repo

| Path | What it is |
| --- | --- |
| `keymap.txt` | The layout: 36 keys per layer. Edit this, never the generated output. |
| `keymap_generator/` | uv-managed Python package that renders `keymap.txt`. |
| `config/` | ZMK user config: `west.yml` (pins ZMK to `v0.3` and the Prospector module), `*.conf`, `*.keymap`. |
| `config/shared_keymap.dtsi` | **Generated** ZMK keymap, included by both `.keymap` files. |
| `dubu36-ergo/qmk/dubu36ergo/keymaps/default/keymap.c` | **Generated** QMK keymap. |
| `diagrams/` | **Generated** SVG and PNG layout diagrams, embedded in the README. |
| `boards/shields/dubu36e/` | ZMK shield definition for dubu36-ergo. |
| `boards/shields/corne_dongle/` | ZMK shield for the Prospector as the dubu36-travel split central. |
| `dubu36-ergo/qmk/` | QMK keyboard for dubu36-ergo, which currently runs wired QMK. |
| `build.yaml` | Board/shield matrix for the ZMK GitHub Actions build. |
| `dubu36-travel/case/`, `*.jpg` | Case models and photos. Binary, leave alone. |

`zephyr/`, `zmk/`, `modules/`, `tools/`, `.west/`, `.zmk-workspace/` and `build/` are west
checkouts and build output, all gitignored. Only `zephyr/module.yml` is tracked, and it is what
makes the repo root a Zephyr module.

## Generated files must stay in sync

`keymap_generator/tests/test_golden.py` asserts that the committed ZMK keymap, QMK keymap and
`diagrams/*.svg` byte-match what the generator produces. After changing `keymap.txt`, a template
or the generator, regenerate all three and commit them:

```sh
make generated
```

That is `make keymaps` (both keymaps) plus `make diagrams`. Running only one of them leaves the
other stale and the golden test red. Diagram PNGs are regenerated too but not compared, since
their bytes depend on the cairo version.

## Checks

`.github/workflows/python-ci.yml` runs exactly this, from `keymap_generator/`:

```sh
uv sync --locked --group diagrams
uv run ruff check src tests
uv run ruff format --check src tests
uv run ty check
uv run pytest
```

Run all five before committing. They take a couple of seconds. The `diagrams` group is not
optional for the checks: without it `ty` cannot resolve the `cairosvg` import in `render.py`.

## Firmware builds

CI builds firmware via ZMK's reusable `build-user-config.yml` workflow, driven by `build.yaml`.
Locally, `.cursor/install.sh` already ran `make setup`, so `make all` produces the six `.uf2`
files in `build/` (`dubu36t_{left,right,left_peripheral,dongle}`, `dubu36e_{left,right}`) in
under a minute. On a fresh checkout `make setup` comes first and needs about a minute and a
half to clone Zephyr and its modules. A change to `config/west.yml` also needs `make setup`
re-run; a plain `make all` will not pull a new west project.

`make clean` drops `build/`; `make distclean` also drops `.zmk-workspace/`, which means the next
`make setup` re-clones.

`make build/settings_reset_nice_nano.uf2` and `make build/settings_reset_xiao_ble.uf2` are
not part of `all`. Flash them on every device before switching the travel board between
standalone and dongle firmware.

`config/west.yml` pins the Prospector module (`carrefinho/prospector-zmk-module`) to commit
`77a8522`, which is the last `main` revision that targets ZMK v0.3 / Zephyr 3.5. The dongle
build is `seeeduino_xiao_ble` with shields `corne_dongle prospector_adapter`. The shield name
`corne_dongle` is load-bearing: ZMK's config lookup strips `_dongle` and then picks up
`config/corne.keymap` and `config/corne.conf`. `config/corne_dongle.conf` is merged after
those and overrides `CONFIG_ZMK_SLEEP` for the USB-powered dongle.

### Why the west workspace is off to the side

`make setup` builds the workspace in `.zmk-workspace/` rather than initializing west at the repo
root, and this is load-bearing. The repo root is passed as `ZMK_EXTRA_MODULES` so ZMK picks up
`boards/shields/dubu36e/` and `boards/shields/corne_dongle/`, which works because
`zephyr/module.yml` makes the root a Zephyr module with `board_root: .`. If a real Zephyr tree
is *also* checked out at `zephyr/`, Zephyr resolves that module's Kconfig to the tree's own
`Kconfig` and the build dies with `recursive 'source' of 'Kconfig.zephyr' detected`.

Two guards exist because of this, and both are deliberate:

- `make setup` refuses to run when `.west/` exists at the repo root, and prints the commands to
  clear it. An earlier `.cursor/install.sh` created one, so old VM snapshots may still have it;
  the current bootstrap clears it for you.
- The Makefile never inherits `ZEPHYR_BASE`. `make setup` unsets it and lets west find the
  workspace from the working directory; the build recipes pin it to `$(ZMK_WS)/zephyr`. A stale
  value fails much later, inside CMake, as `include could not find requested file: zephyr_default`.

## Editing `keymap.txt`

The header comment in `keymap.txt` is the reference; the short version:

- Four rows per block: 10, 10, 10, 6 (thumbs). Whitespace-separated cells, `_` for nothing.
- A cell is `TAP`, `TAP/HOLD`, or `TAP/HOLD:FLAVOR`. `LABEL/LABEL` is one-shot on tap and momentary on hold.
- `FLAVOR` is `tp` (tap-preferred, default, home-row) or `hp` (hold-preferred, thumbs).
- `overlay` blocks supply holds; a `layer` lists the overlays it inherits after a `:`.
- Escape `/`, `:`, `_`, `\` in labels with a backslash.

Layer order is load-bearing: `LAYER_LABELS` in `codes.py` maps names to indices, and
`KeymapParser.check_layers` rejects a `keymap.txt` whose layers are not in that order.

Editing this file changes all three generated artifacts, so follow it with `make generated`.

## Working on the generator

`keymap_generator/src/keymap_generator/`:

- `parser.py` — `keymap.txt` -> `Layer`/`Key`/`Combo`. Raises `ParseError` with path and line.
- `codes.py` — the label vocabulary: `KEY_PRESS_CODES` (a label's ZMK and QMK key code),
  `SPECIAL_LABELS` (non-keypress bindings such as Bluetooth), `LAYER_LABELS`, `FLAVORS`.
- `zmk.py` / `qmk.py` — `Key` -> a binding string for one firmware.
- `generate.py` — substitutes `#LAYER_N#` and the single `#COMBOS#` block in a template. The
  combo generator is handed the default layer, since a combo names its trigger keys by the
  label they tap there.
- `render.py` — the SVG diagram renderer, plus `render_png` which lazily imports `cairosvg` from
  the `diagrams` group. Legend positions and glyphs are documented in the README. Combos appear
  only on the stacked reference card, as a rounded box on the seam between the two trigger keys.
- `cli.py` — `generate-keymap {zmk,qmk,diagrams}`. The keymaps print to stdout; `diagrams` writes
  files to `--out-dir`. Defaults resolve `keymap.txt` and the templates relative to the package,
  so it works from any cwd.

Adding a label usually means one entry in `KEY_PRESS_CODES`, since both backends read it. The
`CMD_` and `HYP_` prefixes are handled structurally in `get_*_key_press_code`, so
`CMD_<anything mappable>` works without a table entry.

Combos reach both firmwares, but by different routes. ZMK numbers them by key position, so
`zmk_key_position` has to map a grid cell through the `&trans` padding below; QMK matches them
against the keycode the keymap holds, so a trigger on the home row has to be named by its whole
`MT(...)` keycode rather than the plain key press it produces.

What keeps a combo from firing during ordinary typing is the choice of keys, not the timing: a
pair the typist never rolls across cannot be triggered by accident. `C+V` was picked over the
more comfortable home-row pairs for that reason, since Colemak puts its most frequent rolls
there and `st` or `ne` would fire a combo constantly. `COMBO_PRIOR_IDLE_MS` in `zmk.py` is the
fallback if a riskier pair is ever needed; it is 0 here, and left out of the generated keymap,
because requiring idle time would stop Esc firing right after a burst of typing.

Known gaps, deliberate:

- `qmk_template.c` only has `#LAYER_0#`..`#LAYER_2#`, so QMK gets the first three layers.
- Combo count is hard-coded in two places that must agree: `COMBO_SLOTS` in `qmk.py` and
  `COMBO_COUNT` in `dubu36-ergo/qmk/dubu36ergo/config.h`. ZMK needs no count, so it only
  emits the combos that exist.
- Combos render on the stacked reference card only, as a rounded box on the seam between the
  two trigger keys. Per-layer boards omit them.
- The guards on the `hp` hold-taps, `require-prior-idle-ms` and `quick-tap-ms`, are ZMK only.
  QMK has `TAPPING_TERM` and `IGNORE_MOD_TAP_INTERRUPT` in its config and nothing per-behavior,
  so a thumb layer is easier to shift by accident there.
- `generate_zmk_layer` pads each of the three main rows with `&trans` on both ends, mapping the
  36-key grid onto the corne's 42-key matrix.
- `render.py` skips the `hyp` and `adj` layers (`EXCLUDED_LAYERS`), so `diagrams/` has no board
  for them.

Code conventions: Python 3.12, `from __future__ import annotations`, full type annotations,
module and public-symbol docstrings, ruff (`E,F,I,UP,B,SIM`, 88 columns) as the formatter and
linter. Tests are plain pytest classes grouped by behaviour under `keymap_generator/tests/`.
