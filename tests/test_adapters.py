"""Parcel adapters: the tolerance rule, a dummy adapter's round trip, the rules files (offline)."""

import json

import pytest
import yaml

from hre.adapters import registry
from hre.adapters.base import RULES_DIR, TOLERANCE, Adapter, apply_tolerance, write_summary
from hre.schema import CountyInputs, StateInputs, validate


def _state() -> StateInputs:
    counties = [CountyInputs(fips="49035", name="Salt Lake County", sf_detached=268749),
                CountyInputs(fips="49043", name="Summit County", sf_detached=16654),
                CountyInputs(fips="49001", name="Beaver County", sf_detached=2704)]
    return StateInputs(state="UT", state_fips="49", counties=counties)


def test_tolerance_keeps_acs_outside_thirty_percent():
    used, excluded = apply_tolerance({"a": 100, "b": 100, "c": 100, "d": None},
                                     {"a": 130, "b": 131, "c": 70, "d": 5})
    assert used == {"a", "c"} and TOLERANCE == 0.30
    assert [(e["fips"], e["ratio"]) for e in excluded] == [("b", 1.31), ("d", None)]


def test_dummy_adapter_round_trip(tmp_path):
    rules = {"state": "UT", "enabled": True, "tolerance": 0.3, "sources": [
        {"dataset": "Test inventory", "area": "two counties", "rule": "single-family features",
         "license_text": "CC BY 4.0", "documentation_url": "https://example.gov/doc", "accessed": "2026-11-03"}]}
    (tmp_path / "ut.yaml").write_text(yaml.safe_dump(rules))
    a = Adapter.from_rules("UT", tmp_path)
    write_summary(a.summary_path(tmp_path), {"Salt Lake": 240491, "Summit": 568}, "test query", "Test inventory")
    si = a.enrich(_state(), tmp_path)
    by = {c.fips: c for c in si.counties}
    assert by["49035"].sf_detached == 240491 and by["49035"].parcel_sf_count == 240491
    assert by["49043"].sf_detached == 16654 and by["49043"].parcel_sf_count == 568      # outside tolerance
    assert by["49001"].sf_detached == 2704 and by["49001"].parcel_sf_count is None       # not covered
    assert si.adapter["used_counties"] == ["49035"]
    assert si.adapter["excluded_counties"][0]["fips"] == "49043"
    assert si.adapter["raw_values"]["49035"] == {"acs_sf_detached": 268749, "parcel_sf_count": 240491, "ratio": 0.8949}
    d = json.loads(si.to_json())
    assert StateInputs.from_dict(d).adapter == si.adapter                                 # survives the file
    assert not [p for p in validate(d) if "adapter" in p]


def test_unknown_county_in_a_summary_fails_loudly(tmp_path):
    (tmp_path / "ut.yaml").write_text(yaml.safe_dump({"state": "UT", "enabled": True, "sources": []}))
    a = Adapter.from_rules("UT", tmp_path)
    write_summary(a.summary_path(tmp_path), {"Atlantis": 5}, "q", "s")
    with pytest.raises(ValueError, match="Atlantis"):
        a.enrich(_state(), tmp_path)


def test_rules_files_declare_sources_and_request_counts_only():
    assert registry.states() == ["AZ", "NH", "UT"]
    for st in registry.states():
        r = yaml.safe_load((RULES_DIR / f"{st.lower()}.yaml").read_text())
        assert r["state"] == st and r["ported_from"] == "adam-v2.0" and r["rechecked"]
        for s in r["sources"]:
            assert all(s.get(k) for k in ("dataset", "area", "rule", "license_text", "documentation_url", "accessed"))
        text = json.dumps(r).lower()
        for pii in ("owner", "mail_", "pstl", "name ="):
            assert pii not in text, f"{st} rules mention {pii}"
    nh = registry.get("NH")
    assert nh is not None and not nh.enabled and "GRANIT" in nh.rules["disabled_reason"]
    assert registry.fetch("NH", RULES_DIR) is None          # disabled: nothing is fetched


def test_utah_rules_on_a_cached_sample(tmp_path):
    a = registry.get("UT")
    sample = {"Salt Lake": 240491, "Summit": 568}
    write_summary(a.summary_path(tmp_path), sample, "cached sample", a.sources[0].dataset)
    si = a.enrich(_state(), tmp_path)
    assert si.adapter["used_counties"] == ["49035"] and si.adapter["tolerance"] == 0.30
    assert "Creative Commons Attribution 4.0" in si.adapter["sources"][0]["license_text"]
