import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "estimate_tokens.py"


def run_estimator(args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True
    )
    return result.stdout, result.stderr, result.returncode


def test_empty_file_zero_tokens(tmp_path):
    f = tmp_path / "empty.py"
    f.write_text("")
    out, _, code = run_estimator([str(f)])
    assert code == 0
    assert "\t0\n" in out or out.strip().endswith("\t0")
    assert "TOTAL\t0" in out


def test_code_file_uses_3_5_divisor(tmp_path):
    # 350 chars / 3.5 = 100 tokens
    f = tmp_path / "code.ts"
    f.write_text("x" * 350)
    out, _, code = run_estimator([str(f)])
    assert code == 0
    assert "\t100" in out
    assert "TOTAL\t100" in out


def test_markdown_uses_4_divisor(tmp_path):
    # 400 chars / 4.0 = 100 tokens
    f = tmp_path / "doc.md"
    f.write_text("x" * 400)
    out, _, code = run_estimator([str(f)])
    assert code == 0
    assert "\t100" in out
    assert "TOTAL\t100" in out


def test_multiple_files_with_total(tmp_path):
    f1 = tmp_path / "a.ts"
    f1.write_text("x" * 350)  # 100
    f2 = tmp_path / "b.md"
    f2.write_text("x" * 400)  # 100
    out, _, code = run_estimator([str(f1), str(f2)])
    assert code == 0
    assert "TOTAL\t200" in out


def test_unknown_extension_uses_prose_divisor(tmp_path):
    # Files without a known code extension treat as prose (divisor 4.0)
    f = tmp_path / "data.txt"
    f.write_text("x" * 400)
    out, _, code = run_estimator([str(f)])
    assert code == 0
    assert "\t100" in out


def test_nonexistent_file_errors(tmp_path):
    out, err, code = run_estimator([str(tmp_path / "nope.py")])
    assert code != 0
    assert "nope.py" in err or "nope.py" in out
