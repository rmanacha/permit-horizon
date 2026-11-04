"""Current-law register: schema, NH ADU worked example, and the documented default."""

import shutil
from pathlib import Path

import pytest
import yaml

from hre.current_law import coverage as cov
from hre.current_law.loader import HERE, current_strength, register_digest
from hre.current_law.schema import (
    DEFAULT_NOTE,
    GATES,
    INTERNAL,
    SCENARIOS,
    coverage_value,
    horizon_share,
    rule_problems,
    shown_text,
    strength_by_rule,
    strength_from_features,
    validate_state,
)


def test_template_and_nh_files_follow_the_schema():
    nh = yaml.safe_load((HERE / "NH.yaml").read_text())
    assert validate_state(nh) == []
    tpl = yaml.safe_load((HERE / "_template.yaml").read_text())
    assert validate_state(tpl) == []


def test_nh_adu_worked_example():
    r = current_strength("NH", "adu")
    assert r["source"] == "register" and r["current_strength"] == 0.75
    assert r["newly_affected_share"] == 0.25
    assert r["human_review"]["status"] == "pending"
    assert strength_from_features(r["features"]) == 0.75
    assert "674-72" in r["record"]["url"]
    assert register_digest("NH") is not None


def test_missing_file_or_scenario_gives_the_default():
    r = current_strength("WY", "adu")
    assert (r["current_strength"], r["newly_affected_share"], r["note"]) == (0.0, 1.0, DEFAULT_NOTE)
    r = current_strength("NH", "fees")          # NH file exists, fees not assessed
    assert r["current_strength"] == 0.0 and r["file"] == "NH.yaml"


def test_incomplete_entry_falls_back_loudly(tmp_path):
    shutil.copy(HERE / "NH.yaml", tmp_path / "NH.yaml")
    doc = yaml.safe_load((tmp_path / "NH.yaml").read_text())
    del doc["scenarios"]["adu"]["features"][0]["sources"]
    doc["scenarios"]["adu"]["current_strength"] = 1.5
    (tmp_path / "NH.yaml").write_text(yaml.safe_dump(doc))
    r = current_strength("NH", "adu", tmp_path)
    assert r["current_strength"] == 0.0 and r["problems"]
    assert "incomplete" in r["note"]


# --- Phase 5: the strength rule, coverage, plain text (docs/methods/current_law.md) ---------

STATE_FILES = sorted(p for p in HERE.glob("[A-Z][A-Z].yaml"))


def _feat(fid: str, status: str, **kw) -> dict:
    return {"id": fid, "status": status, **kw}


@pytest.mark.parametrize("path", STATE_FILES, ids=lambda p: p.stem)
def test_every_state_file_follows_the_schema_and_the_rule(path):
    doc = yaml.safe_load(path.read_text())
    assert doc["state"] == path.stem
    assert validate_state(doc) == []
    for name, s in doc["scenarios"].items():
        assert rule_problems(name, s) == []
        if s.get("strength_method") == "quantified":
            assert s["strength_arithmetic"]
        for f in s["features"]:
            assert f["sources"], f"{path.stem} {name} {f['id']}: every feature cites a source"
        if s.get("ported_from"):
            assert s["ported_from"] == "adam-v2.0" and s.get("rechecked"), "ported entries carry a re-check date"


@pytest.mark.parametrize("path", STATE_FILES, ids=lambda p: p.stem)
def test_text_shown_to_legislators_has_no_internal_references(path):
    doc = yaml.safe_load(path.read_text())
    for name, s in doc["scenarios"].items():
        for text in shown_text(s):
            m = INTERNAL.search(text)
            assert m is None, f"{path.stem} {name}: {m.group(0)!r} in {text[:80]!r}"


def test_horizon_share_counts_the_years_in_force():
    assert horizon_share(None) == 1.0
    assert horizon_share("2017-06-01") == 1.0
    assert horizon_share("2031-01-01") == 0.0
    assert horizon_share("2027-01-01") == pytest.approx(1461 / 1826)     # four of five years
    assert horizon_share("2028-07-01") == pytest.approx(914 / 1826)


def test_gate_rule_scores_an_enabling_law_zero():
    # A statute that lets towns allow ADUs but requires none: the core feature differs.
    feats = [_feat("adu_per_lot", "differs"), _feat("adu_forms", "supported_with_limits"),
             _feat("adu_size", "supported_with_limits"), _feat("adu_parking", "supported_with_limits")]
    assert strength_by_rule("adu", feats) == 0.0
    feats[0]["status"] = "supported_with_limits"
    assert strength_by_rule("adu", feats) == 1.0
    assert strength_by_rule("adu", feats, coverage=0.8) == pytest.approx(0.8)
    feats[1]["in_effect_from"] = "2028-01-01"                            # one feature from 2028
    assert strength_by_rule("adu", feats) == pytest.approx((3 + 1096 / 1826) / 4)
    assert set(GATES) == set(SCENARIOS)


def test_showcase_states_file_all_five_reforms():
    for st in ("AZ", "UT", "NH"):
        doc = yaml.safe_load((HERE / f"{st}.yaml").read_text())
        assert set(doc["scenarios"]) == set(SCENARIOS)
        for name in SCENARIOS:
            assert current_strength(st, name)["source"] == "register"
    az = current_strength("AZ", "adu")
    assert az["current_strength"] == 0.80 and "75,000" in az["note"]
    assert current_strength("UT", "adu")["current_strength"] == 0.50
    nh = yaml.safe_load((HERE / "NH.yaml").read_text())["scenarios"]["parking"]
    assert nh["strength_method"] == "quantified" and nh["current_strength"] == 0.43
    assert coverage_value(yaml.safe_load((HERE / "AZ.yaml").read_text())["scenarios"]["adu"]) == 0.7989


def _write_acs(tmp_path):
    """State 99: county 001 holds a big city and a small town, county 003 a CDP; a reservation;
    two towns (county subdivisions) in county 003."""
    acs = tmp_path / "acs"
    acs.mkdir()
    rows = {   # GEO_ID: (total, detached)
        "0400000US99": (1000, 600),
        "0500000US99001": (700, 400), "0500000US99003": (300, 200),
        "1600000US9910000": (500, 300), "1600000US9920000": (100, 60), "1600000US9930000": (80, 50),
        "1550000US9910000001": (500, 300), "1550000US9920000001": (100, 60), "1550000US9930000003": (80, 50),
        "2600000US123499": (40, 30),
        "0600000US9900311111": (150, 120), "0600000US9900322222": (150, 80),
    }
    head = "GEO_ID|B25024_E001|B25024_M001|B25024_E002|B25024_M002"
    (acs / "acsdt5y2024-b25024.dat").write_text(
        head + "\n" + "\n".join(f"{g}|{t}|1|{d}|1" for g, (t, d) in rows.items()) + "\n")
    pop = {"1600000US9910000": 90000, "1600000US9920000": 4000, "1600000US9930000": 3000,
           "0500000US99001": 120000, "0500000US99003": 9000}
    (acs / "acsdt5y2024-b01003.dat").write_text(
        "GEO_ID|B01003_E001|B01003_M001\n" + "\n".join(f"{g}|{p}|1" for g, p in pop.items()) + "\n")
    names = {"1600000US9910000": "Big city, Test", "1600000US9920000": "Small town, Test",
             "1600000US9930000": "Edge CDP, Test",
             "0600000US9900311111": "Andover town, East County, Test",
             "0600000US9900322222": "Bolton town, East County, Test"}
    (acs / "Geos20245YR.txt").write_text(
        "FILEID|STUSAB|SUMLEVEL|GEO_ID|NAME\n" + "\n".join(f"x|ts|0|{g}|{n}" for g, n in names.items()) + "\n")
    return tmp_path


def test_coverage_arithmetic_on_a_fixture(tmp_path):
    dd = _write_acs(tmp_path)
    r = cov.coverage_share("99", {"above_population": 75000, "unincorporated": "all", "exclude_tribal": True}, dd)
    # covered: Big city 300 + outside incorporated (40 in 001 + 200 in 003; the CDP counts as outside) - tribal 30
    assert r["covered_place_homes"] == 300 and r["homes_outside_incorporated"] == 240
    assert r["tribal_homes_excluded"] == 30 and r["covered_outside_homes"] == 210
    assert r["share"] == pytest.approx(510 / 600, abs=1e-4)
    assert [p["name"] for p in r["largest_uncovered"]] == ["Small town"]
    r = cov.coverage_share("99", {"places": "all", "unincorporated": "none"}, dd)
    assert r["share"] == pytest.approx(360 / 600, abs=1e-4)
    # one county only; unincorporated urban areas only (the CDP, 50 homes, is in county 003)
    r = cov.coverage_share("99", {"counties": ["003"], "unincorporated": "cdp", "cdp_min_population": 1000}, dd)
    assert r["covered_place_homes"] == 0 and r["covered_outside_homes"] == 50
    # unincorporated land only in counties of 15,000 or more people (county 003 has 9,000)
    r = cov.coverage_share("99", {"unincorporated": "all", "county_min_population": 15000}, dd)
    assert r["covered_outside_homes"] == 40 and r["share"] == pytest.approx(400 / 600, abs=1e-4)
    # every town except one that opted out
    r = cov.coverage_share("99", {"unincorporated": "all", "exclude_subdivisions": ["Andover"]}, dd)
    assert r["share"] == pytest.approx((600 - 120) / 600, abs=1e-4)
    with pytest.raises(ValueError):
        cov.coverage_share("99", {"unincorporated": "all", "exclude_subdivisions": ["Nowhere"]}, dd)


def test_stored_coverage_shares_reproduce_from_the_cache():
    from hre.data.fetch_acs import table_path

    raw = Path(__file__).resolve().parents[1] / "data" / "raw"      # the real cache, not the test's
    if not (table_path("b01003", raw).exists() and cov.place_gazetteer_path(raw).exists()):
        pytest.skip("ACS B01003 or the place Gazetteer not cached (hre validate --law-coverage --fetch)")
    rows = cov.check_files(HERE, raw)
    assert rows and all(r["ok"] for r in rows), [(r["state"], r["scenario"], r["computed"]) for r in rows if not r["ok"]]
