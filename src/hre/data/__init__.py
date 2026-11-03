"""Data pipeline: fetchers (one module per source), the download cache, and manifests.

Only this package and ``hre.build`` may import pandas. The engine
(``hre.model``, Phase 2) imports numpy alone.
"""
