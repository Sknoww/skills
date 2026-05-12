#!/usr/bin/env python3
"""Estimate token counts for a list of files.

Heuristic: chars / 3.5 for code, chars / 4.0 for prose/markdown.
Bundled with slice-issues for the 100k context budget gate.

Usage: python estimate_tokens.py path1 path2 ...
Output (tab-separated, one line per file plus TOTAL):
    path<TAB>estimate
    ...
    TOTAL<TAB>sum
Exit code 0 on success, 1 if any path could not be read.
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE_EXTS = {
    ".py", ".pyi",
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".go",
    ".rs",
    ".java", ".kt", ".kts",
    ".swift",
    ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".scala",
    ".sh", ".bash", ".zsh", ".fish",
    ".ps1",
    ".sql",
    ".lua",
    ".dart",
    ".vue", ".svelte",
}


def estimate(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    divisor = 3.5 if path.suffix.lower() in CODE_EXTS else 4.0
    return int(len(text) / divisor)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: estimate_tokens.py path1 [path2 ...]", file=sys.stderr)
        return 2

    errors: list[str] = []
    total = 0
    lines: list[str] = []
    for raw in argv:
        path = Path(raw)
        if not path.exists() or not path.is_file():
            errors.append(f"missing: {raw}")
            continue
        try:
            n = estimate(path)
        except OSError as exc:
            errors.append(f"read failed: {raw}: {exc}")
            continue
        total += n
        lines.append(f"{raw}\t{n}")

    print("\n".join(lines))
    print(f"TOTAL\t{total}")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
