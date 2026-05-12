#!/usr/bin/env python3
"""Count pages in a PDF file.

Usage: python page_count.py <path.pdf>
Prints page count to stdout. Exits 0 on success, 1 on read failure, 2 on usage error.

Requires: pypdf (`pip install pypdf`).
"""
from __future__ import annotations

import sys
from pathlib import Path


def page_count(path: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(path)).pages)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: page_count.py <path.pdf>", file=sys.stderr)
        return 2
    path = Path(argv[0])
    if not path.exists() or not path.is_file():
        print(f"missing: {argv[0]}", file=sys.stderr)
        return 1
    try:
        print(page_count(path))
    except Exception as exc:
        print(f"error: {argv[0]}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
