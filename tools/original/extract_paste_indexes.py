#!/usr/bin/env python3
import csv
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


PASTE_RE = re.compile(r"https://paste\.linuxiarz\.pl/view/([0-9a-f]{8})$")


class PasteIndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_row = False
        self.in_cell = False
        self.cells: list[str] = []
        self.cell_parts: list[str] = []
        self.paste_id = ""
        self.rows: list[tuple[str, list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "tr":
            self.in_row = True
            self.cells = []
            self.paste_id = ""
        elif self.in_row and tag in {"td", "th"}:
            self.in_cell = True
            self.cell_parts = []
        elif self.in_row and tag == "a":
            match = PASTE_RE.fullmatch(attributes.get("href", ""))
            if match:
                self.paste_id = match.group(1)

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.in_row and tag in {"td", "th"} and self.in_cell:
            self.cells.append(" ".join("".join(self.cell_parts).split()))
            self.in_cell = False
        elif tag == "tr" and self.in_row:
            if self.paste_id and len(self.cells) >= 5:
                self.rows.append((self.paste_id, self.cells[:5]))
            self.in_row = False


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_paste_indexes.py INDEX_DIR OUTPUT_TSV")

    index_dir = Path(sys.argv[1])
    output = Path(sys.argv[2])
    rows = []
    for path in sorted(index_dir.iterdir(), key=lambda item: item.name):
        if not path.is_file():
            continue
        parser = PasteIndexParser()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        for paste_id, cells in parser.rows:
            rows.append((paste_id, *cells, path.name))

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(("paste_id", "title", "author", "language", "hits", "age", "index"))
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
