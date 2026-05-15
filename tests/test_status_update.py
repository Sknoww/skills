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
