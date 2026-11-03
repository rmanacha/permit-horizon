"""Operator GTFS feeds that fill National Transit Map gaps (offline, tiny zips built in the test)."""

import shutil
import zipfile

import pytest

from hre.build.build_state_inputs import MissingSource, build_state
from hre.data import fetch_rail_supplement as rs


def _write_gtfs(path, routes, trips, stop_times, stops):
    path.parent.mkdir(parents=True, exist_ok=True)
    tables = {
        "routes.txt": ["route_id,agency_id,route_long_name,route_type"] + routes,
        "trips.txt": ["route_id,service_id,trip_id"] + trips,
        "stop_times.txt": ["trip_id,arrival_time,departure_time,stop_id,stop_sequence"] + stop_times,
        "stops.txt": ["stop_id,stop_name,stop_lat,stop_lon"] + stops,
    }
    with zipfile.ZipFile(path, "w") as z:
        for name, lines in tables.items():
            z.writestr(name, "﻿" + "\n".join(lines) + "\n")
    return path


def test_only_stops_on_matching_rail_trips(tmp_path):
    path = _write_gtfs(
        tmp_path / "feed.zip",
        routes=["R,A1,Shore Line,2", "B,A1,Shuttle,3", "X,A2,Other railroad,2"],
        trips=["R,1,t1", "B,1,t2", "X,1,t3"],
        stop_times=["t1,08:00:00,08:00:00,s1,1", "t1,08:10:00,08:10:00,s2,2",
                    "t2,09:00:00,09:00:00,s3,1", "t3,10:00:00,10:00:00,s4,1"],
        stops=["s1,Branford,41.2745,-72.8172", "s2,Guilford,41.2756,-72.6735",
               "s3,Bus stop,41.30,-72.90", "s4,Elsewhere,40.0,-75.0", "s5,Unserved,41.0,-73.0"],
    )
    stops = rs.load_feed_stops(path, agency_id="A1")
    assert [s["name"] for s in stops] == ["Branford", "Guilford"]           # bus, other agency, unserved dropped
    assert stops[0] == {"lat": 41.2745, "lon": -72.8172, "name": "Branford", "stop_type": "2"}
    assert {s["name"] for s in rs.load_feed_stops(path)} == {"Branford", "Guilford", "Elsewhere"}


def test_connecticut_feeds_are_listed():
    lines = {f.line: f for f in rs.feeds_for("09")}
    assert set(lines) == {"CTrail Hartford Line", "Shore Line East"}
    assert lines["Shore Line East"].agency_id == "1230"
    assert rs.feeds_for("33") == ()


@pytest.fixture
def zz_with_feed(sample_dir, tmp_path, monkeypatch):
    """ZZ plus one supplementary rail station on top of block group 990010002002, which is far from any stop."""
    data = tmp_path / "sample"
    shutil.copytree(sample_dir, data)
    feed = rs.Feed("zz_rail", "Zeta Line", "https://example.invalid/zz.zip", "test")
    _write_gtfs(rs.feed_path(feed, data), routes=["L,,Zeta Line,2"], trips=["L,1,t1"],
                stop_times=["t1,08:00:00,08:00:00,z1,1"], stops=["z1,Zeta Station,44.151,-100.151"])
    monkeypatch.setitem(rs.FEEDS, "99", (feed,))
    return data, feed


def test_build_adds_supplementary_stops(zz_with_feed):
    data, _ = zz_with_feed
    si, summary = build_state("ZZ", data)
    assert summary["major_stops"] == 4 and summary["bg_within_half_mile"] == 4       # 3 without the feed
    bgs = {b.geoid: b for b in si.block_groups}
    assert bgs["990010002002"].near_transit_quarter_mile
    assert any("1 Zeta Line stops added" in n for n in si.notes)


def test_build_needs_the_feed(zz_with_feed):
    data, feed = zz_with_feed
    rs.feed_path(feed, data).unlink()
    with pytest.raises(MissingSource, match="Zeta Line"):
        build_state("ZZ", data)
    si, summary = build_state("ZZ", data, lenient=True)
    assert summary["bg_within_half_mile"] == 3
    assert any("Zeta Line feed not in the cache" in n for n in si.notes)
