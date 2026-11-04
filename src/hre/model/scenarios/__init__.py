"""The five benchmark scenarios, one module each (Phase 3).

Every module exposes ``SPEC`` (its register ids, outcome label, ramp, one-line formula and
``core`` function); :func:`hre.model.scenarios.common.run_scenario` turns a ``Spec`` into the
scenario's block of the results file, and ``hre.model.run`` walks ``SPECS``.
"""

from hre.model.scenarios import adu, fees, missing_middle, parking, tod

SPECS = {s.name: s for s in (adu.SPEC, missing_middle.SPEC, tod.SPEC, parking.SPEC, fees.SPEC)}
