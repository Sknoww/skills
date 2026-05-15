import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "roadmap_merge.py"


def run_script(args, stdin_text=None):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, input=stdin_text
    )
    return result.stdout, result.stderr, result.returncode


def test_no_args_shows_usage():
    out, err, code = run_script([])
    assert code != 0
    combined = (out + err).lower()
    assert "usage" in combined or "subcommand" in combined


def test_help_lists_three_subcommands():
    out, err, code = run_script(["--help"])
    combined = out + err
    assert "parse" in combined
    assert "merge" in combined
    assert "render" in combined


def test_unknown_subcommand_errors():
    out, err, code = run_script(["bogus"])
    assert code != 0
