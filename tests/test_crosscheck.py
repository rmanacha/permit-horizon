"""PEP cross-check panel (decision 56): net change since April 2020, county and state."""

import copy

from hre.model.crosscheck import pep_cross_check
from hre.model.run import run_state, validate_results

META = {"build_id": "x", "vintages": {}, "git_sha": "x", "run_date": "2026-11-03"}


def test_zz_by_hand(zz_state):
    x = pep_cross_check(zz_state)
    # fixture: 99001 20,000 -> 21,000; 99003 10,000 -> 10,500 (April 2020 base -> July 2025)
    by = {c["fips"]: c for c in x["county"]}
    assert by["99001"]["net_change"] == 1000 and by["99003"]["net_change"] == 500
    assert x["state"] == {"april_2020": 30000, "end": 31500, "net_change": 1500, "change_share": 0.05}
    assert x["end_year"] == 2025 and x["outcome"] == "stock_change" and x["can_add_to_baseline"] is False
    assert "built partly from building permits" in x["caveat"]


def test_county_without_base_is_noted(zz_state):
    s = copy.deepcopy(zz_state)
    del s.counties[0].housing_units_pep["2020-04"]
    x = pep_cross_check(s)
    assert len(x["county"]) == len(s.counties) - 1 and "no April 2020 base" in x["notes"][0]


def test_results_file_carries_it_and_validator_requires_it(zz_state, params):
    r = run_state(zz_state, params, ["baseline"], META, {}, state_name="Zetaland")
    xc = r["cross_check"]["housing_units_pep"]
    assert validate_results(r) == [] and xc["narrative"][0].startswith("Census housing-unit estimates put Zetaland")
    xc["can_add_to_baseline"] = True
    assert any("never added to the baseline" in p for p in validate_results(r))
    del r["cross_check"]
    assert any("cross_check" in p for p in validate_results(r))
