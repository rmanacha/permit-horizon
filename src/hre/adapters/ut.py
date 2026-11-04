"""Utah adapter: single-family parcels per county from the Housing Unit Inventory (CC BY 4.0).

``fetch`` runs one grouped count query (no rows) and writes ``data/processed/ut_parcels_summary.json``
and the ``ut_hui`` manifest; ``enrich`` (in ``base.Adapter``) applies the tolerance rule.
"""

from __future__ import annotations

from pathlib import Path

from hre.adapters import arcgis
from hre.adapters.base import Adapter, write_summary
from hre.data.cache import record

MANIFEST = "ut_hui"


def fetch(adapter: Adapter, processed_dir: Path) -> Path:
    r = adapter.rules
    counts = arcgis.grouped_counts(r["layer"], r["where"], r["group_by"])
    path = adapter.summary_path(processed_dir)
    write_summary(path, counts, arcgis.query_text(r["layer"], r["where"], r["group_by"]), adapter.sources[0].dataset)
    record(MANIFEST, f"processed/{path.name}", path, url=r["layer"], license=adapter.sources[0].license_text,
           vintage="live service, as fetched", notes=adapter.sources[0].rule + " Counts only.")
    return path
