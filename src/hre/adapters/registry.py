"""Which states have a parcel adapter, and its fetch function."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from hre.adapters import az, nh, ut
from hre.adapters.base import RULES_DIR, Adapter

FETCHERS: dict[str, Callable[[Adapter, Path], Path]] = {"UT": ut.fetch, "NH": nh.fetch, "AZ": az.fetch}


def states() -> list[str]:
    return sorted(p.stem.upper() for p in RULES_DIR.glob("*.yaml"))


def get(state: str) -> Adapter | None:
    """The state's adapter if it has a rules file, enabled or not (callers check ``enabled``)."""
    p = RULES_DIR / f"{state.lower()}.yaml"
    return Adapter.from_rules(state.upper()) if p.exists() else None


def fetch(state: str, processed_dir: Path) -> Path | None:
    a = get(state)
    if a is None or not a.enabled or state.upper() not in FETCHERS:
        return None
    return FETCHERS[state.upper()](a, processed_dir)
