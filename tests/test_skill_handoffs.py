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
