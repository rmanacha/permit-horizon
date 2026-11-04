"""Grouped counts from an ArcGIS FeatureServer or MapServer layer: the server sums, we never see rows.

    counts = grouped_counts(url, where="TYPE = 'single_family'", group_by="COUNTY")
    -> {"Salt Lake": 240491, ...}

One ``query`` request with ``outStatistics`` (count of the object id) grouped by one field. The
response holds one line per group; no geometry, no attributes beyond the group name and count.
"""

from __future__ import annotations

import json
from typing import Any

import requests

from hre.data.cache import user_agent


def grouped_counts(layer_url: str, where: str, group_by: str, count_field: str = "OBJECTID",
                   session: requests.Session | None = None, timeout: float = 120.0) -> dict[str, int]:
    params = {
        "where": where,
        "groupByFieldsForStatistics": group_by,
        "outStatistics": json.dumps([{"statisticType": "count", "onStatisticField": count_field,
                                      "outStatisticFieldName": "n"}]),
        "returnGeometry": "false",
        "f": "json",
    }
    sess = session or requests.Session()
    r = sess.get(layer_url.rstrip("/") + "/query", params=params,
                 headers={"User-Agent": user_agent()}, timeout=timeout)
    r.raise_for_status()
    d: dict[str, Any] = r.json()
    if "error" in d:
        raise RuntimeError(f"ArcGIS query failed: {d['error']}")
    out: dict[str, int] = {}
    for feat in d.get("features", []):
        a = feat["attributes"]
        key = a.get(group_by)
        if key is None:
            continue
        out[str(key)] = out.get(str(key), 0) + int(a["n"])
    return out


def query_text(layer_url: str, where: str, group_by: str) -> str:
    return f"{layer_url}/query: count of features where {where}, grouped by {group_by}"


def count(layer_url: str, where: str, distinct_field: str | None = None,
          session: requests.Session | None = None, timeout: float = 300.0) -> int:
    """One number: features matching ``where``, or distinct values of ``distinct_field`` among them."""
    params = {"where": where, "returnCountOnly": "true", "returnGeometry": "false", "f": "json"}
    if distinct_field:
        params.update({"outFields": distinct_field, "returnDistinctValues": "true"})
    sess = session or requests.Session()
    r = sess.get(layer_url.rstrip("/") + "/query", params=params,
                 headers={"User-Agent": user_agent()}, timeout=timeout)
    r.raise_for_status()
    d: dict[str, Any] = r.json()
    if "error" in d or "count" not in d:
        raise RuntimeError(f"ArcGIS count failed: {d.get('error', d)}")
    return int(d["count"])
