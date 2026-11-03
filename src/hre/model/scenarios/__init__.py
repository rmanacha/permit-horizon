"""The five benchmark scenarios, one module each (Phase 3).

Every module exposes ``SPEC`` (its register ids, outcome label, ramp and one-line formula)
and ``run_<name>(state, params, law, ctx)``, which returns the scenario's block of the
results file through :func:`hre.model.scenarios.common.run_scenario`.
"""

from hre.model.scenarios import adu, fees, missing_middle, parking, tod

SPECS = {s.name: s for s in (adu.SPEC, missing_middle.SPEC, tod.SPEC, parking.SPEC, fees.SPEC)}
SCENARIO_NAMES = tuple(SPECS)
