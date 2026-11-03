"""The assumption register: every entry complete, every id used in code present."""

import re
from pathlib import Path

import pytest

from hre.assumptions.loader import check_entry, load_entries, load_params, register_markdown

SRC = Path(__file__).resolve().parents[1] / "src" / "hre"
KEY = re.compile(r"""params(?:\[\s*|\.(?:level_value|entry|display|level_of)\(\s*)["']([a-z0-9_]+)["']""")


def _used_ids() -> set[str]:
    used: set[str] = set()
    for py in SRC.rglob("*.py"):
        used |= set(KEY.findall(py.read_text(encoding="utf-8")))
    return used


def test_every_id_used_in_code_is_in_the_register():
    missing = _used_ids() - set(load_entries())
    assert not missing, f"used in code but not in parameters.yaml: {sorted(missing)}"


def test_code_uses_the_register_at_all():
    assert {"horizon_years", "baseline_window_years", "baseline_band_ratio"} <= _used_ids()


def test_every_entry_has_locator_url_grade_confidence():
    for pid, e in load_entries().items():
        assert check_entry(e) == [], pid
        assert e["sources"] and all(s["locator"] and s["url"].startswith("https://") for s in e["sources"])
        assert e["grade"] in "ABCR" and e["confidence"]


def test_ported_entries_are_marked():
    ported = {pid for pid, e in load_entries().items() if e.get("ported_from") == "adam-v2.0"}
    assert {"builder_response_override", "new_home_price_ratio", "horizon_years"} <= ported


def test_loader_levels_and_overrides():
    p = load_params()
    assert p["builder_response_override"] == 0.75
    assert p.at({"builder_response_override": "low"})["builder_response_override"] == 0.0
    assert p.all_at("high")["fee_pass_through"] == 1.66
    q = load_params(overrides={"builder_response_override": 1.1})
    assert q["builder_response_override"] == 1.1 and q.level_of("builder_response_override") == "user"
    with pytest.raises(KeyError):
        p["not_a_parameter"]


def test_check_entry_catches_problems():
    bad = {"id": "x", "label": "x", "description": "x", "unit": "x", "low": 2, "mid": 1, "high": 3,
           "scope": "global", "scenarios": ["adu"], "grade": "D", "confidence": "high",
           "sources": [{"title": "t", "url": "http://x", "locator": "", "accessed": "2026"}],
           "citation": "PLACEHOLDER", "rationale": "r", "transferability": "t",
           "levels": {"low": "a", "mid": "b", "high": "c"}}
    problems = " ".join(check_entry(bad))
    for word in ("grade", "locator", "https", "placeholder", "between"):
        assert word in problems


def test_register_markdown_has_a_row_per_entry():
    md = register_markdown()
    assert md.count("\n| **") == len(load_entries())
    assert "0.3 x 0.5 / 0.0529 = 2.84" in md
