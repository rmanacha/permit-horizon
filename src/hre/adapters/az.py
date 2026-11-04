"""Arizona adapter: single-family parcels in Maricopa and Pinal, Arizona Department of Revenue use codes.

Each county has its own assessor service; one count query per county (distinct parcel numbers, so
a parcel the layer repeats for each condominium unit counts once). No rows are requested: both
layers carry owner and mailing fields, which never leave the server. Other counties keep ACS.
"""

from __future__ import annotations

from pathlib import Path

from hre.adapters import arcgis
from hre.adapters.base import Adapter, write_summary
from hre.data.cache import record

MANIFEST = "az_assessors"


def fetch(adapter: Adapter, processed_dir: Path) -> Path:
    counts, queries = {}, []
    for q in adapter.rules["queries"]:
        counts[q["county"]] = arcgis.count(q["layer"], q["where"], q.get("distinct_field"))
        queries.append(f"{q['county']}: {q['layer']}/query, distinct {q.get('distinct_field')} where {q['where']}")
    path = adapter.summary_path(processed_dir)
    write_summary(path, counts, "; ".join(queries), "; ".join(s.dataset for s in adapter.sources))
    record(MANIFEST, f"processed/{path.name}", path, url=adapter.rules["queries"][0]["layer"],
           license="; ".join(f"{s.dataset}: {s.license_text}" for s in adapter.sources),
           vintage="live services, as fetched",
           notes="Arizona Department of Revenue use codes 0100 to 0179 counted once per parcel in "
                 "Maricopa and Pinal. Counts only.")
    return path
