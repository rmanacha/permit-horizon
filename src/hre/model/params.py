"""The parameter object the engine reads (decision 42: no YAML in the engine).

``hre.assumptions.loader`` reads ``src/hre/assumptions/parameters.yaml`` and
builds a :class:`Params`. Engine code asks for a value with ``params[<id>]`` and
gets the value at the level currently selected for that id: every id starts at
``mid``; ``params.at({<id>: "high"})`` returns a copy with one id moved, which is
how the tornado and the joint cases swing assumptions one at a time or together.
``params.with_values({<id>: 1.0})`` sets a user value (an override).

Rule enforced by ``tests/test_register.py``: every ``params[...]`` key written
anywhere under ``src/hre`` must exist in the register.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

LEVELS = ("low", "mid", "high")


@dataclass(frozen=True)
class Params:
    """Register entries plus the level (or user value) chosen for each id."""

    entries: dict[str, dict[str, Any]]
    levels: dict[str, str] = field(default_factory=dict)
    values: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, pid: str) -> Any:
        if pid not in self.entries:
            raise KeyError(f"parameter {pid!r} is not in the register")
        if pid in self.values:
            return self.values[pid]
        return self.entries[pid][self.levels.get(pid, "mid")]

    def __contains__(self, pid: object) -> bool:
        return pid in self.entries

    def level_value(self, pid: str, level: str) -> Any:
        """The register value at one named level, whatever level is selected."""
        if level not in LEVELS:
            raise ValueError(f"level must be one of {LEVELS}, got {level!r}")
        return self.entries[pid][level]

    def entry(self, pid: str) -> dict[str, Any]:
        return self.entries[pid]

    def level_of(self, pid: str) -> str:
        return "user" if pid in self.values else self.levels.get(pid, "mid")

    def at(self, levels: dict[str, str]) -> Params:
        """A copy with some ids moved to ``low``, ``mid`` or ``high``."""
        for pid, lv in levels.items():
            if pid not in self.entries:
                raise KeyError(f"parameter {pid!r} is not in the register")
            if lv not in LEVELS:
                raise ValueError(f"level must be one of {LEVELS}, got {lv!r}")
        vals = {k: v for k, v in self.values.items() if k not in levels}
        return Params(self.entries, {**self.levels, **levels}, vals)

    def all_at(self, level: str, ids: list[str] | None = None) -> Params:
        """Every id (or the listed ids) at one level: the low, mid or high assumption set.

        A user value (``with_values``, ``hre run --set``) holds in every set: those ids keep it.
        Only ``at({id: level})`` for that id itself replaces it (a tornado swing, a joint case).
        """
        chosen = ids if ids is not None else list(self.entries)
        return self.at({pid: level for pid in chosen if pid not in self.values})

    def with_values(self, values: dict[str, Any]) -> Params:
        """A copy with user values for some ids (shown as level ``user``)."""
        for pid in values:
            if pid not in self.entries:
                raise KeyError(f"parameter {pid!r} is not in the register")
        return Params(self.entries, dict(self.levels), {**self.values, **values})

    def display(self, pid: str, level: str | None = None) -> str:
        """The register's display text for one end (``levels`` field)."""
        lv = level or self.levels.get(pid, "mid")
        return str(self.entries[pid].get("levels", {}).get(lv, self.entries[pid][lv]))
