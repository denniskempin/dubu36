# Keymap Generator

Converts [`keymap.txt`](../keymap.txt) into ZMK and QMK keymaps and the
diagrams under [`diagrams/`](../diagrams). Managed with [uv](https://docs.astral.sh/uv/).

## Development

From this directory:

```sh
uv sync --group diagrams
uv run generate-keymap zmk       # print the ZMK keymap
uv run generate-keymap qmk       # print the QMK keymap
uv run generate-keymap diagrams --out-dir ../diagrams
uv run pytest
uv run ruff check
uv run ruff format
uv run ty check
```

`--group diagrams` is required: cairosvg for PNG export, and `ty` to resolve
that import. cairosvg also needs the system cairo library (`libcairo2` on
Debian/Ubuntu, `cairo` on Homebrew). After editing the layout, regenerate all
outputs together with `make generated` from the repo root;
`tests/test_golden.py` compares them.
