"""New Hampshire adapter: single-family parcels (state land use code 11) per county, GRANIT CAMA table.

Disabled until the publication terms are confirmed (rules/nh.yaml, docs/evidence/nh_granit_terms.md).
When enabled, ``fetch`` runs one grouped count query by county: ten numbers, no rows, no names.
"""

from __future__ import annotations

from pathlib import Path

from hre.adapters import arcgis
from hre.adapters.base import Adapter, write_summary
from hre.data.cache import record

MANIFEST = "nh_granit"


def fetch(adapter: Adapter, processed_dir: Path) -> Path:
    if not adapter.enabled:
        raise PermissionError(adapter.rules.get("disabled_reason", "New Hampshire adapter disabled"))
    r = adapter.rules
    counts = arcgis.grouped_counts(r["layer"], r["where"], r["group_by"])
    path = adapter.summary_path(processed_dir)
    write_summary(path, counts, arcgis.query_text(r["layer"], r["where"], r["group_by"]), adapter.sources[0].dataset)
    record(MANIFEST, f"processed/{path.name}", path, url=r["layer"], license=adapter.sources[0].license_text,
           vintage="live service, as fetched", notes=adapter.sources[0].rule + ". Counts only.")
    return path
