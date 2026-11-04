"""State lookup table: USPS code, FIPS code, and the names each source uses.

Kept as plain tuples so there is one place to look when a source spells a
state differently. ``ZZ`` is the synthetic two-county fixture state used by
``make demo`` and the tests; it has no URLs and ``hre fetch`` refuses it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StateRef:
    usps: str
    fips: str
    name: str
    synthetic: bool = False

    @property
    def name_nospace(self) -> str:
        """Name as the Census Address Count Listing Files spell it (no spaces)."""
        return self.name.replace(" ", "")


_TABLE: tuple[tuple[str, str, str], ...] = (
    ("AL", "01", "Alabama"),
    ("AK", "02", "Alaska"),
    ("AZ", "04", "Arizona"),
    ("AR", "05", "Arkansas"),
    ("CA", "06", "California"),
    ("CO", "08", "Colorado"),
    ("CT", "09", "Connecticut"),
    ("DE", "10", "Delaware"),
    ("DC", "11", "District of Columbia"),
    ("FL", "12", "Florida"),
    ("GA", "13", "Georgia"),
    ("HI", "15", "Hawaii"),
    ("ID", "16", "Idaho"),
    ("IL", "17", "Illinois"),
    ("IN", "18", "Indiana"),
    ("IA", "19", "Iowa"),
    ("KS", "20", "Kansas"),
    ("KY", "21", "Kentucky"),
    ("LA", "22", "Louisiana"),
    ("ME", "23", "Maine"),
    ("MD", "24", "Maryland"),
    ("MA", "25", "Massachusetts"),
    ("MI", "26", "Michigan"),
    ("MN", "27", "Minnesota"),
    ("MS", "28", "Mississippi"),
    ("MO", "29", "Missouri"),
    ("MT", "30", "Montana"),
    ("NE", "31", "Nebraska"),
    ("NV", "32", "Nevada"),
    ("NH", "33", "New Hampshire"),
    ("NJ", "34", "New Jersey"),
    ("NM", "35", "New Mexico"),
    ("NY", "36", "New York"),
    ("NC", "37", "North Carolina"),
    ("ND", "38", "North Dakota"),
    ("OH", "39", "Ohio"),
    ("OK", "40", "Oklahoma"),
    ("OR", "41", "Oregon"),
    ("PA", "42", "Pennsylvania"),
    ("RI", "44", "Rhode Island"),
    ("SC", "45", "South Carolina"),
    ("SD", "46", "South Dakota"),
    ("TN", "47", "Tennessee"),
    ("TX", "48", "Texas"),
    ("UT", "49", "Utah"),
    ("VT", "50", "Vermont"),
    ("VA", "51", "Virginia"),
    ("WA", "53", "Washington"),
    ("WV", "54", "West Virginia"),
    ("WI", "55", "Wisconsin"),
    ("WY", "56", "Wyoming"),
    ("PR", "72", "Puerto Rico"),
)

STATES: dict[str, StateRef] = {u: StateRef(u, f, n) for u, f, n in _TABLE}
STATES["ZZ"] = StateRef("ZZ", "99", "Zetaland", synthetic=True)

BY_FIPS: dict[str, StateRef] = {s.fips: s for s in STATES.values()}

# The 50 states plus DC: what "--all" means. Puerto Rico is excluded from
# "--all" because several sources (PEP county housing units, FHFA, NZLUD)
# do not cover it; it can still be requested by code.
ALL_STATES: tuple[str, ...] = tuple(u for u, _, _ in _TABLE if u != "PR")


def lookup(code: str) -> StateRef:
    """Return the StateRef for a USPS code (case-insensitive) or a 2-digit FIPS."""
    key = code.strip().upper()
    if key in STATES:
        return STATES[key]
    if key in BY_FIPS:
        return BY_FIPS[key]
    raise KeyError(f"unknown state code {code!r}; use a USPS code such as NH or a 2-digit FIPS")
