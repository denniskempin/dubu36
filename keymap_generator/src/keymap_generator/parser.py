"""Parse the keymap grid into layers and combos."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import NamedTuple

from keymap_generator.codes import FLAVORS, LAYER_LABELS

# Number of keys in each row of the grid: three rows of ten, then the thumbs.
ROW_SIZES: tuple[int, ...] = (10, 10, 10, 6)

# Cell that holds no key, and no hold when used on the hold side of a cell.
BLANK = "_"

COMMENT = "//"


class Combo(NamedTuple):
    """A chord: press `a` and `b` together to produce `result`."""

    a: str
    b: str
    result: str


class Key(NamedTuple):
    """A single key: what it does when tapped, and what it does when held.

    `hold` is `None` while a layer cell is still waiting for an overlay to
    fill it in; after overlays are applied it is always a string (possibly
    empty).
    """

    tap: str
    hold: str | None
    flavor: str | None

    @property
    def is_oneshot(self) -> bool:
        """One-shot keys repeat their label, e.g. `shft/shft` or `rse/rse`.

        A tap applies the modifier or layer to the next keypress; a hold is a
        regular (momentary) modifier or layer shift.
        """
        return bool(self.tap) and self.tap == self.hold


class Layer(NamedTuple):
    """A named layer, as rows of keys matching ROW_SIZES."""

    name: str
    rows: list[list[Key]]


class Block(NamedTuple):
    """The header of the block currently being parsed.

    `keyword` is one of `overlay`, `layer` or `combos`; `name` is empty for a
    `combos` block; `overlays` lists the overlays a `layer` inherits holds from.
    """

    keyword: str
    name: str
    overlays: list[str]


class ParseError(Exception):
    """A parse failure with a path and line number."""

    def __init__(self, path: str | Path, line_number: int, message: str) -> None:
        super().__init__(f"{path}:{line_number}: {message}")


def split_unescaped(text: str, separator: str) -> list[str]:
    """Split on the first unescaped separator, leaving escape sequences intact."""
    parts: list[str] = []
    part: list[str] = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            part.append(text[i : i + 2])
            i += 2
        elif text[i] == separator and not parts:
            parts.append("".join(part))
            part = []
            i += 1
        else:
            part.append(text[i])
            i += 1
    parts.append("".join(part))
    return parts


def strip_comment(line: str) -> str:
    """Return `line` with a trailing `//` comment removed, respecting escapes."""
    i = 0
    while i < len(line):
        if line[i] == "\\" and i + 1 < len(line):
            i += 2
        elif line.startswith(COMMENT, i):
            return line[:i]
        else:
            i += 1
    return line


def unescape(label: str) -> str:
    """Resolve backslash escape sequences in a label."""
    out: list[str] = []
    i = 0
    while i < len(label):
        if label[i] == "\\" and i + 1 < len(label):
            out.append(label[i + 1])
            i += 2
        else:
            out.append(label[i])
            i += 1
    return "".join(out)


def parse_label(field: str) -> str:
    """Normalize a label, mapping the blank cell to an empty label."""
    return "" if field == BLANK else unescape(field).upper()


class KeymapParser:
    """Parse the keymap grid into a list of layers and combos."""

    def __init__(self, path: str | Path) -> None:
        self.path = path
        self.line_number = 0
        self.overlays: dict[str, list[list[Key]]] = {}
        self.layers: list[Layer] = []
        self.combos: list[Combo] = []
        self.block: Block | None = None
        self.rows: list[list[Key]] = []

    def error(self, message: str) -> ParseError:
        return ParseError(self.path, self.line_number, message)

    def parse(self, source_lines: Iterable[str]) -> tuple[list[Layer], list[Combo]]:
        for self.line_number, line in enumerate(source_lines, start=1):
            line = strip_comment(line).strip()
            if not line:
                continue
            parts = line.split(None, 1)
            keyword = parts[0]
            rest = parts[1].strip() if len(parts) > 1 else ""
            if keyword in ("overlay", "layer", "combos"):
                self.end_block()
                self.start_block(keyword, rest)
            elif self.block is None:
                raise self.error(
                    f"expected an overlay, layer or combos block, got {line!r}"
                )
            elif self.block.keyword == "combos":
                self.combos.append(self.parse_combo(line.split()))
            else:
                self.rows.append(self.parse_row(line.split()))
        self.end_block()
        self.check_layers()
        return self.layers, self.combos

    def start_block(self, keyword: str, rest: str) -> None:
        name, separator, overlays = rest.partition(":")
        overlays_list = (
            [o.strip() for o in overlays.split(",") if o.strip()] if separator else []
        )
        for overlay in overlays_list:
            if overlay not in self.overlays:
                raise self.error(f"unknown overlay {overlay!r}")
        if overlays_list and keyword != "layer":
            raise self.error(f"{keyword} blocks cannot use overlays")
        name = name.strip()
        if keyword == "combos" and name:
            raise self.error(f"{keyword} blocks take no name")
        if keyword != "combos" and not name:
            raise self.error(f"{keyword} blocks need a name")
        self.block = Block(keyword, name, overlays_list)
        self.rows = []

    def end_block(self) -> None:
        if self.block is None:
            return
        keyword, name, overlays = self.block
        if keyword != "combos":
            if len(self.rows) != len(ROW_SIZES):
                raise self.error(
                    f"{keyword} {name} has {len(self.rows)} rows, "
                    f"expected {len(ROW_SIZES)}"
                )
            if keyword == "overlay":
                self.overlays[name] = self.rows
            else:
                self.layers.append(
                    Layer(name, self.apply_overlays(self.rows, overlays))
                )
        self.block = None
        self.rows = []

    def apply_overlays(
        self, rows: Sequence[Sequence[Key]], overlays: Sequence[str]
    ) -> list[list[Key]]:
        """Fill in the hold of every cell that does not define one itself."""
        keys: list[list[Key]] = []
        for y, row in enumerate(rows):
            keys.append([])
            for x, (tap, hold, flavor) in enumerate(row):
                if hold is None:
                    # The cell inherits its hold from the overlays it covers,
                    # with the last overlay to cover it taking precedence.
                    for overlay in overlays:
                        _, covered, covered_flavor = self.overlays[overlay][y][x]
                        if covered:
                            hold, flavor = covered, covered_flavor
                keys[-1].append(Key(tap, hold or "", flavor))
        return keys

    def parse_row(self, cells: Sequence[str]) -> list[Key]:
        assert self.block is not None
        keyword, name, _ = self.block
        row_number = len(self.rows)
        if row_number >= len(ROW_SIZES):
            raise self.error(f"{keyword} {name} has more than {len(ROW_SIZES)} rows")
        if len(cells) != ROW_SIZES[row_number]:
            raise self.error(
                f"row {row_number} of {keyword} {name} has {len(cells)} keys, "
                f"expected {ROW_SIZES[row_number]}"
            )
        if keyword == "overlay":
            # Overlay cells only define the hold of the keys they cover.
            return [Key("", *self.parse_hold(cell)) for cell in cells]
        return [self.parse_key(cell) for cell in cells]

    def parse_key(self, cell: str) -> Key:
        """Parse `TAP`, `TAP/HOLD` or `TAP/HOLD:FLAVOR` into a Key."""
        parts = split_unescaped(cell, "/")
        tap = parts[0]
        if len(parts) == 1:
            # A cell without a hold of its own inherits the hold of an overlay,
            # which `apply_overlays` fills in.
            return Key(parse_label(tap), None, None)
        hold = parts[1]
        key = Key(parse_label(tap), *self.parse_hold(hold))
        if key.flavor and (key.is_oneshot or not key.tap):
            # One-shot keys always use the same tap-preferred hold-tap, and a
            # hold-only key has no tap to distinguish, so a flavor is a mistake.
            raise self.error(f"{cell!r} is not a hold-tap, so it takes no flavor")
        return key

    def parse_hold(self, field: str) -> tuple[str, str | None]:
        """Parse `HOLD` or `HOLD:FLAVOR` into a (hold, flavor) pair."""
        parts = split_unescaped(field, ":")
        hold = parts[0]
        flavor = parts[1] if len(parts) > 1 else None
        if flavor is not None and flavor not in FLAVORS:
            raise self.error(
                f"unknown flavor {flavor!r}, expected one of {', '.join(FLAVORS)}"
            )
        return parse_label(hold), flavor

    def parse_combo(self, cells: Sequence[str]) -> Combo:
        if len(cells) != 4 or cells[2] != "->":
            raise self.error("expected a combo of the form `KEY KEY -> RESULT`")
        return Combo(*(parse_label(cell) for cell in [*cells[:2], cells[3]]))

    def check_layers(self) -> None:
        """Layers are referenced by their position, so the order matters."""
        for name, index in LAYER_LABELS.items():
            if index >= len(self.layers) or self.layers[index].name.upper() != name:
                raise self.error(
                    f"layer {index} must be named {name.lower()!r}, as it is the "
                    f"layer used by the {name.lower()} hold"
                )


def parse_keymap(path: str | Path) -> tuple[list[Layer], list[Combo]]:
    """Parse a keymap file into layers and combos."""
    with open(path, encoding="utf-8") as source:
        return KeymapParser(path).parse(source.readlines())
