# Keymap Generator

A small Python package that converts [`keymap.txt`](../keymap.txt) into ZMK and QMK
keymaps and into the layout diagrams under [`diagrams/`](../diagrams).
Managed with [uv](https://docs.astral.sh/uv/).

## Development

Install uv, then from this directory:

```sh
uv sync --group diagrams
uv run generate-keymap zmk       # print the ZMK keymap
uv run generate-keymap qmk       # print the QMK keymap
uv run generate-keymap diagrams --out-dir ../diagrams
uv run pytest                    # run the test suite
uv run ruff check                # lint
uv run ruff format               # format
uv run ty check                  # type check
```

The `diagrams` group provides cairosvg, which the renderer needs for PNG export
and `ty` needs to resolve the import.

`tests/test_golden.py` compares the committed keymaps and diagram SVGs against a
fresh render, so regenerate all of them together with `make generated` from the
repo root after editing the layout.
