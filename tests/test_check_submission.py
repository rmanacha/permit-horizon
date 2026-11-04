"""The submission checklist script (scripts/check_submission.py): its rules on small inputs."""

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_submission", REPO / "scripts" / "check_submission.py")
cs = importlib.util.module_from_spec(spec)
sys.modules["check_submission"] = cs
spec.loader.exec_module(cs)

BLOCK = """
- Code scanning open alerts: {a}
- Dependabot open alerts: {b}
- Secret scanning open alerts: {c}
- Push protection: {d}
- Checked by and date: {e}
"""


def judge(a="0", b="0", c="0", d="on", e="R. M., 2026-12-01"):
    return cs.judge_security(cs.security_block(BLOCK.format(a=a, b=b, c=c, d=d, e=e)))[0]


def test_security_block_blank_is_pending_and_zeros_pass():
    assert judge(a="", e="") == "PENDING"
    assert judge() == "PASS"


def test_security_block_open_alerts_fail_unless_justified():
    assert judge(b="2") == "FAIL"
    assert judge(b="2 (both low severity, justified in the report)") == "PASS"
    assert judge(d="off") == "FAIL"
    assert judge(a="none") == "FAIL"


def test_the_committed_security_block_never_fails_the_checklist():
    text = (REPO / "docs" / "evidence" / "security_gates.md").read_text(encoding="utf-8")
    status, detail = cs.judge_security(cs.security_block(text))
    assert status in ("PASS", "PENDING"), detail


def test_template_prompts_are_caught():
    assert cs.TEMPLATE_PROMPT.search("[List the scenarios you modeled.]")
    assert cs.TEMPLATE_PROMPT.search("| [name] | [value] | [why] | [citation] |")
    assert not cs.TEMPLATE_PROMPT.search("see [what the tool cannot tell you](docs/methods/limits.md)")


def test_secret_file_names():
    for bad in (".env", "config/.env.local", "deploy/key.pem", "id_rsa", "credentials.json"):
        assert cs.SECRET_NAMES.search(bad), bad
    for ok in (".env.example", "docs/evidence/security_gates.md", "src/hre/data/net.py"):
        assert not cs.SECRET_NAMES.search(ok), ok


def test_unlabeled_ranges_inherit_the_enclosing_label():
    labeled = {"outcome": "permits", "parts": {"low": 1, "mid": 2, "high": 3}}
    bare = {"parts": {"low": 1, "mid": 2, "high": 3}, "ramp": [0.1, 0.2]}
    assert cs.unlabeled_ranges(labeled) == 0
    assert cs.unlabeled_ranges(bare) == 1
