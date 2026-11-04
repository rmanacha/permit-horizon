"""The adapter contract (decision 39): counts only, a tolerance test, provenance for every county.

An adapter declares ``state`` and ``sources`` (dataset, area, rule, license_text,
documentation_url, accessed), fetches one small summary of counts per county, and
``enrich(state_inputs)`` fills ``parcel_sf_count`` per county. A county's parcel count replaces
the ACS detached count (``sf_detached``, the exposure the ADU and missing-middle scenarios use)
only when it lies within ``TOLERANCE`` of it; otherwise the ACS count stays and the county is
listed under ``excluded_counties`` with its ratio. The ACS value is kept in ``raw_values`` and the
state file gains an ``adapter`` block (sources, counts, ratios, which counties changed), so a
reader can always see which number the engine used and why.

Counts only: no parcel rows, owner names or addresses are requested, written or cached. The
summary on disk is ``data/processed/{st}_parcels_summary.json``: one number per county and group.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from hre.data.fetch_gazetteer import normalize_name
from hre.schema import StateInputs

RULES_DIR = Path(__file__).resolve().parent / "rules"
TOLERANCE = 0.30      # decision 39's starting rule; the distribution on UT, NH, AZ is in docs/methods/adapters.md


@dataclass
class Source:
    dataset: str
    area: str
    rule: str
    license_text: str
    documentation_url: str
    accessed: str | None = None


@dataclass
class Adapter:
    state: str
    rules: dict[str, Any]
    sources: list[Source] = field(default_factory=list)

    @classmethod
    def from_rules(cls, state: str, rules_dir: Path = RULES_DIR) -> Adapter:
        rules = yaml.safe_load((rules_dir / f"{state.lower()}.yaml").read_text(encoding="utf-8"))
        srcs = [Source(**{k: s.get(k) for k in Source.__dataclass_fields__}) for s in rules["sources"]]
        return cls(state=state, rules=rules, sources=srcs)

    @property
    def enabled(self) -> bool:
        return bool(self.rules.get("enabled"))

    def summary_path(self, processed_dir: Path) -> Path:
        return processed_dir / f"{self.state.lower()}_parcels_summary.json"

    def read_counts(self, processed_dir: Path) -> dict[str, Any]:
        return json.loads(self.summary_path(processed_dir).read_text(encoding="utf-8"))

    def enrich(self, si: StateInputs, processed_dir: Path) -> StateInputs:
        """Replace sf_detached by the parcel count where within tolerance; record everything."""
        summary = self.read_counts(processed_dir)
        by_name = {normalize_name(c.name.removesuffix(" County")): c for c in si.counties}
        parcels: dict[str, int] = {}
        for county_name, n in summary["counts"].items():
            c = by_name.get(normalize_name(county_name.removesuffix(" County")))
            if c is None:
                raise ValueError(f"{self.state} adapter: county {county_name!r} not in the state file")
            parcels[c.fips] = int(n)
        acs = {c.fips: c.sf_detached for c in si.counties}
        used, excluded = apply_tolerance(acs, parcels, float(self.rules.get("tolerance", TOLERANCE)))
        for c in si.counties:
            if c.fips in parcels:
                c.parcel_sf_count = parcels[c.fips]
            if c.fips in used:
                c.notes.append(f"sf_detached from parcel data ({parcels[c.fips]:,}; ACS {acs[c.fips]:,}, "
                               f"ratio {parcels[c.fips] / acs[c.fips]:.3f}); adapter {self.state}")
                c.sf_detached = parcels[c.fips]
        si.adapter = {
            "state": self.state,
            "tolerance": float(self.rules.get("tolerance", TOLERANCE)),
            "sources": [s.__dict__ for s in self.sources],
            "summary_file": self.summary_path(processed_dir).name,
            "fetched_at": summary.get("fetched_at"),
            "raw_values": {f: {"acs_sf_detached": acs[f], "parcel_sf_count": parcels[f],
                               "ratio": round(parcels[f] / acs[f], 4) if acs[f] else None}
                           for f in sorted(parcels)},
            "used_counties": sorted(used),
            "excluded_counties": excluded,
            "provenance": f"{self.sources[0].dataset if self.sources else ''}; counts only "
                          f"({summary.get('query', '')})",
        }
        si.notes.append(f"adapter {self.state}: parcel counts used in {len(used)} of {len(si.counties)} "
                        f"counties; {len(excluded)} outside the {si.adapter['tolerance']:.0%} tolerance keep ACS")
        return si


def apply_tolerance(acs: dict[str, int | None], parcels: dict[str, int],
                    tolerance: float = TOLERANCE) -> tuple[set[str], list[dict[str, Any]]]:
    """Counties whose parcel count is within tolerance of ACS, and the excluded ones with ratios."""
    used: set[str] = set()
    excluded: list[dict[str, Any]] = []
    for f, n in sorted(parcels.items()):
        a = acs.get(f)
        if not a:
            excluded.append({"fips": f, "ratio": None, "why": "no ACS count to compare"})
            continue
        ratio = n / a
        if abs(ratio - 1.0) <= tolerance + 1e-12:      # a ratio of exactly 1.30 is inside
            used.add(f)
        else:
            excluded.append({"fips": f, "ratio": round(ratio, 4),
                             "why": f"parcel count {n:,} is {ratio:.2f} times ACS {a:,}"})
    return used, excluded


def write_summary(path: Path, counts: dict[str, int], query: str, source: str) -> dict[str, Any]:
    out = {"counts": dict(sorted(counts.items())), "query": query, "source": source,
           "fetched_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "note": "Counts only: no parcel rows, owner names or addresses were requested or stored."}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return out
