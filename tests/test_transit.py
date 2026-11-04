"""Haversine against known distances, the major-stop filter, and nearest-stop search."""

import numpy as np
import pytest

from hre.build.transit_proximity import haversine_miles, nearest_stop_miles
from hre.data import fetch_transit


def test_haversine_known_distances():
    # One degree of latitude is 69.09 statute miles on this sphere.
    assert haversine_miles(0, 0, 1, 0) == pytest.approx(69.09, abs=0.02)
    # Half way round the sphere is pi times the radius.
    assert haversine_miles(0, 0, 0, 180) == pytest.approx(3.14159265 * 3958.7613, rel=1e-6)
    # New York City Hall to Los Angeles City Hall: about 2,445 statute miles.
    assert haversine_miles(40.7128, -74.0060, 34.0522, -118.2437) == pytest.approx(2445, rel=0.002)
    assert haversine_miles(43.0, -71.0, 43.0, -71.0) == 0.0


def test_nearest_stop_miles_chunked_and_empty():
    bg_lat, bg_lon = np.array([44.0, 44.5]), np.array([-100.0, -100.5])
    d = nearest_stop_miles(bg_lat, bg_lon, [44.002, 44.6505], [-100.0, -100.65], chunk=1)
    assert d[0] == pytest.approx(0.138, abs=0.002) and d[1] == pytest.approx(13.0, abs=0.5)
    assert np.isnan(nearest_stop_miles(bg_lat, bg_lon, [], [])).all()


@pytest.mark.parametrize(
    "stop, expected",
    [
        ({"stop_type": "0;3", "location_type": "1"}, True),      # light rail station
        ({"stop_type": "2", "location_type": ""}, True),         # commuter rail stop
        ({"stop_type": "4", "location_type": "0"}, True),        # ferry
        ({"stop_type": "3", "location_type": "0"}, False),       # bus only
        ({"stop_type": "11", "location_type": "0"}, False),      # trolleybus is not rail (no substring match on '1')
        ({"stop_type": "0", "location_type": "2"}, False),       # station entrance
        ({"stop_type": "1", "location_type": "3"}, False),       # generic node
        ({"stop_type": None, "location_type": None}, False),
    ],
)
def test_is_major_stop(stop, expected):
    assert fetch_transit.is_major_stop(stop) is expected


def test_load_major_stops_from_fixture(sample_dir):
    stops = fetch_transit.load_major_stops("99", sample_dir)
    assert sorted(s["name"] for s in stops) == ["Alder Center Platform", "Alder Center Station", "Birch Landing"]
    rail = fetch_transit.load_ntd_rail_agencies("99", sample_dir)
    assert [a["agency"] for a in rail] == ["Alder Transit", "Birch Ferries"]


def test_bbox_margin(sample_dir):
    from hre.data import fetch_gazetteer

    counties = fetch_gazetteer.load_counties("99", sample_dir)
    west, south, east, north = fetch_transit.bbox_for_counties(counties)
    assert (west, south, east, north) == (-102.1, 42.55, -98.55, 46.1)


def test_stops_page_retries_a_transient_error(monkeypatch):
    calls = []

    def fake(url, params=None, **kw):
        calls.append(params["resultOffset"])
        return {"error": {"code": 400}} if len(calls) == 1 else {"features": [], "exceededTransferLimit": False}

    monkeypatch.setattr(fetch_transit, "get_json", fake)
    assert fetch_transit._stops_page({}, 4000, pause=0) == {"features": [], "exceededTransferLimit": False}
    assert calls == ["4000", "4000"]
    monkeypatch.setattr(fetch_transit, "get_json", lambda url, params=None, **kw: {"error": {"code": 400}})
    with pytest.raises(RuntimeError, match="after 4 tries"):
        fetch_transit._stops_page({}, 0, pause=0)
