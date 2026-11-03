"""Permit Horizon engine: pure functions, numpy only (decision 42).

Allowed imports inside this package: numpy, math, json, dataclasses, typing
(and ``__future__``). No file I/O; inputs arrive as ``hre.schema.StateInputs``
objects and a :class:`hre.model.params.Params`; outputs are plain dicts.
``tests/test_engine_purity.py`` enforces both rules.
"""
