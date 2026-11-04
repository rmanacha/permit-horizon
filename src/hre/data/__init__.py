"""Data pipeline: fetchers (one module per source), the download cache, and manifests.

Only ``fetch_hcd`` imports pandas (the optional ``pipeline`` extra). The engine
(``hre.model``) imports numpy alone.
"""
