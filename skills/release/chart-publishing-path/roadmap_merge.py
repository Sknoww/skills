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


STATUS_RANK = {"pending": 0, "blocked": 1, "partial": 2, "done": 3,
               "recheck": 0, "not-applicable": -1}


def merge_states(existing: dict, findings: dict) -> dict:
    merged = {
        "header": dict(existing.get("header", {})),
        "items": [],
        "history": list(existing.get("history", [])),
    }
    audit_date = findings.get("audit_date", "")

    existing_by_id = {it["id"]: it for it in existing.get("items", [])}
    finding_by_id = {it["id"]: it for it in findings.get("items", [])}

    counts = {"done": 0, "partial": 0, "pending": 0, "blocked": 0, "recheck": 0}

    # Apply findings to existing items + add new ones.
    for fid, finding in finding_by_id.items():
        if finding["status"] == "not-applicable":
            merged["history"].append({
                "date": audit_date,
                "text": f"`{fid}` no longer applicable on {audit_date}.",
            })
            continue

        prior = existing_by_id.get(fid)
        if prior is None:
            new_item = {
                "id": fid,
                "section": finding["section"],
                "title": finding["title"],
                "platform_tag": finding["platform_tag"],
                "status": finding["status"],
                "evidence": finding.get("evidence", ""),
                "next_action": finding.get("next_action"),
                "dev_notes": [],
            }
            merged["items"].append(new_item)
            counts[new_item["status"]] = counts.get(new_item["status"], 0) + 1
            continue

        # Existing item — apply status transition rules.
        prior_rank = STATUS_RANK.get(prior["status"], 0)
        new_rank = STATUS_RANK.get(finding["status"], 0)

        if new_rank < prior_rank and prior["status"] != "recheck":
            # Regression — mark recheck, keep dev notes, append audit evidence.
            merged_item = dict(prior)
            merged_item["status"] = "recheck"
            old_ev = prior.get("evidence", "")
            new_ev = finding.get("evidence", "")
            merged_item["evidence"] = (
                f"⚠️ regressed — previously: {old_ev}; now: {new_ev}"
                if old_ev else f"⚠️ regressed — {new_ev}"
            )
            merged_item["dev_notes"] = list(prior.get("dev_notes", []))
        else:
            merged_item = dict(prior)
            merged_item["status"] = finding["status"]
            merged_item["evidence"] = finding.get("evidence", "")
            merged_item["next_action"] = finding.get("next_action")
            merged_item["dev_notes"] = list(prior.get("dev_notes", []))

        merged["items"].append(merged_item)
        counts[merged_item["status"]] = counts.get(merged_item["status"], 0) + 1

    # Items in prior state but missing from new findings → history.
    for eid, prior in existing_by_id.items():
        if eid not in finding_by_id:
            merged["history"].append({
                "date": audit_date,
                "text": f"`{eid}` removed from audit guide on {audit_date}.",
            })

    # Pending history line for the orchestrator / render step.
    parts = [f"{counts[k]} {k}" for k in ("done", "partial", "pending",
                                           "blocked", "recheck") if counts.get(k)]
    prefix = "Re-run. " if existing_by_id else "Initial scaffold. "
    if parts:
        line_text = prefix + ", ".join(parts) + "."
    else:
        line_text = prefix + "(no items)."
    merged["pending_history_line"] = {"date": audit_date, "text": line_text}

    return merged


def cmd_merge(args: argparse.Namespace) -> int:
    existing = json.loads(args.existing_state.read_text(encoding="utf-8"))
    findings = json.loads(args.findings.read_text(encoding="utf-8"))
    result = merge_states(existing, findings)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def render_item(item: dict) -> list[str]:
    icon = ICON_BY_STATUS[item["status"]]
    title = item["title"]
    evidence = item.get("evidence") or ""
    body = f"{title} — {evidence}" if evidence else title
    line = (
        f"- {icon} [{item['platform_tag']}] {body} "
        f"<!-- id: {item['id']} -->"
    )
    lines = [line]
    for note in item.get("dev_notes", []):
        lines.append(f"  > _Dev note ({note['date']}): {note['text']}_")
    return lines


def render_state(state: dict, metadata: dict, template: str) -> str:
    # Count statuses.
    counts = {"done": 0, "partial": 0, "pending": 0, "blocked": 0, "recheck": 0}
    for it in state["items"]:
        counts[it["status"]] = counts.get(it["status"], 0) + 1

    # Group items by section.
    by_section = {n: [] for n in range(1, 11)}
    for it in state["items"]:
        by_section[it["section"]].append(it)

    # Render each section block.
    section_blocks = {}
    for n in range(1, 11):
        items = by_section[n]
        if not items:
            section_blocks[n] = "_(no items)_"
        else:
            block_lines = []
            for it in items:
                block_lines.extend(render_item(it))
            section_blocks[n] = "\n".join(block_lines)

    # History (append pending_history_line if present, but not into state).
    history_lines = [f"- {h['date']} — {h['text']}" for h in state.get("history", [])]
    pending = state.get("pending_history_line")
    if pending:
        history_lines.append(f"- {pending['date']} — {pending['text']}")
    history_block = "\n".join(history_lines) if history_lines else "_(no history yet)_"

    substitutions = {
        "{{GENERATED_DATE}}": metadata["generated_date"],
        "{{PLATFORMS}}": ", ".join(metadata["platforms"]),
        "{{APP_NAME}}": metadata["app_name"],
        "{{BUNDLE_ID}}": metadata["bundle_id"],
        "{{FRAMEWORK}}": metadata["framework"],
        "{{LAST_AUDIT_DATE}}": metadata["last_audit_date"],
        "{{COUNT_DONE}}": str(counts["done"]),
        "{{COUNT_IN_PROGRESS}}": str(counts["partial"]),
        "{{COUNT_PENDING}}": str(counts["pending"]),
        "{{COUNT_BLOCKED}}": str(counts["blocked"]),
        "{{COUNT_RECHECK}}": str(counts["recheck"]),
        "{{HISTORY_LOG}}": history_block,
    }
    for n in range(1, 11):
        substitutions[f"{{{{ITEMS_SECTION_{n}}}}}"] = section_blocks[n]

    output = template
    for k, v in substitutions.items():
        output = output.replace(k, v)
    return output


def cmd_render(args: argparse.Namespace) -> int:
    state = json.loads(args.state.read_text(encoding="utf-8"))
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    template_path = Path(metadata["template_path"])
    template = template_path.read_text(encoding="utf-8")
    output = render_state(state, metadata, template)
    sys.stdout.write(output)
    return 0


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
    # Ensure stdout is UTF-8 on Windows (default may be cp1252).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
