"""ACS bulk, centers of population and FHFA parsers on the ZZ fixtures."""

from hre.data import fetch_acs, fetch_cenpop, fetch_fhfa


def test_acs_county_fields(sample_dir):
    c = fetch_acs.load_county_acs("99", sample_dir)
    alder = c["99001"]
    assert alder["housing_units"] == 20500 and alder["sf_detached"] == 12000 and alder["sf_attached"] == 800
    assert alder["units_2_4"] == 900 and alder["units_5plus"] == 5800 and alder["mobile"] == 900
    assert alder["owner_occupied"] == 12500 and alder["renter_occupied"] == 6000 and alder["vacant"] == 2000
    assert alder["median_value"] == 350000 and alder["median_rent"] == 1400
    # units in structure sum to the total (boats/RVs/vans, 100, are not stored)
    assert alder["sf_detached"] + alder["sf_attached"] + alder["units_2_4"] + alder["units_5plus"] + alder["mobile"] + 100 == alder["housing_units"]
    assert set(c) == {"99001", "99003"}  # the NH row and the place row are filtered out


def test_acs_block_groups(sample_dir):
    bg = fetch_acs.load_block_group_acs("99", sample_dir)
    assert len(bg) == 9 and "990030002002" not in bg
    assert bg["990010001001"]["housing_units"] == 600 and bg["990010001001"]["sf_detached"] == 360


def test_acs_places_and_names(sample_dir):
    places = fetch_acs.load_place_acs("99", sample_dir)
    assert places["9900100"]["median_value"] == 175000 and places["9900100"]["sf_detached"] == 6000
    assert fetch_acs.load_geo_names(fetch_acs.PREFIX_PLACE, "99", sample_dir) == {"9900100": "Alderton city, Zetaland"}


def test_acs_cell_nulls():
    assert fetch_acs._cell("") is None and fetch_acs._cell("-666666666") is None
    assert fetch_acs._cell("12") == 12 and fetch_acs._cell("-1") == -1


def test_cenpop(sample_dir):
    rows = fetch_cenpop.load_cenpop("99", sample_dir)
    assert len(rows) == 10 and rows[0]["geoid"] == "990010001001" and rows[0]["county_fips"] == "99001"
    assert rows[0]["lat"] == 44.0 and rows[0]["population"] == 1200
    assert all(len(r["geoid"]) == 12 for r in rows)


def test_fhfa(sample_dir):
    hpi = fetch_fhfa.load_fhfa("99", sample_dir)
    assert sorted(hpi["99001"]) == [str(y) for y in range(2015, 2026)]  # 2014 is outside the window
    assert "2016" not in hpi["99003"] and "2017" in hpi["99003"]       # "." cell dropped
    assert hpi["99001"]["2015"] == round(100 * 1.05**2, 2)
    assert "33001" not in hpi
