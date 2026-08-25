# Keymap Generator

A small Python package that converts [`keymap.txt`](../keymap.txt) into ZMK and QMK
keymaps. Managed with [uv](https://docs.astral.sh/uv/).

## Development

Install uv, then from this directory:

```sh
uv sync
uv run generate-keymap zmk   # print the ZMK keymap
uv run generate-keymap qmk   # print the QMK keymap
uv run pytest                # run the test suite
uv run ruff check            # lint
uv run ruff format           # format
uv run ty check              # type check
```

Regenerating the committed keymaps via `make keymaps` (repo root) or
`make keymap` (under `dubu36-ergo/qmk/`) also requires `uv` on `PATH`.
