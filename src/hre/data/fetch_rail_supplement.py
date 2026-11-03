"""Rail stops missing from the National Transit Map, taken from the operators' own GTFS feeds.

The National Transit Map has no feed for two Connecticut commuter lines, so
before this supplement Hartford, Meriden, Wallingford, Old Saybrook and New
London all read as far from rail. Both feeds are the ones CTtransit's developer
page (https://www.cttransit.com/about/developers) names as current:

- CTrail Hartford Line (New Haven to Springfield): CTDOT's feed
  https://ctrides.com/hlgtfs.zip ; routes of GTFS route type 2.
- Shore Line East (Stamford to New London): Amtrak's national feed
  https://content.amtrak.com/content/gtfs/GTFS.zip , where Shore Line East is
  agency 1230. (The CTDOT feed also lists Shore Line East stops, but with no
  trips, the bus route type and names attached to the wrong points.)

Only the stops served by a matching route's trips are kept (route types 0, 1,
2 or 4, as in ``fetch_transit``). A station already in the National Transit
Map (New Haven, Bridgeport, Stamford) appears twice; that cannot change a
nearest-stop distance. Other states' gaps found in the check are written up in
docs/methods/transit.md; none of them is a missing feed of this kind.
"""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

from hre.data.cache import fetch, raw_dir
from hre.data.fetch_transit import MAJOR_ROUTE_TYPES


@dataclass(frozen=True)
class Feed:
    key: str
    line: str
    url: str
    license: str
    agency_id: str | None = None  # keep only this agency's routes (None = every agency)


LICENSE_CTDOT = ("CTtransit GTFS Data Terms of Use: non-exclusive, limited, revocable right to use, "
                 "reproduce and redistribute; no use of CTtransit trademarks; provided as is")
LICENSE_AMTRAK = ("Amtrak publishes no licence or terms for its GTFS feed; public download, "
                  "station locations only are used and the file is not redistributed")

FEEDS: dict[str, tuple[Feed, ...]] = {
    "09": (
        Feed("ct_hartford_line", "CTrail Hartford Line", "https://ctrides.com/hlgtfs.zip", LICENSE_CTDOT),
        Feed("amtrak", "Shore Line East", "https://content.amtrak.com/content/gtfs/GTFS.zip", LICENSE_AMTRAK,
             agency_id="1230"),
    ),
}


def feed_path(feed: Feed, data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "rail_supplement" / f"{feed.key}_gtfs.zip"


def feeds_for(state_fips: str) -> tuple[Feed, ...]:
    return FEEDS.get(state_fips, ())


def fetch_rail_supplement(state_fips: str, data_dir: Path | None = None, force: bool = False) -> list[Path]:
    """One manifest per feed (``data/manifests/gtfs_{key}.json``): each operator has its own terms."""
    return [fetch(f.url, feed_path(f, data_dir), source=f"gtfs_{f.key}", license=f.license,
                  vintage="feed current on the fetch date (service dates in its feed_info.txt or calendar.txt)",
                  force=force,
                  notes=f"Operator GTFS feed used only for the {f.line} stations, which the National "
                        "Transit Map lacks; see src/hre/data/fetch_rail_supplement.py.")
            for f in feeds_for(state_fips)]


def _rows(z: zipfile.ZipFile, name: str) -> list[dict]:
    with z.open(name) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", newline="")))


def load_feed_stops(path: Path, agency_id: str | None = None) -> list[dict]:
    """Stops served by rail, streetcar or ferry trips in one GTFS zip, in load_major_stops' shape."""
    with zipfile.ZipFile(path) as z:
        routes = {r["route_id"]: r["route_type"].strip() for r in _rows(z, "routes.txt")
                  if r.get("route_type", "").strip() in MAJOR_ROUTE_TYPES
                  and (agency_id is None or r.get("agency_id", "").strip() == agency_id)}
        trips = {t["trip_id"]: routes[t["route_id"]] for t in _rows(z, "trips.txt") if t["route_id"] in routes}
        served: dict[str, set[str]] = {}
        for st in _rows(z, "stop_times.txt"):
            if st["trip_id"] in trips:
                served.setdefault(st["stop_id"], set()).add(trips[st["trip_id"]])
        out = []
        for s in _rows(z, "stops.txt"):
            if s["stop_id"] not in served:
                continue
            try:
                lat, lon = float(s["stop_lat"]), float(s["stop_lon"])
            except (TypeError, ValueError):
                continue
            out.append({"lat": lat, "lon": lon, "name": s.get("stop_name"),
                        "stop_type": ";".join(sorted(served[s["stop_id"]]))})
    return sorted(out, key=lambda s: (s["lat"], s["lon"]))


def load_supplement_stops(state_fips: str, data_dir: Path | None = None) -> tuple[list[dict], list[str]]:
    """(stops from every cached supplementary feed for the state, one note per feed)."""
    stops, notes = [], []
    for f in feeds_for(state_fips):
        path = feed_path(f, data_dir)
        if not path.exists():
            notes.append(f"transit: {f.line} feed not in the cache, so its stations are missing.")
            continue
        got = load_feed_stops(path, f.agency_id)
        stops.extend(got)
        notes.append(f"transit: {len(got)} {f.line} stops added from the operator's GTFS feed "
                     "(missing from the National Transit Map).")
    return stops, notes
