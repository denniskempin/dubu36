# Agent Guide

A personal 36-key keyboard layout. `keymap.txt` is the single source of truth; a small Python
tool (`keymap_generator`) renders it into a ZMK keymap and a QMK keymap, which are committed
and built into firmware.

## Layout of the repo

| Path | What it is |
| --- | --- |
| `keymap.txt` | The layout: 36 keys per layer. Edit this, never the generated keymaps. |
| `keymap_generator/` | uv-managed Python package that renders `keymap.txt`. |
| `config/` | ZMK user config: `west.yml` (pins ZMK to `v0.3`), `*.conf`, `*.keymap`. |
| `config/shared_keymap.dtsi` | **Generated** ZMK keymap, included by both `.keymap` files. |
| `boards/shields/dubu36e/` | ZMK shield definition for dubu36-ergo. |
| `dubu36-ergo/qmk/` | QMK keyboard for dubu36-ergo, which currently runs wired QMK. |
| `dubu36-ergo/qmk/dubu36ergo/keymaps/default/keymap.c` | **Generated** QMK keymap. |
| `build.yaml` | Board/shield matrix for the ZMK GitHub Actions build. |
| `dubu36-travel/case/`, `*.jpg` | Case models and photos. Binary, leave alone. |

`zephyr/`, `zmk/`, `modules/`, `tools/`, `.west/`, `.zmk-workspace/` and `build/` are west
checkouts and build output, all gitignored. Only `zephyr/module.yml` is tracked, and it is what
makes the repo root a Zephyr module.

## Generated files must stay in sync

`keymap_generator/tests/test_golden.py` asserts that the two committed keymaps byte-match what
the generator produces. Any change to `keymap.txt`, a template, or the generator means you must
regenerate **both** and commit them:

```sh
make keymaps   # -> config/shared_keymap.dtsi
uv run --directory keymap_generator generate-keymap qmk \
  > dubu36-ergo/qmk/dubu36ergo/keymaps/default/keymap.c
```

`make -C dubu36-ergo/qmk keymap` does the QMK half too, but only works once a `qmk_firmware`
checkout exists next to it, so prefer the command above.

## Checks

`.github/workflows/python-ci.yml` runs exactly this, from `keymap_generator/`:

```sh
uv sync --locked
uv run ruff check src tests
uv run ruff format --check src tests
uv run ty check
uv run pytest
```

Run all five before committing. They take a couple of seconds.

## Firmware builds

CI builds firmware via ZMK's reusable `build-user-config.yml` workflow, driven by `build.yaml`.
Locally, `make setup` once (about a minute and a half; it clones Zephyr and its modules), then
`make all` for the four `.uf2` files in `build/` (`dubu36t_{left,right}`, `dubu36e_{left,right}`,
under a minute for all four).

The build needs an **isolated** west workspace, which is why `make setup` creates
`.zmk-workspace/` instead of initializing west at the repo root. The repo root is passed as
`ZMK_EXTRA_MODULES` so ZMK picks up `boards/shields/dubu36e/`, while `zephyr/module.yml` makes
it a Zephyr module with `board_root: .`.

### Gotcha: `.cursor/install.sh` breaks `make`

The Cloud Agent bootstrap runs `west init -l config` at the repo root, so on a fresh VM there is
a west workspace at `/workspace` with Zephyr, ZMK and the modules checked out in place. Two
things then go wrong, and neither is obvious from the output:

- `make setup` fails silently. `west init` inside `.zmk-workspace/` finds the root `.west/`
  above it and aborts with `FATAL ERROR: already initialized in /workspace`, which the Makefile
  swallows with `|| true`. The following `west update` then updates the *root* workspace, so
  `make setup` exits 0 having created nothing, and `make all` fails with
  `ERROR: source directory zmk/app does not exist`.
- Building in the root workspace instead is not a workaround. With the repo root as an extra
  module and a real Zephyr tree at `zephyr/`, Zephyr resolves the repo-root module's Kconfig to
  that tree's own `Kconfig`, and the build dies with
  `recursive 'source' of 'Kconfig.zephyr' detected`.

Clear the root workspace before building firmware:

```sh
cd /workspace
rm -rf .west zmk modules tools
find zephyr -mindepth 1 -maxdepth 1 -not -name module.yml -exec rm -rf {} +
unset ZEPHYR_BASE          # .devcontainer/.bashrc exports it from the root tree
make setup && make all
```

Nothing else in the repo depends on the root workspace, and the keymap generator and its checks
are unaffected.

## Editing `keymap.txt`

The header comment in `keymap.txt` is the reference; the short version:

- Four rows per block: 10, 10, 10, 6 (thumbs). Whitespace-separated cells, `_` for nothing.
- A cell is `TAP`, `TAP/HOLD`, or `TAP/HOLD:FLAVOR`. `LABEL/LABEL` is sticky-on-tap.
- `FLAVOR` is `tp` (tap-preferred, default, home-row) or `hp` (hold-preferred, thumbs).
- `overlay` blocks supply holds; a `layer` lists the overlays it inherits after a `:`.
- Escape `/`, `:`, `_`, `\` in labels with a backslash.

Layer order is load-bearing: `LAYER_LABELS` in `codes.py` maps names to indices, and
`KeymapParser.check_layers` rejects a `keymap.txt` whose layers are not in that order.

## Working on the generator

`keymap_generator/src/keymap_generator/`:

- `parser.py` — `keymap.txt` -> `Layer`/`Key`/`Combo`. Raises `ParseError` with path and line.
- `codes.py` — the label vocabulary: `KEY_PRESS_CODES` (a label's ZMK and QMK key code),
  `SPECIAL_LABELS` (non-keypress bindings such as Bluetooth), `LAYER_LABELS`, `FLAVORS`.
- `zmk.py` / `qmk.py` — `Key` -> a binding string for one firmware.
- `generate.py` — substitutes `#LAYER_N#` / `#COMBO_TRIGGER_N#` / `#COMBO_RESULT_N#` in a template.
- `cli.py` — `generate-keymap {zmk,qmk}`, prints to stdout. Defaults resolve `keymap.txt` and the
  templates relative to the package, so it works from any cwd.

Adding a label usually means one entry in `KEY_PRESS_CODES`, since both backends read it. The
`CMD_` and `HYP_` prefixes are handled structurally in `get_*_key_press_code`, so
`CMD_<anything mappable>` works without a table entry.

Known gaps, deliberate:

- `generate_zmk_combo` is a stub; combos only reach QMK.
- `qmk_template.c` only has `#LAYER_0#`..`#LAYER_2#`, so QMK gets the first three layers.
- Combo count is hard-coded in three places that must agree: `COMBO_SLOTS` in `generate.py`, the
  `#COMBO_*_N#` slots in `qmk_template.c`, and `COMBO_COUNT` in
  `dubu36-ergo/qmk/dubu36ergo/config.h`.
- `generate_zmk_layer` pads each of the three main rows with `&trans` on both ends, mapping the
  36-key grid onto the corne's 42-key matrix.

Code conventions: Python 3.12, `from __future__ import annotations`, full type annotations,
module and public-symbol docstrings, ruff (`E,F,I,UP,B,SIM`, 88 columns) as the formatter and
linter. Tests are plain pytest classes grouped by behaviour under `keymap_generator/tests/`.
