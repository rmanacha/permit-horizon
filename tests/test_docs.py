"""The submission documents' tables are generated (src/hre/docs.py) and must match their sources.

If this fails, a register entry, a current-law file, the ledger or the committed bundle changed
after the docs were written: run `make docs` and commit the result.
"""

import json
from pathlib import Path

import pytest

from hre import docs

REPO = Path(__file__).resolve().parents[1]


def test_generated_tables_match_their_sources():
    docs.clear_caches()
    assert not docs.problems()


@pytest.mark.parametrize("rel, expected", [
    ("docs/MODEL_AND_ASSUMPTIONS.md", {"core-assumptions", "current-law-adu", "current-law-showcase",
                                       "formulas", "validation-ledger", "sensitivity"}),
    ("docs/POLICY_SCENARIO_COMPARISON.md", {"benchmarks", "ranking-UT", "ranking-NH", "ranking-AZ", "flips"}),
])
def test_each_document_carries_its_generated_tables(rel, expected):
    names = docs.block_names((REPO / rel).read_text(encoding="utf-8"))
    assert expected <= set(names), sorted(expected - set(names))
    assert len(names) == len(set(names)), "a block appears twice"


def test_unknown_block_names_fail_loudly():
    with pytest.raises(KeyError):
        docs.render_text("<!-- BEGIN generated:nonsense -->\n<!-- END generated:nonsense -->")


def test_core_table_has_every_register_entry():
    from hre.assumptions.loader import load_entries

    rows = [r for r in docs.core_assumptions().splitlines() if r.startswith("| **")]
    assert len(rows) == len(load_entries())


def test_top_two_breaks_ties_in_reform_order():
    assert docs.top_two({"adu": 5, "missing_middle": 5, "tod": 1, "parking": 0, "fees": 9}) == ("fees", "adu")


def test_flip_table_marks_unchanged_states_same():
    text = docs.flips()
    rows = [r for r in text.splitlines() if r.startswith("| ") and not r.startswith("| What")]
    assert rows[0].startswith("| Nothing: the middle assumptions")
    assert all(r.count("|") == len(docs.SHOWCASE) + 2 for r in rows)
    singles = [r for r in rows if not r.startswith(("| Nothing", "| Every range"))]
    assert singles, "at least one assumption reorders the top two somewhere"
    assert all(any(c.strip() != "same" for c in r.split("|")[2:-1]) for r in singles)


def test_rankings_compare_permits_only_and_follow_the_middle():
    for st in docs.SHOWCASE:
        r = json.loads((docs.BUNDLE / f"{st}.json").read_text(encoding="utf-8"))
        mids = [r["scenarios"][sc]["increment"]["estimate"]["mid"] for sc in docs.REFORMS]
        assert all(r["scenarios"][sc]["increment"]["outcome"] == "permits" for sc in docs.REFORMS)
        table = [row for row in docs.ranking(st).splitlines() if row[:3] in {f"| {k}" for k in range(1, 6)}]
        assert len(table) == 5
        shown = [float(row.split("|")[3].split("(")[0].replace(",", "")) for row in table]
        assert shown == sorted(shown, reverse=True)
        assert sorted(round(m) for m in mids) == sorted(shown)


def test_adu_table_covers_all_51_jurisdictions():
    text = docs.current_law_adu()
    rows = [r for r in text.splitlines() if r.startswith("| ") and not r.startswith("| State")
            and not r.startswith("|---")]
    listed_none = text.rsplit("(strength 0, the whole benchmark counts as new): ", 1)[1].rstrip(".").split(", ")
    assert len(rows) + len(listed_none) == 51


def test_site_text_has_no_internal_references():
    """Glossary, limits and fixed site text reach legislators verbatim: no decision numbers or phase names."""
    import re

    bad = re.compile(r"\bdecisions? \d|\bPhase \d", re.IGNORECASE)
    lines = [ln for rel in ("docs/GLOSSARY.md", "docs/methods/limits.md")
             for ln in (REPO / rel).read_text(encoding="utf-8").splitlines() if ln.startswith("- **")]
    site = (REPO / "web/src/content/site.ts").read_text(encoding="utf-8")
    lines += [m.group(0) for m in re.finditer(r"'[^']{20,}'|\"[^\"]{20,}\"", site)]
    hits = [ln for ln in lines if bad.search(ln)]
    assert not hits, hits
