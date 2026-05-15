#!/usr/bin/env python3
"""Parse, merge, and render publishing-roadmap.md.

Three subcommands:
  parse <path>                       — read existing roadmap markdown,
                                       emit structured JSON state to stdout.
  merge <existing-state> <findings>  — apply merge rules; emit merged
                                       state JSON to stdout.
  render <state> <metadata>          — render markdown from state +
                                       metadata; emit to stdout.

Bundled with chart-publishing-path. Source of truth at
scripts/roadmap_merge.py; copy lives at
skills/release/chart-publishing-path/roadmap_merge.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def cmd_parse(args: argparse.Namespace) -> int:
    raise NotImplementedError("parse — see Task 6")


def cmd_merge(args: argparse.Namespace) -> int:
    raise NotImplementedError("merge — see Task 7")


def cmd_render(args: argparse.Namespace) -> int:
    raise NotImplementedError("render — see Task 8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roadmap_merge",
        description="Parse, merge, and render publishing-roadmap.md",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_parse = sub.add_parser("parse", help="parse existing roadmap markdown")
    p_parse.add_argument("path", type=Path, help="path to existing roadmap markdown")
    p_parse.set_defaults(func=cmd_parse)

    p_merge = sub.add_parser("merge", help="merge new findings into existing state")
    p_merge.add_argument("existing_state", type=Path, help="existing state JSON path")
    p_merge.add_argument("findings", type=Path, help="new findings JSON path")
    p_merge.set_defaults(func=cmd_merge)

    p_render = sub.add_parser("render", help="render markdown from state + metadata")
    p_render.add_argument("state", type=Path, help="state JSON path")
    p_render.add_argument("metadata", type=Path, help="metadata JSON path")
    p_render.set_defaults(func=cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
