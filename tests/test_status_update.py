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
