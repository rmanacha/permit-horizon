"""Schema: a StateInputs built from a dict round-trips through JSON, and bad input is refused."""

import json

import pytest

from hre.schema import BlockGroupInputs, CountyInputs, StateInputs, validate


def _county(fips="33001", **over):
    base = {
        "fips": fips,
        "name": "Belknap County",
        "cbsa": "29060",
        "cbsa_title": "Laconia, NH",
        "cbsa_type": "micropolitan",
        "metro_role": "none",
        "permits": {
            "2024": {"u1": 300, "u2": 20, "u34": 9, "u5": 40},
            "2025": {"u1": 332, "u2": 42, "u34": 11, "u5": 38},
        },
        "permits_5plus_share_5yr": 0.1,
        "housing_units_pep": {"2025": 39998},
        "address_units": {"2022-06": 38000, "2026-07": 39900},
        "housing_units": 39000,
        "sf_detached": 30000,
        "sf_attached": 1000,
        "units_2_4": 3000,
        "units_5plus": 3000,
        "mobile": 2000,
        "owner_occupied": 22000,
        "renter_occupied": 7000,
        "vacant": 10000,
        "median_value": 350000,
        "median_rent": 1300,
        "hpi": {"2024": 410.5, "2025": 425.1},
        "land_sqmi": 401.912,
        "notes": [],
    }
    base.update(over)
    return base


def _bg(geoid="330019651001", county="33001", **over):
    base = {
        "geoid": geoid,
        "county_fips": county,
        "pop_center_lat": 43.52,
        "pop_center_lon": -71.42,
        "population": 1200,
        "housing_units": 600,
        "sf_detached": 400,
        "units_5plus": 50,
        "land_sqmi": None,
        "dist_major_stop_miles": 12.3,
        "near_transit_half_mile": False,
        "near_transit_quarter_mile": False,
    }
    base.update(over)
    return base


def _state():
    return {
        "state": "NH",
        "state_fips": "33",
        "vintages": {"bps": "2025", "acs": "2020-2024"},
        "counties": [_county()],
        "block_groups": [_bg()],
        "zoning_by_cbsa": {},
        "notes": [],
    }


def test_round_trip_through_json():
    si = StateInputs.from_dict(_state())
    text = si.to_json()
    again = StateInputs.from_json(text)
    assert again == si
    assert json.loads(text)["counties"][0]["fips"] == "33001"
    # Compact and sorted: no spaces after separators, keys in order.
    assert ": " not in text and text.index('"block_groups"') < text.index('"counties"')


def test_dataclasses_default_cleanly():
    c = CountyInputs(fips="33001", name="Belknap County")
    assert c.metro_role == "none" and c.permits == {} and c.supply_elasticity is None
    b = BlockGroupInputs(
        geoid="330019651001",
        county_fips="33001",
        pop_center_lat=0.0,
        pop_center_lon=0.0,
        population=0,
    )
    assert b.dist_major_stop_miles is None


@pytest.mark.parametrize(
    "mutate, fragment",
    [
        (lambda d: d.update(state_fips="3"), "state_fips"),
        (lambda d: d["counties"][0].update(fips=33001), "5-digit string"),
        (lambda d: d["counties"][0].update(fips="25001"), "does not start with state_fips"),
        (lambda d: d["counties"][0].update(metro_role="suburb"), "metro_role"),
        (lambda d: d["counties"][0]["permits"].update({"2025": {"u1": 1}}), "must have keys"),
        (lambda d: d["counties"][0]["permits"]["2025"].update(u1=-1), "non-negative"),
        (lambda d: d["counties"][0].update(median_value="350000"), "median_value"),
        (lambda d: d["block_groups"][0].update(geoid="33001965100"), "12-digit"),
        (
            lambda d: d["block_groups"][0].update(geoid="330039651001", county_fips="33003"),
            "not in counties",
        ),
        (lambda d: d["block_groups"][0].update(near_transit_quarter_mile=True), "quarter"),
        (lambda d: d["block_groups"][0].update(pop_center_lat=95.0), "out of range"),
        (lambda d: d["counties"].append(_county()), "duplicate fips"),
    ],
)
def test_validation_catches(mutate, fragment):
    d = _state()
    mutate(d)
    problems = validate(d)
    assert problems, "expected a validation problem"
    assert any(fragment in msg for msg in problems), problems
    with pytest.raises(ValueError):
        StateInputs.from_dict(d)


def test_unknown_field_is_refused():
    d = _state()
    d["counties"][0]["bogus"] = 1
    with pytest.raises(ValueError, match="unknown fields"):
        StateInputs.from_dict(d)
