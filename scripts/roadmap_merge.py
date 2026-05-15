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
import re
import sys
from pathlib import Path

STATUS_BY_ICON = {
    "✅": "done",
    "🟡": "partial",
    "⬜": "pending",
    "🚧": "blocked",
    "⚠️": "recheck",
}
ICON_BY_STATUS = {v: k for k, v in STATUS_BY_ICON.items()}

# matches: "- <icon> [Tag] Title... <!-- id: some.dotted.id -->"
ITEM_RE = re.compile(
    r"^-\s+(?P<icon>✅|🟡|⬜|🚧|⚠️)\s+\[(?P<tag>Apple|Google|Both)\]\s+"
    r"(?P<body>.+?)\s*<!--\s*id:\s*(?P<id>[a-z0-9.\-]+)\s*-->\s*$"
)
SECTION_RE = re.compile(r"^##\s+(?P<num>\d+)\.\s+(?P<title>.+)$")
DEV_NOTE_RE = re.compile(
    r"^\s*>\s*_Dev note\s*\((?P<date>\d{4}-\d{2}-\d{2})\):\s*(?P<text>.+?)_\s*$"
)
HISTORY_LINE_RE = re.compile(
    r"^-\s+(?P<date>\d{4}-\d{2}-\d{2})\s+—\s+(?P<text>.+)$"
)
HEADER_PLATFORMS_RE = re.compile(r"^\*\*Platforms:\*\*\s+(?P<value>.+)$")
HEADER_APP_RE = re.compile(r"^\*\*App:\*\*\s+(?P<name>.+?)\s+\(`(?P<bundle>[^`]+)`\)$")
HEADER_FRAMEWORK_RE = re.compile(r"^\*\*Framework:\*\*\s+(?P<value>.+)$")
HEADER_AUDIT_RE = re.compile(r"^\*\*Last audit:\*\*\s+(?P<value>.+)$")


def parse_roadmap(text: str) -> dict:
    state = {
        "header": {
            "platforms": [],
            "app_name": None,
            "bundle_id": None,
            "framework": None,
            "last_audit": None,
        },
        "items": [],
        "history": [],
    }

    section_num = None
    in_history = False
    current_item = None

    for line in text.splitlines():
        # Header lines (anywhere before sections)
        if (m := HEADER_PLATFORMS_RE.match(line)):
            state["header"]["platforms"] = [p.strip() for p in m["value"].split(",")]
            continue
        if (m := HEADER_APP_RE.match(line)):
            state["header"]["app_name"] = m["name"].strip()
            state["header"]["bundle_id"] = m["bundle"].strip()
            continue
        if (m := HEADER_FRAMEWORK_RE.match(line)):
            state["header"]["framework"] = m["value"].strip()
            continue
        if (m := HEADER_AUDIT_RE.match(line)):
            state["header"]["last_audit"] = m["value"].strip()
            continue

        # Section transitions
        if (m := SECTION_RE.match(line)):
            section_num = int(m["num"])
            in_history = False
            current_item = None
            continue
        if line.strip().lower().startswith("## notes & history"):
            section_num = None
            in_history = True
            current_item = None
            continue

        if in_history:
            if (m := HISTORY_LINE_RE.match(line)):
                state["history"].append({"date": m["date"], "text": m["text"].strip()})
            continue

        # Item lines (must have id comment)
        if section_num is not None and (m := ITEM_RE.match(line)):
            body = m["body"].strip()
            # Split body into title and evidence at em-dash if present
            if " — " in body:
                title, evidence = body.split(" — ", 1)
            else:
                title, evidence = body, ""
            current_item = {
                "id": m["id"],
                "section": section_num,
                "title": title.strip(),
                "platform_tag": m["tag"],
                "status": STATUS_BY_ICON[m["icon"]],
                "evidence": evidence.strip(),
                "next_action": None,
                "dev_notes": [],
            }
            state["items"].append(current_item)
            continue

        # Dev note blockquote (attaches to current item)
        if current_item is not None and (m := DEV_NOTE_RE.match(line)):
            current_item["dev_notes"].append(
                {"date": m["date"], "text": m["text"].strip()}
            )
            continue

    return state


def cmd_parse(args: argparse.Namespace) -> int:
    if not args.path.exists():
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 1
    text = args.path.read_text(encoding="utf-8")
    state = parse_roadmap(text)
    json.dump(state, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


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
