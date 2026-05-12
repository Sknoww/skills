import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "career" / "align-resume" / "page_count.py"


def run_script(args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True
    )
    return result.stdout, result.stderr, result.returncode


def make_pdf(path, pages):
    from pypdf import PdfWriter
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    with open(path, "wb") as f:
        writer.write(f)


def test_one_page_pdf(tmp_path):
    pdf = tmp_path / "one.pdf"
    make_pdf(pdf, 1)
    out, err, code = run_script([str(pdf)])
    assert code == 0, err
    assert out.strip() == "1"


def test_three_page_pdf(tmp_path):
    pdf = tmp_path / "three.pdf"
    make_pdf(pdf, 3)
    out, err, code = run_script([str(pdf)])
    assert code == 0, err
    assert out.strip() == "3"


def test_missing_file_errors(tmp_path):
    out, err, code = run_script([str(tmp_path / "nope.pdf")])
    assert code != 0
    assert "nope.pdf" in (out + err)


def test_no_args_prints_usage():
    out, err, code = run_script([])
    assert code != 0
    assert "usage" in (out + err).lower()
