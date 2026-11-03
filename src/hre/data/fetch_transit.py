"""Major transit stops from the BTS National Transit Map (NTM) plus NTD agency modes.

Stops layer (keyless ArcGIS FeatureServer, paged 2,000 at a time):
https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_National_Transit_Map_Stops/FeatureServer/0
Each stop carries ``stop_type``: the GTFS route types served, as a
semicolon-separated string ("0;3" = light rail and bus). GTFS route types:
0 tram/streetcar/light rail, 1 subway/metro, 2 rail (commuter, intercity),
3 bus, 4 ferry, 5 cable tram, 6 aerial lift, 7 funicular, 11 trolleybus,
12 monorail. ``location_type``: 0 or blank = stop/platform, 1 = station,
2 = entrance/exit, 3 = generic node, 4 = boarding area.

A **major stop** here is any stop or station served by route type 0, 1, 2 or 4
(rail of any kind, streetcar, ferry). Bus rapid transit cannot be told apart
from ordinary bus in GTFS, so it is not counted (limitation in docs/methods/transit.md).

NTD annual service by mode (Socrata, keyless):
https://data.transportation.gov/resource/wwdp-t4re.json?state=NH&report_year=2024
used only to list which agencies in the state report rail or ferry modes, as a
cross-check that the stop filter found what the agencies run.

The saved files are our own assembly of paged results, so the manifest records
the query URL, the page count, and the SHA-256 of the saved file.
"""

from __future__ import annotations

import json
from pathlib import Path

from hre.data.cache import get_json, raw_dir, record
from hre.data.states import StateRef

STOPS_URL = ("https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/"
             "NTAD_National_Transit_Map_Stops/FeatureServer/0/query")
NTD_URL = "https://data.transportation.gov/resource/wwdp-t4re.json"
LICENSE_NTM = ("BTS National Transit Map: public domain (1,237 of 1,239 agency feeds) or "
               "CC-BY-3.0 US (2 feeds); attribution to BTS/NTAD is the only obligation")
LICENSE_NTD = "National Transit Database, U.S. DOT, public domain"
PAGE = 2000
MAJOR_ROUTE_TYPES = frozenset({"0", "1", "2", "4"})
STOP_LOCATION_TYPES = frozenset({"", "0", "1", "null", "none"})
NTD_RAIL_FERRY_MODES = frozenset({"LR", "HR", "CR", "SR", "YR", "MG", "CC", "IP", "AR", "FB"})
NTD_YEAR = "2024"
STOP_FIELDS = "stop_id,stop_name,stop_lat,stop_lon,stop_type,location_type,parent_station,ntd_id,download_date"


def stops_path(state_fips: str, data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "transit" / f"ntm_stops_{state_fips}.json"


def ntd_path(state_fips: str, data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "transit" / f"ntd_modes_{state_fips}.json"


def bbox_for_counties(counties: list[dict], margin: float = 1.5) -> tuple[float, float, float, float]:
    """(west, south, east, north) around the counties' internal points, widened by ``margin`` degrees.

    Internal points sit inside each county, so a margin wider than the largest
    county is needed; 1.5 degrees (about 100 miles) also pulls in stops just
    across the state line, which matter for a nearest-stop distance.
    """
    lats = [c["intpt_lat"] for c in counties]
    lons = [c["intpt_lon"] for c in counties]
    return (min(lons) - margin, min(lats) - margin, max(lons) + margin, max(lats) + margin)


def fetch_ntm_stops(
    state: StateRef, counties: list[dict], data_dir: Path | None = None, force: bool = False,
) -> Path:
    """Page through every stop in the state's bounding box and save a compact JSON list."""
    dest = stops_path(state.fips, data_dir)
    if dest.exists() and not force:
        return dest
    west, south, east, north = bbox_for_counties(counties)
    base = {
        "where": "1=1",
        "geometry": f"{west},{south},{east},{north}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": STOP_FIELDS,
        "returnGeometry": "false",
        "orderByFields": "OBJECTID",
        "resultRecordCount": str(PAGE),
        "f": "json",
    }
    features: list[dict] = []
    offset, pages = 0, 0
    while True:
        data = get_json(STOPS_URL, params={**base, "resultOffset": str(offset)})
        if "error" in data:
            raise RuntimeError(f"NTM stops query failed: {data['error']}")
        batch = [f["attributes"] for f in data.get("features", [])]
        features.extend(batch)
        pages += 1
        if not data.get("exceededTransferLimit") or not batch:
            break
        offset += len(batch)
    compact = [{
        "stop_id": a.get("stop_id"), "stop_name": a.get("stop_name"),
        "lat": a.get("stop_lat"), "lon": a.get("stop_lon"),
        "stop_type": a.get("stop_type"), "location_type": a.get("location_type"),
        "parent_station": a.get("parent_station"), "ntd_id": a.get("ntd_id"),
        "download_date": a.get("download_date"),
    } for a in features]
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = {"bbox": [west, south, east, north], "pages": pages, "count": len(compact), "stops": compact}
    dest.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    dates = sorted({str(a.get("download_date")) for a in features if a.get("download_date")})
    record("transit", f"transit/{dest.name}", dest,
           url=f"{STOPS_URL}?geometry={west},{south},{east},{north}&outFields={STOP_FIELDS}",
           license=LICENSE_NTM, vintage=f"feeds downloaded {dates[0]} to {dates[-1]}" if dates else "unknown",
           notes=f"{len(compact)} stops in {pages} pages of {PAGE} within the state bounding box "
                 f"(1.5 degree margin). Major stop = route type 0, 1, 2 or 4; entrances and nodes dropped.")
    return dest


def fetch_ntd_modes(state: StateRef, data_dir: Path | None = None, force: bool = False) -> Path:
    dest = ntd_path(state.fips, data_dir)
    if dest.exists() and not force:
        return dest
    params = {"state": state.usps, "report_year": NTD_YEAR,
              "$select": "agency,_5_digit_ntd_id,mode,mode_name", "$limit": "5000"}
    rows = get_json(NTD_URL, params=params)
    agencies: dict[str, dict] = {}
    for r in rows:
        key = r.get("_5_digit_ntd_id") or r.get("agency")
        a = agencies.setdefault(key, {"agency": r.get("agency"), "ntd_id": r.get("_5_digit_ntd_id"), "modes": set()})
        a["modes"].add(r.get("mode"))
    out = sorted(({**a, "modes": sorted(m for m in a["modes"] if m)} for a in agencies.values()),
                 key=lambda a: str(a["ntd_id"]))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    record("transit", f"transit/{dest.name}", dest, url=f"{NTD_URL}?state={state.usps}&report_year={NTD_YEAR}",
           license=LICENSE_NTD, vintage=f"report year {NTD_YEAR}",
           notes="Agencies and the modes they report; rail/ferry modes cross-check the stop filter.")
    return dest


def is_major_stop(stop: dict) -> bool:
    types = {t.strip() for t in str(stop.get("stop_type") or "").split(";")}
    loc = str(stop.get("location_type") or "").strip().lower()
    return bool(types & MAJOR_ROUTE_TYPES) and loc in STOP_LOCATION_TYPES


def load_major_stops(state_fips: str, data_dir: Path | None = None) -> list[dict]:
    """Stops with a usable lat/lon that serve rail, streetcar or ferry (bus excluded)."""
    path = stops_path(state_fips, data_dir)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for s in payload["stops"]:
        if not is_major_stop(s):
            continue
        try:
            lat, lon = float(s["lat"]), float(s["lon"])
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        out.append({"lat": lat, "lon": lon, "name": s.get("stop_name"), "stop_type": s.get("stop_type")})
    return out


def load_ntd_rail_agencies(state_fips: str, data_dir: Path | None = None) -> list[dict]:
    path = ntd_path(state_fips, data_dir)
    if not path.exists():
        return []
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [a for a in rows if set(a.get("modes", [])) & NTD_RAIL_FERRY_MODES]
