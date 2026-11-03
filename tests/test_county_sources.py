"""Gazetteer, OMB delineation, PEP and BPS parsers on the ZZ fixtures and small inline cases."""

import pytest

from hre.data import fetch_bps, fetch_cbsa, fetch_gazetteer, fetch_pep
from hre.data.states import ALL_STATES, lookup


def test_state_lookup():
    assert lookup("nh").fips == "33" and lookup("33").usps == "NH"
    assert lookup("NH").name_nospace == "NewHampshire" and lookup("DC").name_nospace == "DistrictofColumbia"
    assert lookup("ZZ").synthetic and len(ALL_STATES) == 51 and "PR" not in ALL_STATES


def test_gazetteer_counties(sample_dir):
    rows = fetch_gazetteer.load_counties("99", sample_dir)
    assert [r["fips"] for r in rows] == ["99001", "99003"]
    assert rows[0]["name"] == "Alder County" and rows[0]["land_sqmi"] == 500.0
    assert fetch_gazetteer.normalize_name("Doña Ana County") == "dona ana county"


def test_cbsa_roles(sample_dir):
    table = fetch_cbsa.load_cbsa(sample_dir)
    assert table["99001"] == {"cbsa": "99900", "cbsa_title": "Alderton, ZZ", "cbsa_type": "metropolitan",
                              "metro_role": "central"}
    assert table["33001"]["cbsa_type"] == "micropolitan" and table["33001"]["metro_role"] == "none"
    assert "99003" not in table


def test_pep_joins_by_name(sample_dir):
    counties = fetch_gazetteer.load_counties("99", sample_dir)
    pep = fetch_pep.load_pep("Zetaland", counties, sample_dir)
    assert pep["99001"]["2025"] == 21000 and pep["99003"]["2020"] == 10000
    assert sorted(pep["99001"]) == [str(y) for y in range(2020, 2026)]  # the April 1 base is not a year key


def test_bps_county_total_matches_state_file(sample_dir):
    permits, notes = fetch_bps.load_county_permits("99", sample_dir)
    state = fetch_bps.load_state_permits("99", sample_dir, years=(2024, 2025))
    for year in ("2024", "2025"):
        county_sum = {k: sum(permits[f][year][k] for f in permits) for k in ("u1", "u2", "u34", "u5")}
        assert county_sum == state[year]
    assert "2017" not in permits["99003"] and "2017" in permits["99001"]
    assert permits["99001"]["2025"] == {"u1": 190, "u2": 10, "u34": 6, "u5": 80}
    assert notes == {}


def test_bps_fips_are_strings_with_leading_zeros(sample_dir):
    rows = fetch_bps.parse_county_file(sample_dir / "bps" / "co2025a.txt")
    assert {r["fips"] for r in rows} == {"33001", "99001", "99003"}
    assert rows[0]["name"] == "Belknap County"  # padding stripped


def test_five_plus_share():
    permits = {str(y): {"u1": 100, "u2": 0, "u34": 0, "u5": 100 if y >= 2021 else 0} for y in range(2016, 2026)}
    assert fetch_bps.five_plus_share(permits) == 0.5          # last five years: 2021-2025
    assert fetch_bps.five_plus_share(permits, last_n=10) == pytest.approx(500 / 1500)
    assert fetch_bps.five_plus_share({"2025": {"u1": 0, "u2": 0, "u34": 0, "u5": 0}}) is None


def test_connecticut_reallocation_preserves_totals():
    regions = {f"09{c}": {} for c in ("110", "120")}
    legacy = {"09001": {}, "09003": {}}
    for y in ("2023", "2024", "2025"):
        regions["09110"][y] = {"u1": 300, "u2": 0, "u34": 0, "u5": 100}
        regions["09120"][y] = {"u1": 100, "u2": 0, "u34": 0, "u5": 300}
    legacy["09001"]["2022"] = {"u1": 101, "u2": 0, "u34": 0, "u5": 50}
    legacy["09003"]["2022"] = {"u1": 100, "u2": 0, "u34": 0, "u5": 50}
    out, notes = fetch_bps.allocate_ct_legacy({**regions, **legacy})
    assert set(out) == {"09110", "09120"}
    # 2022 statewide u1 = 201 split 3:1 -> 151 + 50; u5 = 100 split 1:3 -> 25 + 75.
    assert out["09110"]["2022"] == {"u1": 151, "u2": 0, "u34": 0, "u5": 25}
    assert out["09120"]["2022"] == {"u1": 50, "u2": 0, "u34": 0, "u5": 75}
    assert "planning region" in notes["09110"][0]
