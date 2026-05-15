# Probe-Library Handoff, Progress Tracking & Install Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every probe-library handoff emit a literal copy-pasteable slash command, add a per-feature STATUS.md progress tracker, disambiguate bare issue numbers across features, and give the install scripts an up-front global-choice + flags.

**Architecture:** A new deterministic Python helper `scripts/status_update.py` owns all STATUS.md reads/writes (mirroring how `roadmap_merge.py` serves chart-publishing-path and `estimate_tokens.py` serves slice-issues). It is bundled into the `slice-issues` skill folder so it ships to `~/.claude/skills/slice-issues/status_update.py`, the same path convention `execute-issue` already uses for `estimate_tokens.py`. SKILL.md files are edited to call the helper and to emit literal slash commands. Install scripts get a shared up-front collision-mode decision plus non-interactive flags.

**Tech Stack:** Python 3 (stdlib only), pytest, Bash, PowerShell, Markdown.

**Repo conventions discovered (follow these):**
- Canonical scripts live in `scripts/`; an **identical copy** is bundled into the consuming skill folder. `scripts/estimate_tokens.py` == `skills/plan/slice-issues/estimate_tokens.py`; `scripts/roadmap_merge.py` == `skills/release/chart-publishing-path/roadmap_merge.py`. Tests reference the `scripts/` copy.
- Tests are pytest in `tests/`, invoking scripts as subprocesses via `subprocess.run([sys.executable, str(SCRIPT), ...])` with `encoding="utf-8"`.
- Issue files: `docs/features/<slug>/issues/NNN-<slug>.md`. Slice type is the line `## Slice type: vertical` (or `skeleton`). `execute-issue` appends `- **Date:** <YYYY-MM-DD>` under `## Execution log (filled by execute-issue)`. `verify-issue` appends `- **Date:** <YYYY-MM-DD>` and a `- **Code review:** <verdict> — ...` line under `## Review verdict (filled by verify-issue)`.
- `SEQUENCE.md` lives at `docs/features/<slug>/issues/SEQUENCE.md` and lists issues as `- 001 — <title>` lines grouped by `### Layer N` headings.

---

## File Structure

| File | Responsibility | Action |
|------|----------------|--------|
| `scripts/status_update.py` | Canonical STATUS.md helper: `seed`, `mark-executed`, `mark-verified`, `regen`, `next` | Create |
| `skills/plan/slice-issues/status_update.py` | Byte-identical bundled copy (ships with skill) | Create |
| `tests/test_status_update.py` | pytest coverage for the helper | Create |
| `tests/test_skill_handoffs.py` | Lint guard: chained SKILL.md report lines emit literal slash commands, no `<NNN>`/`...` placeholders | Create |
| `skills/plan/slice-issues/SKILL.md` | Seed STATUS.md; emit `/sequence-issues <slug>` | Modify |
| `skills/plan/sequence-issues/SKILL.md` | Read STATUS.md for next; never write it; emit fully-qualified `/execute-issue <slug>/<NNN-name>` | Modify |
| `skills/implement/execute-issue/SKILL.md` | Slug disambiguation; self-heal+mark STATUS.md; emit fully-qualified next | Modify |
| `skills/implement/verify-issue/SKILL.md` | Slug disambiguation; mark STATUS.md; emit fully-qualified next | Modify |
| `skills/shape/shape-feature/SKILL.md` | Emit `/probe-feature <slug>` | Modify |
| `skills/flow/probe-feature/SKILL.md` | Accept slug arg; emit `/slice-issues <slug>` | Modify |
| `skills/discover/probe-product/SKILL.md` | Accept slug arg; emit `/probe-design <slug>` + `/probe-technical <slug>` | Modify |
| `skills/discover/probe-design/SKILL.md` | Accept slug arg; emit remaining-probe/`/write-prd <slug>` | Modify |
| `skills/discover/probe-technical/SKILL.md` | Accept slug arg; emit remaining-probe/`/write-prd <slug>` | Modify |
| `skills/synthesize/write-prd/SKILL.md` | Accept slug arg; emit `/write-design-brief <slug>` + `/write-tech-spec <slug>` | Modify |
| `skills/synthesize/write-design-brief/SKILL.md` | Accept slug arg; emit `/write-tech-spec <slug>` | Modify |
| `skills/synthesize/write-tech-spec/SKILL.md` | Accept slug arg; emit `/slice-issues <slug>` | Modify |
| `skills/integrate/publish-issues/SKILL.md` | Accept slug arg (already asks) — document it | Modify |
| `install.sh` | `--overwrite/--skip/--archive` flags + up-front 4-way global prompt | Modify |
| `install.ps1` | `-Overwrite/-Skip/-Archive` flags + up-front 4-way global prompt | Modify |
| `README.md` | Document new install flags and STATUS.md | Modify |

---

## Task 1: status_update.py — `seed` and STATUS.md (de)serialization

**Files:**
- Create: `scripts/status_update.py`
- Test: `tests/test_status_update.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_status_update.py
import subprocess
import sys
import textwrap
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "status_update.py"


def run(args, cwd=None):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", cwd=cwd,
    )
    return result.stdout, result.stderr, result.returncode


def make_issue(issues_dir: Path, name: str, slice_type: str = "vertical"):
    (issues_dir / f"{name}.md").write_text(
        textwrap.dedent(f"""\
            # Issue {name}: demo

            ## Slice type: {slice_type}

            ## Execution log (filled by execute-issue)
            - **Token budget actual:** <filled post-run>

            ## Review verdict (filled by verify-issue)
            - **Code review:** PASS | FAIL | NEEDS_USER — <summary>
            """),
        encoding="utf-8",
    )


def test_no_args_shows_usage():
    out, err, code = run([])
    assert code != 0
    assert "usage" in (out + err).lower()


def test_seed_creates_status_with_all_dashes(tmp_path):
    feature = tmp_path / "docs" / "features" / "demo"
    issues = feature / "issues"
    issues.mkdir(parents=True)
    make_issue(issues, "001-alpha")
    make_issue(issues, "002-beta", slice_type="skeleton")

    out, err, code = run(
        ["seed", "--feature-dir", str(feature), "--name", "Demo", "--slug", "demo"]
    )
    assert code == 0, err
    status = (issues / "STATUS.md").read_text(encoding="utf-8")
    assert "# Status — Demo (demo)" in status
    assert "| 001-alpha | vertical | — | — |" in status
    assert "| 002-beta | skeleton | — | — |" in status
    assert "**Feature status:** in-progress — 0/2 executed, 0/2 verified" in status
    assert "## Notes" in status


def test_seed_preserves_existing_notes(tmp_path):
    feature = tmp_path / "docs" / "features" / "demo"
    issues = feature / "issues"
    issues.mkdir(parents=True)
    make_issue(issues, "001-alpha")
    (issues / "STATUS.md").write_text(
        "# Status — Demo (demo)\n\n## Notes\nkeep me\n", encoding="utf-8"
    )

    out, err, code = run(
        ["seed", "--feature-dir", str(feature), "--name", "Demo", "--slug", "demo"]
    )
    assert code == 0, err
    status = (issues / "STATUS.md").read_text(encoding="utf-8")
    assert "keep me" in status
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_status_update.py -v`
Expected: FAIL — `status_update.py` does not exist (collection error / non-zero).

- [ ] **Step 3: Write the minimal implementation**

```python
# scripts/status_update.py
"""STATUS.md helper for the probe-feature skill library.

Owns all reads/writes of docs/features/<slug>/issues/STATUS.md.
Subcommands: seed, mark-executed, mark-verified, regen, next.

The Notes section is user-owned and always preserved verbatim.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DASH = "—"
TABLE_HEADER = "| Issue | Slice | Executed | Verified |"
TABLE_SEP = "|-------|-------|----------|----------|"


def issue_files(issues_dir: Path):
    """Return sorted list of NNN-*.md issue stems (excludes STATUS/SEQUENCE)."""
    out = []
    for p in sorted(issues_dir.glob("[0-9][0-9][0-9]-*.md")):
        if p.name in ("STATUS.md", "SEQUENCE.md"):
            continue
        out.append(p)
    return out


def slice_type_of(issue_path: Path) -> str:
    for line in issue_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"##\s*Slice type:\s*(\S+)", line)
        if m:
            return m.group(1).strip()
    return "vertical"


def parse_notes(status_path: Path) -> str:
    """Extract the body after the '## Notes' heading, or a default."""
    if not status_path.exists():
        return "<freeform; preserved across regenerations>\n"
    text = status_path.read_text(encoding="utf-8")
    idx = text.find("\n## Notes")
    if idx == -1:
        return "<freeform; preserved across regenerations>\n"
    body = text[idx + len("\n## Notes"):].lstrip("\n")
    return body if body.strip() else "<freeform; preserved across regenerations>\n"


def parse_rows(status_path: Path) -> dict:
    """Return {issue_stem: {'slice':, 'executed':, 'verified':}} from an
    existing STATUS.md table. Empty dict if no file/table."""
    rows = {}
    if not status_path.exists():
        return rows
    for line in status_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0] in ("Issue", "-------"):
            continue
        if set(cells[0]) <= set("-"):
            continue
        rows[cells[0]] = {
            "slice": cells[1],
            "executed": cells[2],
            "verified": cells[3],
        }
    return rows


def render(name: str, slug: str, ordered_stems: list, rows: dict, notes: str) -> str:
    n = len(ordered_stems)
    n_exec = sum(1 for s in ordered_stems if rows[s]["executed"] != DASH)
    n_ver = sum(1 for s in ordered_stems if rows[s]["verified"] != DASH)
    all_pass = n > 0 and all(
        rows[s]["verified"].endswith("PASS") for s in ordered_stems
    )
    feat = "complete" if all_pass else (
        f"in-progress — {n_exec}/{n} executed, {n_ver}/{n} verified"
    )
    lines = [
        f"# Status — {name} ({slug})",
        "",
        "Generated by slice-issues; updated by execute-issue / verify-issue.",
        "Do not hand-edit the table. The Notes section is yours and is preserved.",
        "",
        TABLE_HEADER,
        TABLE_SEP,
    ]
    for s in ordered_stems:
        r = rows[s]
        lines.append(f"| {s} | {r['slice']} | {r['executed']} | {r['verified']} |")
    lines += ["", f"**Feature status:** {feat}", "", "## Notes", "", notes.rstrip() + "\n"]
    return "\n".join(lines)


def load_state(feature_dir: Path):
    issues_dir = feature_dir / "issues"
    status_path = issues_dir / "STATUS.md"
    stems = [p.stem for p in issue_files(issues_dir)]
    old = parse_rows(status_path)
    rows = {}
    for stem in stems:
        prev = old.get(stem, {})
        rows[stem] = {
            "slice": slice_type_of(issues_dir / f"{stem}.md"),
            "executed": prev.get("executed", DASH),
            "verified": prev.get("verified", DASH),
        }
    return issues_dir, status_path, stems, rows


def write_status(args, transform=None):
    feature_dir = Path(args.feature_dir)
    issues_dir, status_path, stems, rows = load_state(feature_dir)
    if not stems:
        print(f"No issue files in {issues_dir}", file=sys.stderr)
        return 1
    if transform:
        err = transform(rows)
        if err:
            print(err, file=sys.stderr)
            return 1
    notes = parse_notes(status_path)
    status_path.write_text(
        render(args.name, args.slug, stems, rows, notes), encoding="utf-8"
    )
    print(f"Wrote {status_path}")
    return 0


def cmd_seed(args):
    return write_status(args)


def build_parser():
    p = argparse.ArgumentParser(description="STATUS.md helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("seed", help="Create/refresh STATUS.md from issue files")
    sp.add_argument("--feature-dir", required=True)
    sp.add_argument("--name", required=True)
    sp.add_argument("--slug", required=True)
    sp.set_defaults(func=cmd_seed)
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_status_update.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/status_update.py tests/test_status_update.py
git commit -m "feat(status): add status_update.py seed + STATUS.md (de)serialization"
```

---

## Task 2: status_update.py — `mark-executed` and `mark-verified`

**Files:**
- Modify: `scripts/status_update.py`
- Test: `tests/test_status_update.py`

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_status_update.py`:

```python
def _seed(tmp_path):
    feature = tmp_path / "docs" / "features" / "demo"
    issues = feature / "issues"
    issues.mkdir(parents=True)
    make_issue(issues, "001-alpha")
    make_issue(issues, "002-beta")
    run(["seed", "--feature-dir", str(feature), "--name", "Demo", "--slug", "demo"])
    return feature, issues


def test_mark_executed_sets_date(tmp_path):
    feature, issues = _seed(tmp_path)
    out, err, code = run([
        "mark-executed", "--feature-dir", str(feature), "--name", "Demo",
        "--slug", "demo", "--issue", "001-alpha", "--date", "2026-05-15",
    ])
    assert code == 0, err
    status = (issues / "STATUS.md").read_text(encoding="utf-8")
    assert "| 001-alpha | vertical | 2026-05-15 | — |" in status
    assert "**Feature status:** in-progress — 1/2 executed, 0/2 verified" in status


def test_mark_executed_with_status_suffix(tmp_path):
    feature, issues = _seed(tmp_path)
    run([
        "mark-executed", "--feature-dir", str(feature), "--name", "Demo",
        "--slug", "demo", "--issue", "002-beta", "--date", "2026-05-15",
        "--status", "BLOCKED",
    ])
    status = (issues / "STATUS.md").read_text(encoding="utf-8")
    assert "| 002-beta | vertical | 2026-05-15 BLOCKED | — |" in status


def test_mark_verified_sets_verdict_and_complete(tmp_path):
    feature, issues = _seed(tmp_path)
    for stem in ("001-alpha", "002-beta"):
        run([
            "mark-executed", "--feature-dir", str(feature), "--name", "Demo",
            "--slug", "demo", "--issue", stem, "--date", "2026-05-15",
        ])
        out, err, code = run([
            "mark-verified", "--feature-dir", str(feature), "--name", "Demo",
            "--slug", "demo", "--issue", stem, "--date", "2026-05-15",
            "--verdict", "PASS",
        ])
        assert code == 0, err
    status = (issues / "STATUS.md").read_text(encoding="utf-8")
    assert "| 001-alpha | vertical | 2026-05-15 | 2026-05-15 PASS |" in status
    assert "**Feature status:** complete" in status


def test_mark_unknown_issue_errors(tmp_path):
    feature, issues = _seed(tmp_path)
    out, err, code = run([
        "mark-executed", "--feature-dir", str(feature), "--name", "Demo",
        "--slug", "demo", "--issue", "099-nope", "--date", "2026-05-15",
    ])
    assert code != 0
    assert "099-nope" in err
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_status_update.py -k "mark" -v`
Expected: FAIL — `invalid choice: 'mark-executed'`.

- [ ] **Step 3: Implement the two subcommands**

In `scripts/status_update.py`, add these functions above `build_parser`:

```python
def _require_issue(rows, stem):
    if stem not in rows:
        return f"Issue '{stem}' not found among issue files."
    return None


def cmd_mark_executed(args):
    def t(rows):
        err = _require_issue(rows, args.issue)
        if err:
            return err
        val = args.date
        if args.status and args.status != "DONE":
            val = f"{args.date} {args.status}"
        rows[args.issue]["executed"] = val
        return None
    return write_status(args, t)


def cmd_mark_verified(args):
    def t(rows):
        err = _require_issue(rows, args.issue)
        if err:
            return err
        rows[args.issue]["verified"] = f"{args.date} {args.verdict}"
        return None
    return write_status(args, t)
```

In `build_parser`, add after the `seed` block (before `return p`):

```python
    me = sub.add_parser("mark-executed", help="Set the Executed cell")
    me.add_argument("--feature-dir", required=True)
    me.add_argument("--name", required=True)
    me.add_argument("--slug", required=True)
    me.add_argument("--issue", required=True, help="Issue stem, e.g. 001-alpha")
    me.add_argument("--date", required=True)
    me.add_argument("--status", choices=["DONE", "BLOCKED", "NEEDS_USER"],
                    default="DONE")
    me.set_defaults(func=cmd_mark_executed)

    mv = sub.add_parser("mark-verified", help="Set the Verified cell")
    mv.add_argument("--feature-dir", required=True)
    mv.add_argument("--name", required=True)
    mv.add_argument("--slug", required=True)
    mv.add_argument("--issue", required=True, help="Issue stem, e.g. 001-alpha")
    mv.add_argument("--date", required=True)
    mv.add_argument("--verdict", required=True,
                    choices=["PASS", "FAIL", "NEEDS_USER"])
    mv.set_defaults(func=cmd_mark_verified)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_status_update.py -v`
Expected: PASS (all tests including the 4 `mark` tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/status_update.py tests/test_status_update.py
git commit -m "feat(status): add mark-executed / mark-verified subcommands"
```

---

## Task 3: status_update.py — `next` and `regen`

**Files:**
- Modify: `scripts/status_update.py`
- Test: `tests/test_status_update.py`

`next` computes the next slash command. Ordering: read `SEQUENCE.md` if present (parse `- NNN — title` lines top-to-bottom across `### Layer` sections); else fall back to numeric stem order. `--stage execute` picks the first stem whose `executed == —`; `--stage verify` picks the first whose `verified == —`. Output is the literal command string. `regen` rebuilds executed/verified from each issue file's Execution log / Review verdict sections (self-heal when STATUS.md is missing/stale).

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_status_update.py`:

```python
def test_next_execute_returns_first_unexecuted(tmp_path):
    feature, issues = _seed(tmp_path)
    run([
        "mark-executed", "--feature-dir", str(feature), "--name", "Demo",
        "--slug", "demo", "--issue", "001-alpha", "--date", "2026-05-15",
    ])
    out, err, code = run([
        "next", "--feature-dir", str(feature), "--slug", "demo",
        "--stage", "execute",
    ])
    assert code == 0, err
    assert out.strip() == "/execute-issue demo/002-beta"


def test_next_verify_returns_first_unverified(tmp_path):
    feature, issues = _seed(tmp_path)
    out, err, code = run([
        "next", "--feature-dir", str(feature), "--slug", "demo",
        "--stage", "verify",
    ])
    assert out.strip() == "/verify-issue demo/001-alpha"


def test_next_all_done_signals_publish(tmp_path):
    feature, issues = _seed(tmp_path)
    for stem in ("001-alpha", "002-beta"):
        run(["mark-executed", "--feature-dir", str(feature), "--name", "Demo",
             "--slug", "demo", "--issue", stem, "--date", "2026-05-15"])
        run(["mark-verified", "--feature-dir", str(feature), "--name", "Demo",
             "--slug", "demo", "--issue", stem, "--date", "2026-05-15",
             "--verdict", "PASS"])
    out, err, code = run([
        "next", "--feature-dir", str(feature), "--slug", "demo",
        "--stage", "verify",
    ])
    assert out.strip() == "/publish-issues demo"


def test_next_honors_sequence_order(tmp_path):
    feature, issues = _seed(tmp_path)
    (issues / "SEQUENCE.md").write_text(
        "# Build Sequence\n\n### Layer 0\n- 002 — beta\n\n"
        "### Layer 1\n- 001 — alpha\n",
        encoding="utf-8",
    )
    out, err, code = run([
        "next", "--feature-dir", str(feature), "--slug", "demo",
        "--stage", "execute",
    ])
    assert out.strip() == "/execute-issue demo/002-beta"


def test_regen_rebuilds_from_issue_logs(tmp_path):
    feature = tmp_path / "docs" / "features" / "demo"
    issues = feature / "issues"
    issues.mkdir(parents=True)
    (issues / "001-alpha.md").write_text(textwrap.dedent("""\
        # Issue 001-alpha: demo

        ## Slice type: vertical

        ## Execution log (filled by execute-issue)
        - **Token budget actual:** 1234
        - **Date:** 2026-05-10

        ## Review verdict (filled by verify-issue)
        - **Code review:** PASS — looks good
        - **Date:** 2026-05-11
        """), encoding="utf-8")
    make_issue(issues, "002-beta")  # untouched logs
    out, err, code = run([
        "regen", "--feature-dir", str(feature), "--name", "Demo",
        "--slug", "demo",
    ])
    assert code == 0, err
    status = (issues / "STATUS.md").read_text(encoding="utf-8")
    assert "| 001-alpha | vertical | 2026-05-10 | 2026-05-11 PASS |" in status
    assert "| 002-beta | vertical | — | — |" in status
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_status_update.py -k "next or regen" -v`
Expected: FAIL — `invalid choice: 'next'` / `'regen'`.

- [ ] **Step 3: Implement `next` and `regen`**

In `scripts/status_update.py`, add above `build_parser`:

```python
def sequence_order(issues_dir: Path, stems: list) -> list:
    """Order stems by SEQUENCE.md if present, else numeric stem order."""
    seq = issues_dir / "SEQUENCE.md"
    if not seq.exists():
        return sorted(stems)
    by_num = {}
    for stem in stems:
        by_num.setdefault(stem.split("-", 1)[0], stem)
    ordered, seen = [], set()
    for line in seq.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*-\s*(\d{3})\b", line)
        if not m:
            continue
        stem = by_num.get(m.group(1))
        if stem and stem not in seen:
            ordered.append(stem)
            seen.add(stem)
    for stem in sorted(stems):  # any stems missing from SEQUENCE.md
        if stem not in seen:
            ordered.append(stem)
    return ordered


def cmd_next(args):
    feature_dir = Path(args.feature_dir)
    issues_dir, status_path, stems, rows = load_state(feature_dir)
    if not stems:
        print(f"No issue files in {issues_dir}", file=sys.stderr)
        return 1
    ordered = sequence_order(issues_dir, stems)
    key = "executed" if args.stage == "execute" else "verified"
    skill = "execute-issue" if args.stage == "execute" else "verify-issue"
    for stem in ordered:
        if rows[stem][key] == DASH:
            print(f"/{skill} {args.slug}/{stem}")
            return 0
    if args.stage == "verify":
        print(f"/publish-issues {args.slug}")
    else:
        print(f"/verify-issue {args.slug}/{ordered[-1]}")
    return 0


def _section(text: str, header: str) -> str:
    idx = text.find(header)
    if idx == -1:
        return ""
    rest = text[idx + len(header):]
    nxt = rest.find("\n## ")
    return rest if nxt == -1 else rest[:nxt]


def cmd_regen(args):
    def t(rows):
        issues_dir = Path(args.feature_dir) / "issues"
        for stem in rows:
            text = (issues_dir / f"{stem}.md").read_text(encoding="utf-8")
            exe = _section(text, "## Execution log (filled by execute-issue)")
            ver = _section(text, "## Review verdict (filled by verify-issue)")
            m = re.search(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})", exe)
            if m:
                rows[stem]["executed"] = m.group(1)
            vm = re.search(r"\*\*Code review:\*\*\s*(PASS|FAIL|NEEDS_USER)\b", ver)
            vd = re.search(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})", ver)
            if vm and vm.group(1) in ("PASS", "FAIL", "NEEDS_USER"):
                date = vd.group(1) if vd else ""
                rows[stem]["verified"] = f"{date} {vm.group(1)}".strip()
        return None
    return write_status(args, t)
```

In `build_parser`, add before `return p`:

```python
    nx = sub.add_parser("next", help="Print the next slash command")
    nx.add_argument("--feature-dir", required=True)
    nx.add_argument("--slug", required=True)
    nx.add_argument("--stage", required=True, choices=["execute", "verify"])
    nx.set_defaults(func=cmd_next)

    rg = sub.add_parser("regen", help="Rebuild STATUS.md from issue logs")
    rg.add_argument("--feature-dir", required=True)
    rg.add_argument("--name", required=True)
    rg.add_argument("--slug", required=True)
    rg.set_defaults(func=cmd_regen)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_status_update.py -v`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/status_update.py tests/test_status_update.py
git commit -m "feat(status): add next + regen subcommands"
```

---

## Task 4: Bundle status_update.py into slice-issues + parity test

**Files:**
- Create: `skills/plan/slice-issues/status_update.py`
- Test: `tests/test_status_update.py`

- [ ] **Step 1: Add the failing parity test**

Append to `tests/test_status_update.py`:

```python
def test_bundled_copy_is_identical():
    canonical = (Path(__file__).resolve().parent.parent
                 / "scripts" / "status_update.py")
    bundled = (Path(__file__).resolve().parent.parent
               / "skills" / "plan" / "slice-issues" / "status_update.py")
    assert bundled.exists(), "bundled status_update.py missing"
    assert bundled.read_bytes() == canonical.read_bytes(), (
        "bundled copy drifted from scripts/status_update.py"
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_status_update.py -k bundled -v`
Expected: FAIL — bundled file missing.

- [ ] **Step 3: Create the byte-identical copy**

Run:

```bash
cp scripts/status_update.py skills/plan/slice-issues/status_update.py
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_status_update.py -v`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add skills/plan/slice-issues/status_update.py tests/test_status_update.py
git commit -m "feat(status): bundle status_update.py into slice-issues skill"
```

---

## Task 5: slice-issues SKILL.md — seed STATUS.md, emit literal next

**Files:**
- Modify: `skills/plan/slice-issues/SKILL.md`

- [ ] **Step 1: Add the Preconditions line for the bundled helper**

In `## Preconditions (HARD)`, replace:

```
The bundled `ISSUE-TEMPLATE.md` and `estimate_tokens.py` must be in this skill's folder.
```

with:

```
The bundled `ISSUE-TEMPLATE.md`, `estimate_tokens.py`, and `status_update.py` must be in this skill's folder.
```

- [ ] **Step 2: Add a STATUS.md seeding step**

After `### 8. Write all issues`, insert a new step:

```markdown
### 8.5. Seed the progress tracker

After all issue files are written, seed `STATUS.md`. After install the helper
is a flat sibling at `~/.claude/skills/slice-issues/status_update.py`:

```
python ~/.claude/skills/slice-issues/status_update.py seed \
  --feature-dir docs/features/<slug> \
  --name "<feature name>" --slug <slug>
```

This writes `docs/features/<slug>/issues/STATUS.md` with every issue and all
cells `—`. If the script isn't found at that path (non-standard install),
note `STATUS.md: unseeded — helper not found` and continue; execute-issue
will self-heal it on first run.
```

- [ ] **Step 3: Replace the report line with a literal command**

Replace step 9's report block:

```
> "Wrote <N> issues to `docs/features/<slug>/issues/`. <count vertical / count skeleton>. Token budget summary: <min>k / <median>k / <max>k. Next: `sequence-issues` to build the dependency order."
```

with:

```
> "Wrote <N> issues to `docs/features/<slug>/issues/` and seeded `STATUS.md`. <count vertical / count skeleton>. Token budget summary: <min>k / <median>k / <max>k.
>
> Next — run: `/sequence-issues <slug>`"
```

- [ ] **Step 4: Verify the edits**

Run: `python -m pytest tests/test_skill_handoffs.py -v` (added in Task 10 — if not yet present, defer this check to Task 10).
Manual: re-read `skills/plan/slice-issues/SKILL.md` and confirm the three edits landed and `<slug>` is the literal placeholder the engineer substitutes at runtime.

- [ ] **Step 5: Commit**

```bash
git add skills/plan/slice-issues/SKILL.md
git commit -m "feat(slice-issues): seed STATUS.md and emit literal /sequence-issues command"
```

---

## Task 6: sequence-issues SKILL.md — read STATUS.md, emit fully-qualified next, never write

**Files:**
- Modify: `skills/plan/sequence-issues/SKILL.md`

- [ ] **Step 1: Replace the report line**

Replace step 6's block:

```
> "Wrote `docs/features/<slug>/issues/SEQUENCE.md`. <N> layers, max parallelism <M>. Next: `execute-issue 001-...` to begin."
```

with:

```
> "Wrote `docs/features/<slug>/issues/SEQUENCE.md`. <N> layers, max parallelism <M>.
>
> Next — run: `<next-command>`"

Compute `<next-command>` from STATUS.md + this sequence (the helper ships at
`~/.claude/skills/slice-issues/status_update.py`):

```
python ~/.claude/skills/slice-issues/status_update.py next \
  --feature-dir docs/features/<slug> --slug <slug> --stage execute
```

Print its stdout verbatim as `<next-command>` (e.g.
`/execute-issue <slug>/001-<name>`). If STATUS.md is absent, fall back to
`/execute-issue <slug>/<first issue in Layer 0>`.
```

- [ ] **Step 2: Add a Rule that sequence-issues never writes STATUS.md**

In `## Rules`, append:

```
- `sequence-issues` READS `STATUS.md` only to compute the next command. It MUST NOT create or modify `STATUS.md` — that file is owned by slice-issues / execute-issue / verify-issue. A re-sequence still only rewrites `SEQUENCE.md`.
```

- [ ] **Step 3: Accept the slug as an argument**

In `### 1. Resolve slug + read all issues`, replace the first sentence:

```
Read every `NNN-*.md` in `docs/features/<slug>/issues/`.
```

with:

```
The slug may be supplied as the first argument (e.g. `/sequence-issues payments-v2`). If absent, ask for it. Then read every `NNN-*.md` in `docs/features/<slug>/issues/`.
```

- [ ] **Step 4: Verify**

Manual: re-read `skills/plan/sequence-issues/SKILL.md`; confirm report emits a runnable command and the new Rule is present.

- [ ] **Step 5: Commit**

```bash
git add skills/plan/sequence-issues/SKILL.md
git commit -m "feat(sequence-issues): emit fully-qualified next command, never write STATUS.md"
```

---

## Task 7: execute-issue SKILL.md — slug disambiguation, STATUS.md self-heal+mark, literal next

**Files:**
- Modify: `skills/implement/execute-issue/SKILL.md`

- [ ] **Step 1: Replace step 1 with explicit slug-resolution rules**

Replace `### 1. Resolve target issue` body:

```
Argument: a path or NNN. Resolve to `docs/features/<slug>/issues/NNN-<slug>.md`. Read the full issue.
```

with:

```
Resolve the argument in this order:

1. **Contains `/` or is an existing path** (e.g. `payments-v2/003-add-webhook`
   or a full path) → use it directly.
2. **Bare `NNN` or `NNN-name`** → glob `docs/features/*/issues/NNN-*.md`:
   - **0 matches** → abort: "No issue `NNN` found under `docs/features/`."
   - **exactly 1 match** → use it.
   - **>1 matches → HARD STOP.** Do NOT guess. List every candidate as a
     fully-qualified command and require the user to re-run disambiguated:
     > "`NNN` is ambiguous across features. Re-run one of:
     > - `/execute-issue <slugA>/<NNN-name>`
     > - `/execute-issue <slugB>/<NNN-name>`"

Once resolved, derive `<slug>` from the path (`docs/features/<slug>/...`),
`<feature name>` from STATUS.md/probe-product if available, and read the full
issue.
```

- [ ] **Step 2: Add STATUS.md self-heal before execution**

After step 1, insert:

```markdown
### 1.5. Ensure STATUS.md exists (self-heal)

If `docs/features/<slug>/issues/STATUS.md` does not exist (feature predates
the tracker), regenerate it from existing issue logs:

```
python ~/.claude/skills/slice-issues/status_update.py regen \
  --feature-dir docs/features/<slug> \
  --name "<feature name>" --slug <slug>
```

If the helper is not found at that path, record
`STATUS.md: unmanaged — helper not found` in the Execution log and continue.
```

- [ ] **Step 3: Update STATUS.md in the Execution-log step**

In `### 6. Update Execution log`, after the existing bullet list, append:

```markdown
Then update the progress tracker (skip silently if the helper is not found):

```
python ~/.claude/skills/slice-issues/status_update.py mark-executed \
  --feature-dir docs/features/<slug> --name "<feature name>" --slug <slug> \
  --issue <NNN-name> --date <YYYY-MM-DD> --status <DONE|BLOCKED|NEEDS_USER>
```
```

- [ ] **Step 4: Replace the report line with a literal next command**

Replace step 7:

```
> "Issue <NNN> executed. Status: <DONE | BLOCKED | NEEDS_USER>. Token actual: <N> (estimated was <M>). Next: `verify-issue <NNN>`."
```

with:

```
> "Issue <NNN> executed. Status: <DONE | BLOCKED | NEEDS_USER>. Token actual: <N> (estimated was <M>).
>
> Next — run:
> - DONE → `/verify-issue <slug>/<NNN-name>`
> - BLOCKED / NEEDS_USER → fix the blocker, then re-run `/execute-issue <slug>/<NNN-name>`"
```

- [ ] **Step 5: Commit**

```bash
git add skills/implement/execute-issue/SKILL.md
git commit -m "feat(execute-issue): slug disambiguation, STATUS.md self-heal+mark, literal next"
```

---

## Task 8: verify-issue SKILL.md — slug disambiguation, STATUS.md mark, literal next

**Files:**
- Modify: `skills/implement/verify-issue/SKILL.md`

- [ ] **Step 1: Replace step 1 with the same slug-resolution rules**

Replace `### 1. Resolve target issue` body:

```
Argument: a path or NNN. Resolve to `docs/features/<slug>/issues/NNN-<slug>.md`. Read the full issue.
```

with (identical resolution rules as execute-issue, command name `/verify-issue`):

```
Resolve the argument in this order:

1. **Contains `/` or is an existing path** → use it directly.
2. **Bare `NNN` or `NNN-name`** → glob `docs/features/*/issues/NNN-*.md`:
   - **0 matches** → abort: "No issue `NNN` found under `docs/features/`."
   - **exactly 1 match** → use it.
   - **>1 matches → HARD STOP.** List every candidate as a fully-qualified
     command and require re-run disambiguated:
     > "`NNN` is ambiguous across features. Re-run one of:
     > - `/verify-issue <slugA>/<NNN-name>`
     > - `/verify-issue <slugB>/<NNN-name>`"

Derive `<slug>` from the resolved path and read the full issue.
```

- [ ] **Step 2: Mark STATUS.md after the verdict is written**

In `### 6. Append to issue's Review verdict section`, after the verdict block, append:

```markdown
Then update the progress tracker (skip silently if the helper is not found):

```
python ~/.claude/skills/slice-issues/status_update.py mark-verified \
  --feature-dir docs/features/<slug> --name "<feature name>" --slug <slug> \
  --issue <NNN-name> --date <YYYY-MM-DD> --verdict <PASS|FAIL|NEEDS_USER>
```

If STATUS.md does not exist, run the `regen` self-heal (see execute-issue
§1.5) first, then `mark-verified`.
```

- [ ] **Step 3: Replace the report line with literal next commands**

Replace step 7:

```
> "Issue <NNN> review: <verdict>. <QA doc path or 'no QA doc — skeleton issue'>. Next: <fix-and-re-verify | execute-issue NNN+1>."
```

with:

```
> "Issue <NNN> review: <verdict>. <QA doc path or 'no QA doc — skeleton issue'>.
>
> Next — run:"

Then compute and print the literal next command from the tracker:

```
python ~/.claude/skills/slice-issues/status_update.py next \
  --feature-dir docs/features/<slug> --slug <slug> --stage verify
```

- On **PASS**: print the helper's stdout (e.g.
  `/execute-issue <slug>/<next-NNN-name>`, or `/publish-issues <slug>`
  when every issue is verified PASS).
- On **FAIL / NEEDS_USER**: print `fix the issue, then re-run
  /verify-issue <slug>/<NNN-name>` instead of the helper output.
```

- [ ] **Step 4: Commit**

```bash
git add skills/implement/verify-issue/SKILL.md
git commit -m "feat(verify-issue): slug disambiguation, STATUS.md mark, literal next"
```

---

## Task 9: Literal next-command + slug-as-argument across the rest of the chain

Each sub-step is one SKILL.md. For every file: (a) ensure step 1 accepts the
slug as an optional first argument, falling back to asking; (b) replace the
final report `Next:` text with the literal slash command(s) below. Keep all
other content unchanged.

- [ ] **Step 1: shape-feature** — `skills/shape/shape-feature/SKILL.md`

In step 6, replace the **ready-to-probe** report line:

```
> "Wrote `docs/concepts/<slug>.md` (Status: ready-to-probe). Next: run `probe-feature` with slug `<slug>` — it will promote this concept into `docs/features/<slug>/concept.md` on entry."
```

with:

```
> "Wrote `docs/concepts/<slug>.md` (Status: ready-to-probe).
>
> Next — run: `/probe-feature <slug>` (it promotes this concept into `docs/features/<slug>/concept.md` on entry)."
```

(Leave the `shaping` and `shelved` report lines as-is — they have no single next command.)

- [ ] **Step 2: probe-feature** — `skills/flow/probe-feature/SKILL.md`

In `### 1. Get the feature identity`, before "Ask:", add:

```
The slug may be supplied as the first argument (e.g. `/probe-feature dark-mode-toggle`). If supplied, skip the slug question (still ask for the human-readable name if not derivable). Otherwise ask as below.
```

In step 5, replace:

```
> Next: `slice-issues` to break this into vertical-slice issues."
```

with:

```
>
> Next — run: `/slice-issues <slug>`"
```

- [ ] **Step 3: probe-product** — `skills/discover/probe-product/SKILL.md`

In `### 1. Identify the feature`, prepend:

```
If a slug was passed as the first argument (e.g. by `probe-feature` or `/probe-product dark-mode-toggle`), use it and skip the slug question. Otherwise ask as below.
```

Replace step 5's report:

```
> "Wrote `docs/features/<slug>/probe-product.md`. Next: run `probe-design` or `probe-technical` (parallel) — both must be done before `write-prd`."
```

with:

```
> "Wrote `docs/features/<slug>/probe-product.md`.
>
> Next — run both (parallel; both required before write-prd):
> - `/probe-design <slug>`
> - `/probe-technical <slug>`"
```

- [ ] **Step 4: probe-design** — `skills/discover/probe-design/SKILL.md`

`### 1. Identify the feature` already handles standalone vs. via-probe-feature; replace its standalone prompt block with:

```
If invoked standalone, the slug may be the first argument (e.g. `/probe-design dark-mode-toggle`); if not supplied, ask:
> "What is the feature slug? (lowercase-hyphenated)"

If invoked via `probe-feature`, the slug is passed in.
```

Replace step 5's report:

```
> "Wrote `docs/features/<slug>/probe-design.md`. Design system: `docs/design-system.md`. Next: `probe-product` / `probe-technical` (if not yet run), then `write-prd` + `write-design-brief`."
```

with:

```
> "Wrote `docs/features/<slug>/probe-design.md`. Design system: `docs/design-system.md`.
>
> Next — run any probe not yet done (`/probe-product <slug>`, `/probe-technical <slug>`); once all three probes exist, run `/write-prd <slug>`."
```

- [ ] **Step 5: probe-technical** — `skills/discover/probe-technical/SKILL.md`

`### 1. Identify the feature` currently reads "If invoked standalone, ask for the slug." Replace with:

```
If invoked standalone, the slug may be the first argument (e.g. `/probe-technical dark-mode-toggle`); if not supplied, ask for it. If invoked via `probe-feature`, the slug is passed in.
```

Replace step 6's report:

```
> "Wrote `docs/features/<slug>/probe-technical.md`. Tech spec depth signal: <full | module-map-only>. Next: `write-prd` (after all three probes complete), then `write-tech-spec`."
```

with:

```
> "Wrote `docs/features/<slug>/probe-technical.md`. Tech spec depth signal: <full | module-map-only>.
>
> Next — run any probe not yet done (`/probe-product <slug>`, `/probe-design <slug>`); once all three probes exist, run `/write-prd <slug>`."
```

- [ ] **Step 6: write-prd** — `skills/synthesize/write-prd/SKILL.md`

In `### 1. Resolve slug`, replace:

```
Ask for slug if not provided. Confirm all three probe files exist.
```

with:

```
The slug may be the first argument (e.g. `/write-prd dark-mode-toggle`). Ask for it only if not provided. Confirm all three probe files exist.
```

Replace step 6's report:

```
> "Wrote `docs/features/<slug>/prd.md`. Next: `write-design-brief` and `write-tech-spec`."
```

with:

```
> "Wrote `docs/features/<slug>/prd.md`.
>
> Next — run both: `/write-design-brief <slug>` and `/write-tech-spec <slug>`"
```

- [ ] **Step 7: write-design-brief** — `skills/synthesize/write-design-brief/SKILL.md`

Insert a new `### 1. Resolve slug` step before the current `### 1. Read inputs` (renumber the rest):

```markdown
### 1. Resolve slug

The slug may be the first argument (e.g. `/write-design-brief dark-mode-toggle`). Ask for it only if not provided.
```

Replace the report:

```
> "Wrote `docs/features/<slug>/design-brief.md`. Next: `write-tech-spec`, then `slice-issues`."
```

with:

```
> "Wrote `docs/features/<slug>/design-brief.md`.
>
> Next — run: `/write-tech-spec <slug>`"
```

- [ ] **Step 8: write-tech-spec** — `skills/synthesize/write-tech-spec/SKILL.md`

Insert a new `### 1. Resolve slug` step before the current `### 1. Read inputs` (renumber the rest):

```markdown
### 1. Resolve slug

The slug may be the first argument (e.g. `/write-tech-spec dark-mode-toggle`). Ask for it only if not provided.
```

Replace the report:

```
> "Wrote `docs/features/<slug>/tech-spec.md` (depth: <full | module-map-only>). Next: `slice-issues`."
```

with:

```
> "Wrote `docs/features/<slug>/tech-spec.md` (depth: <full | module-map-only>).
>
> Next — run: `/slice-issues <slug>`"
```

- [ ] **Step 9: publish-issues** — `skills/integrate/publish-issues/SKILL.md`

In `### 1. Resolve slug + verify gh`, replace:

```
Ask for slug if not provided. Run:
```

with:

```
The slug may be the first argument (e.g. `/publish-issues dark-mode-toggle`). Ask for it only if not provided. Run:
```

(publish-issues is a terminal step — no `Next:` line to change.)

- [ ] **Step 10: Commit**

```bash
git add skills/shape/shape-feature/SKILL.md skills/flow/probe-feature/SKILL.md skills/discover/probe-product/SKILL.md skills/discover/probe-design/SKILL.md skills/discover/probe-technical/SKILL.md skills/synthesize/write-prd/SKILL.md skills/synthesize/write-design-brief/SKILL.md skills/synthesize/write-tech-spec/SKILL.md skills/integrate/publish-issues/SKILL.md
git commit -m "feat(chain): emit literal slash commands and accept slug arg across the probe chain"
```

---

## Task 10: SKILL.md handoff lint test (regression guard)

**Files:**
- Create: `tests/test_skill_handoffs.py`

This guards against future placeholder regressions in the chained skills'
report lines.

- [ ] **Step 1: Write the test**

```python
# tests/test_skill_handoffs.py
import re
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parent.parent / "skills"

# (skill SKILL.md path, expected literal slash command substring)
CASES = [
    ("plan/slice-issues/SKILL.md", "/sequence-issues <slug>"),
    ("synthesize/write-tech-spec/SKILL.md", "/slice-issues <slug>"),
    ("synthesize/write-design-brief/SKILL.md", "/write-tech-spec <slug>"),
    ("synthesize/write-prd/SKILL.md", "/write-design-brief <slug>"),
    ("synthesize/write-prd/SKILL.md", "/write-tech-spec <slug>"),
    ("discover/probe-product/SKILL.md", "/probe-design <slug>"),
    ("discover/probe-product/SKILL.md", "/probe-technical <slug>"),
    ("discover/probe-design/SKILL.md", "/write-prd <slug>"),
    ("discover/probe-technical/SKILL.md", "/write-prd <slug>"),
    ("flow/probe-feature/SKILL.md", "/slice-issues <slug>"),
    ("shape/shape-feature/SKILL.md", "/probe-feature <slug>"),
    ("implement/execute-issue/SKILL.md", "/verify-issue <slug>/<NNN-name>"),
    ("implement/verify-issue/SKILL.md", "/verify-issue <slug>/<NNN-name>"),
]


@pytest.mark.parametrize("rel,needle", CASES)
def test_skill_emits_literal_command(rel, needle):
    text = (SKILLS / rel).read_text(encoding="utf-8")
    assert needle in text, f"{rel} missing literal command '{needle}'"


# Skills whose report line must not regress to bare placeholders.
NO_BARE = [
    "implement/execute-issue/SKILL.md",
    "implement/verify-issue/SKILL.md",
    "plan/sequence-issues/SKILL.md",
]


@pytest.mark.parametrize("rel", NO_BARE)
def test_no_bare_nnn_in_report(rel):
    text = (SKILLS / rel).read_text(encoding="utf-8")
    # The old broken patterns: `verify-issue <NNN>` / `execute-issue 001-...`
    # without a slash prefix or slug.
    assert not re.search(r"`(execute|verify)-issue <NNN>`", text), (
        f"{rel} still emits a bare <NNN> command"
    )
    assert "execute-issue 001-...`" not in text, (
        f"{rel} still emits the truncated `001-...` placeholder"
    )
```

- [ ] **Step 2: Run the test**

Run: `python -m pytest tests/test_skill_handoffs.py -v`
Expected: PASS — all edits from Tasks 5–9 satisfy the assertions. If any
case fails, fix the corresponding SKILL.md (the literal string must appear
verbatim) and re-run.

- [ ] **Step 3: Commit**

```bash
git add tests/test_skill_handoffs.py
git commit -m "test: lint guard for literal slash-command handoffs"
```

---

## Task 11: install.sh — global collision choice + flags

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Replace the flag-parsing block**

Replace lines 8–17 (the `DRY_RUN/FORCE` block and `while` loop):

```bash
DRY_RUN=0
FORCE=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --force) FORCE=1 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
    shift
done
```

with:

```bash
DRY_RUN=0
# MODE is empty until the user/flags choose: overwrite | skip | archive | ""
MODE=""
set_mode() {
    if [[ -n "$MODE" && "$MODE" != "$1" ]]; then
        echo "conflicting collision flags: --$MODE and --$1" >&2; exit 2
    fi
    MODE="$1"
}
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --force|--overwrite) set_mode overwrite ;;
        --skip) set_mode skip ;;
        --archive) set_mode archive ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
    shift
done
```

- [ ] **Step 2: Add the up-front global prompt helper**

Immediately after the `run()` function definition (after its closing `}` near line 28), add:

```bash
# Decide the collision mode the first time it is needed (interactive only).
ASKED_GLOBAL=0
ensure_mode() {
    [[ -n "$MODE" ]] && return
    [[ $ASKED_GLOBAL -eq 1 ]] && return
    ASKED_GLOBAL=1
    echo "Existing skills collide. Apply which action to ALL collisions?"
    read -r -p "  (o)verwrite-all / (s)kip-all / (a)rchive-all / (d)ecide-each: " g
    case "$g" in
        o|O) MODE=overwrite ;;
        s|S) MODE=skip ;;
        a|A) MODE=archive ;;
        *)   MODE="" ;;   # decide-each: fall through to per-skill prompt
    esac
}
```

- [ ] **Step 3: Use FORCE-equivalent logic in the prototype-archive prompt**

Replace (around line 49):

```bash
    if [[ $FORCE -eq 1 ]]; then ans=y; else read -r -p "Archive these before installing the new library? (y/N) " ans; fi
```

with:

```bash
    if [[ -n "$MODE" ]]; then ans=y; else read -r -p "Archive these before installing the new library? (y/N) " ans; fi
```

- [ ] **Step 4: Replace the per-skill collision branch**

Replace the collision `if [[ -d "$dst" ]]` block (lines ~65–85):

```bash
    if [[ -d "$dst" ]]; then
        if [[ $FORCE -eq 1 ]]; then action=o; else
            read -r -p "Skill '$name' already exists. (o)verwrite / (s)kip / (a)rchive-then-overwrite? " action
        fi
        case "$action" in
            o)
                run "rm -rf '$dst'"
                run "cp -r '$leaf' '$dst'"
                overwritten=$((overwritten+1))
                ;;
            a)
                stamp="$(date +%Y%m%d-%H%M%S)"
                run "mkdir -p '$ARCHIVE_ROOT'"
                run "mv '$dst' '$ARCHIVE_ROOT/$name-$stamp'"
                run "cp -r '$leaf' '$dst'"
                overwritten=$((overwritten+1))
                ;;
            *)
                echo "Skipped $name"; skipped=$((skipped+1))
                ;;
        esac
    else
```

with:

```bash
    if [[ -d "$dst" ]]; then
        ensure_mode
        if [[ "$MODE" == overwrite ]]; then action=o
        elif [[ "$MODE" == skip ]]; then action=s
        elif [[ "$MODE" == archive ]]; then action=a
        else
            read -r -p "Skill '$name' already exists. (o)verwrite / (s)kip / (a)rchive-then-overwrite? " action
        fi
        case "$action" in
            o)
                run "rm -rf '$dst'"
                run "cp -r '$leaf' '$dst'"
                overwritten=$((overwritten+1))
                ;;
            a)
                stamp="$(date +%Y%m%d-%H%M%S)"
                run "mkdir -p '$ARCHIVE_ROOT'"
                run "mv '$dst' '$ARCHIVE_ROOT/$name-$stamp'"
                run "cp -r '$leaf' '$dst'"
                overwritten=$((overwritten+1))
                ;;
            *)
                echo "Skipped $name"; skipped=$((skipped+1))
                ;;
        esac
    else
```

- [ ] **Step 5: Verify with a dry run**

Set up a collision and exercise each path:

```bash
mkdir -p ~/.claude/skills/execute-issue
./install.sh --dry-run --skip
./install.sh --dry-run --archive
./install.sh --dry-run --overwrite --skip   # expect: conflicting collision flags, exit 2
echo "exit: $?"
```

Expected: skip run prints `Skipped <name>` lines for collisions; archive run prints `[dry-run] mv ...`; the conflicting-flags run exits 2 with the conflict message. Clean up: `rm -rf ~/.claude/skills/execute-issue` (only if you created it solely for the test).

- [ ] **Step 6: Commit**

```bash
git add install.sh
git commit -m "feat(install.sh): up-front global collision choice + --skip/--archive/--overwrite flags"
```

---

## Task 12: install.ps1 — global collision choice + flags

**Files:**
- Modify: `install.ps1`

- [ ] **Step 1: Replace the param block**

Replace the `param(...)` block (lines ~20–24):

```powershell
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force
)
```

with:

```powershell
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$Overwrite,
    [switch]$Skip,
    [switch]$Archive
)

# Resolve a single collision mode from flags ("" = undecided / decide-each).
$Mode = ''
$flagModes = @()
if ($Force -or $Overwrite) { $flagModes += 'overwrite' }
if ($Skip)                 { $flagModes += 'skip' }
if ($Archive)              { $flagModes += 'archive' }
if ($flagModes.Count -gt 1) {
    throw "Conflicting collision flags: $($flagModes -join ', '). Pick one."
}
if ($flagModes.Count -eq 1) { $Mode = $flagModes[0] }
$script:AskedGlobal = $false
```

- [ ] **Step 2: Add the ensure-mode helper**

After `$ErrorActionPreference = 'Stop'` (line ~26), add:

```powershell
function Get-CollisionMode {
    if ($script:Mode) { return $script:Mode }
    if ($script:AskedGlobal) { return $script:Mode }
    $script:AskedGlobal = $true
    Write-Host "Existing skills collide. Apply which action to ALL collisions?"
    $g = Read-Host "  (o)verwrite-all / (s)kip-all / (a)rchive-all / (d)ecide-each"
    switch ($g) {
        'o' { $script:Mode = 'overwrite' }
        's' { $script:Mode = 'skip' }
        'a' { $script:Mode = 'archive' }
        default { $script:Mode = '' }
    }
    return $script:Mode
}
```

(Note: change `$Mode` to `$script:Mode` at its definition in Step 1 so the
function can mutate it: `$script:Mode = ''` and `if ($flagModes.Count -eq 1)
{ $script:Mode = $flagModes[0] }`.)

- [ ] **Step 3: Update the prototype-archive prompt**

Replace (lines ~57–61):

```powershell
    if (-not $Force) {
        $answer = Read-Host "Archive these (move to .archive/) before installing the new library? (y/N)"
    } else {
        $answer = 'y'
    }
```

with:

```powershell
    if ($script:Mode) {
        $answer = 'y'
    } else {
        $answer = Read-Host "Archive these (move to .archive/) before installing the new library? (y/N)"
    }
```

- [ ] **Step 4: Replace the per-skill collision branch**

Replace the collision block (lines ~86–120, `if (Test-Path $dst) { ... }`)
with one that consults `Get-CollisionMode`:

```powershell
    if (Test-Path $dst) {
        $mode = Get-CollisionMode
        if ($mode -eq 'overwrite') {
            $action = 'o'
        } elseif ($mode -eq 'skip') {
            $action = 's'
        } elseif ($mode -eq 'archive') {
            $action = 'a'
        } else {
            $action = Read-Host "Skill '$name' already exists. (o)verwrite / (s)kip / (a)rchive-then-overwrite?"
        }
        switch ($action) {
            'o' {
                if ($DryRun) { Write-Host "[dry-run] would overwrite $dst" }
                else { Remove-Item -Recurse -Force $dst; Copy-Item -Recurse $leaf.FullName $dst }
                $overwritten++
            }
            'a' {
                $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
                $archDst = Join-Path $archiveRoot "$name-$stamp"
                if (-not (Test-Path $archiveRoot)) {
                    if (-not $DryRun) { New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null }
                }
                if ($DryRun) {
                    Write-Host "[dry-run] would archive existing $dst -> $archDst, then install"
                } else {
                    Move-Item -Path $dst -Destination $archDst
                    Copy-Item -Recurse $leaf.FullName $dst
                }
                $overwritten++
            }
            default {
                Write-Host "Skipped $name"; $skipped++
            }
        }
    } else {
```

(This also collapses the old duplicate `'o'`/`'overwrite'` switch arms into a
single `'o'` arm, since the mode is now normalized before the switch.)

- [ ] **Step 5: Verify with a dry run**

Run in PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills\execute-issue" | Out-Null
.\install.ps1 -DryRun -Skip
.\install.ps1 -DryRun -Archive
.\install.ps1 -DryRun -Overwrite -Skip   # expect: throws "Conflicting collision flags"
```

Expected: `-Skip` prints `Skipped <name>` for collisions; `-Archive` prints `[dry-run] would archive ...`; the conflicting run throws and exits non-zero. Clean up the temp dir if you created it only for the test.

- [ ] **Step 6: Commit**

```bash
git add install.ps1
git commit -m "feat(install.ps1): up-front global collision choice + -Skip/-Archive/-Overwrite flags"
```

---

## Task 13: Docs — README + final full verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document the install flags**

In `README.md`, replace the paragraph:

```
The installer copies each leaf skill folder into `~/.claude/skills/`. Re-running is idempotent (it'll prompt before overwriting). On first run, it offers to archive existing prototype skills (`probe`, `scope`, `grill-me`) to `~/.claude/skills/.archive/`.
```

with:

```
The installer copies each leaf skill folder into `~/.claude/skills/`. Re-running is idempotent. On the first collision it asks once whether to overwrite-all / skip-all / archive-all / decide-each. Non-interactive equivalents: `--overwrite` (alias `--force`), `--skip`, `--archive` (PowerShell: `-Overwrite`/`-Skip`/`-Archive`); these are mutually exclusive and compose with `--dry-run`/`-DryRun`. On first run it also offers to archive existing prototype skills (`probe`, `scope`, `grill-me`) to `~/.claude/skills/.archive/`.
```

- [ ] **Step 2: Document STATUS.md in the Quick start / Skills section**

In `README.md`, in the `Plan` skills description area (find the `slice-issues` bullet), append a sentence to the `slice-issues` line:

```
 Also seeds `docs/features/<slug>/issues/STATUS.md`, a per-feature progress tracker that `execute-issue`/`verify-issue` tick off and that drives the literal "Next — run:" command at every handoff.
```

And in the Quick start fenced block, update the loop lines to show fully-qualified args:

```
> execute-issue <slug>/001-...   # loop per issue (slug-qualified — avoids cross-feature NNN collisions)
> verify-issue  <slug>/001-...   # after each execute
```

- [ ] **Step 3: Run the full test suite**

Run: `python -m pytest -v`
Expected: PASS — all of `test_status_update.py`, `test_skill_handoffs.py`, and the pre-existing `test_estimate_tokens.py` / `test_page_count.py` / `test_roadmap_merge.py` green.

- [ ] **Step 4: Final manual smoke of the tracker lifecycle**

```bash
TMP=$(mktemp -d); mkdir -p "$TMP/docs/features/demo/issues"
printf '# Issue 001-a: x\n\n## Slice type: vertical\n' > "$TMP/docs/features/demo/issues/001-a.md"
printf '# Issue 002-b: y\n\n## Slice type: vertical\n' > "$TMP/docs/features/demo/issues/002-b.md"
python scripts/status_update.py seed --feature-dir "$TMP/docs/features/demo" --name Demo --slug demo
python scripts/status_update.py mark-executed --feature-dir "$TMP/docs/features/demo" --name Demo --slug demo --issue 001-a --date 2026-05-15
python scripts/status_update.py next --feature-dir "$TMP/docs/features/demo" --slug demo --stage execute
cat "$TMP/docs/features/demo/issues/STATUS.md"; rm -rf "$TMP"
```

Expected: `next` prints `/execute-issue demo/002-b`; STATUS.md shows `001-a` executed `2026-05-15`, feature status `in-progress — 1/2 executed, 0/2 verified`.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: document install flags and STATUS.md progress tracker"
```

---

## Self-Review

**Spec coverage:**
- Part A (STATUS.md tracker): Tasks 1–8 (helper, seed, mark, regen self-heal, slice-issues seeds, sequence-issues reads-only, execute/verify mark). ✓
- Part B (slug disambiguation): Tasks 7 & 8 — identical hard-stop resolution rules in execute-issue and verify-issue. ✓
- Part C (literal next-command + slug-as-arg): Tasks 5, 6, 7, 8, 9, guarded by Task 10. Orchestration-unchanged constraint preserved — Task 9 Step 2/4/5 keep "If invoked via probe-feature, slug is passed in" wording. ✓
- Part D (install global choice + flags): Tasks 11 (sh) & 12 (ps1), symmetric, mutual-exclusion validated, dry-run composes. ✓
- Out-of-scope items (global index, auto-close, issue renumbering) — not introduced. ✓

**Placeholder scan:** `<slug>`, `<NNN-name>`, `<feature name>` are intentional *runtime substitution markers inside SKILL.md prose* (the literal text the skill renders with real values), not plan placeholders — every code/Markdown block is concrete. No TBD/TODO. ✓

**Type/string consistency:** STATUS.md table header/sep constants (`| Issue | Slice | Executed | Verified |`) are defined once in `status_update.py` and asserted verbatim in tests. Helper path `~/.claude/skills/slice-issues/status_update.py` is identical across slice-issues/sequence-issues/execute-issue/verify-issue (matches the existing `estimate_tokens.py` convention). Subcommand names (`seed`/`mark-executed`/`mark-verified`/`next`/`regen`) and flags (`--feature-dir`/`--name`/`--slug`/`--issue`/`--date`/`--status`/`--verdict`/`--stage`) are consistent between implementation, tests, and SKILL.md call sites. ✓
