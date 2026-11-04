"""HTTP GET with the Python standard library (``urllib``), so the pipeline needs no HTTP package.

Every download in the project goes through this module: the data cache (``hre.data.cache``), the
parcel count queries (``hre.adapters.arcgis``) and the current-law quote check
(``hre.validation.law_quotes``). It replaced ``requests``, whose certificate bundle (certifi) is
licensed MPL-2.0, a copyleft licence the project does not accept for any dependency. TLS
certificates come from the operating system's trust store through Python's default SSL context
(macOS ``/etc/ssl/cert.pem``, the ``ca-certificates`` bundle on Linux); set ``SSL_CERT_FILE`` to
use another bundle.

    with_retries(lambda: get_bytes(url), retries=4)        # bytes, retried on 429/5xx and network errors
    download(url, dest)                                     # streamed to a file
    get_json(url, params={"f": "json"})                     # parsed JSON
"""

from __future__ import annotations

import http.client
import http.cookiejar
import json
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
CHUNK = 1 << 20


class HTTPError(OSError):
    """The server answered with an error status (4xx or 5xx)."""

    def __init__(self, status: int, url: str) -> None:
        super().__init__(f"{status} for {url}")
        self.status = status
        self.url = url


# Network failures worth retrying (a refused or reset connection, DNS, TLS, a timeout).
TRANSIENT: tuple[type[BaseException], ...] = (urllib.error.URLError, ConnectionError, TimeoutError,
                                              socket.timeout, ssl.SSLError, http.client.HTTPException)
# Everything a GET in this module can raise for a reason outside our code.
ERRORS: tuple[type[BaseException], ...] = (HTTPError, *TRANSIENT)


def _timeout(timeout: float | tuple[float, float]) -> float:
    """urllib takes one socket timeout; a (connect, read) pair uses the longer read value."""
    return float(max(timeout)) if isinstance(timeout, tuple) else float(timeout)


def build_url(url: str, params: dict[str, Any] | None = None) -> str:
    if not params:
        return url
    return url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)


def _open(url: str, params: dict[str, Any] | None, headers: dict[str, str] | None,
          timeout: float | tuple[float, float]) -> Any:
    req = urllib.request.Request(build_url(url, params), headers={"Accept": "*/*", **(headers or {})},
                                 method="GET")
    # A cookie jar per request, as a browser keeps one across the redirects of one page.
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
                                         urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    try:
        return opener.open(req, timeout=_timeout(timeout))
    except urllib.error.HTTPError as e:
        e.close()
        raise HTTPError(e.code, url) from None


def get_bytes(url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None,
              timeout: float | tuple[float, float] = 60.0) -> bytes:
    with _open(url, params, headers, timeout) as resp:
        return resp.read()


def get_json(url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None,
             timeout: float | tuple[float, float] = 60.0) -> Any:
    h = {"Accept": "application/json", **(headers or {})}
    return json.loads(get_bytes(url, params=params, headers=h, timeout=timeout))


def download(url: str, dest: Path, *, params: dict[str, Any] | None = None,
             headers: dict[str, str] | None = None, timeout: float | tuple[float, float] = 180.0) -> None:
    """Stream ``url`` into ``dest`` in 1 MB chunks (the caller renames a partial file into place)."""
    with _open(url, params, headers, timeout) as resp, open(dest, "wb") as f:
        while chunk := resp.read(CHUNK):
            f.write(chunk)


def with_retries[T](call: Callable[[], T], *, retries: int = 4, pause: Callable[[int], float] | None = None) -> T:
    """Run ``call``; on a 429/5xx status or a network failure wait and try again, up to ``retries`` more times.

    Any other status (a 404, a 403) is raised at once. The wait doubles from 1 second, at most 30.
    """
    wait = pause or (lambda attempt: min(2.0 ** attempt, 30.0))
    for attempt in range(retries + 1):
        try:
            return call()
        except HTTPError as e:
            if e.status not in RETRY_STATUSES or attempt == retries:
                raise
        except TRANSIENT:
            if attempt == retries:
                raise
        time.sleep(wait(attempt))
    raise RuntimeError("unreachable")  # pragma: no cover
