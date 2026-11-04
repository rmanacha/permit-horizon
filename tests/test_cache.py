"""Cache: fetch streams a file, hashes it, writes a sorted manifest, and skips unchanged files."""

import hashlib
import http.server
import json
import threading
from functools import partial

import pytest

from hre.data import cache


@pytest.fixture
def local_server(tmp_path):
    root = tmp_path / "www"
    root.mkdir()
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    handler.log_message = lambda *a, **k: None  # type: ignore[attr-defined]
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield root, f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown()


@pytest.fixture
def dirs(tmp_path):
    """The raw cache and manifest folders the autouse conftest fixture already points the module at."""
    return tmp_path / "raw", tmp_path / "manifests"


def test_fetch_writes_file_and_manifest(local_server, dirs):
    root, base = local_server
    raw, man = dirs
    (root / "tiny.txt").write_bytes(b"hello,permit\n")
    dest = raw / "demo" / "tiny.txt"
    out = cache.fetch(f"{base}/tiny.txt", dest, source="demo", license="public domain",
                      vintage="2026", notes="unit test")
    assert out == dest and dest.read_bytes() == b"hello,permit\n"
    m = json.loads((man / "demo.json").read_text())
    entry = m["files"]["demo/tiny.txt"]
    assert entry["sha256"] == hashlib.sha256(b"hello,permit\n").hexdigest()
    assert entry["bytes"] == 13 and entry["url"].endswith("/tiny.txt")
    assert entry["vintage"] == "2026" and entry["fetched_at"].endswith("Z")
    assert m["license"] == "public domain" and m["notes"] == "unit test" and m["source"] == "demo"
    assert list(m) == sorted(m) and list(entry) == sorted(entry)


def test_fetch_is_idempotent_and_refetches_on_change(local_server, dirs):
    root, base = local_server
    raw, man = dirs
    (root / "f.txt").write_bytes(b"v1")
    dest = raw / "demo" / "f.txt"
    cache.fetch(f"{base}/f.txt", dest, source="demo", license="x", vintage="1")
    first = json.loads((man / "demo.json").read_text())["files"]["demo/f.txt"]
    # Change the remote file: without force, the cached copy still matches the manifest, so no refetch.
    (root / "f.txt").write_bytes(b"v2")
    cache.fetch(f"{base}/f.txt", dest, source="demo", license="x", vintage="1")
    assert dest.read_bytes() == b"v1"
    # With force, it is re-downloaded and the manifest updated.
    cache.fetch(f"{base}/f.txt", dest, source="demo", license="x", vintage="1", force=True)
    second = json.loads((man / "demo.json").read_text())["files"]["demo/f.txt"]
    assert dest.read_bytes() == b"v2" and second["sha256"] != first["sha256"]


def test_fetch_404_raises_without_retry_loop(local_server, dirs):
    _, base = local_server
    raw, _ = dirs
    from hre.data.net import HTTPError

    with pytest.raises(HTTPError, match="404"):
        cache.fetch(f"{base}/missing.txt", raw / "demo" / "missing.txt", source="demo",
                    license="x", vintage="1", retries=1)
    assert not (raw / "demo" / "missing.txt").exists()


def test_record_assembled_file(dirs):
    raw, man = dirs
    p = raw / "transit" / "stops_33.json"
    p.parent.mkdir(parents=True)
    p.write_text("[]")
    cache.record("transit", "transit/stops_33.json", p, url="https://example/query",
                 license="public domain", vintage="2026-09")
    m = json.loads((man / "transit.json").read_text())
    assert m["files"]["transit/stops_33.json"]["bytes"] == 2


def test_dotenv_and_user_agent(tmp_path, monkeypatch):
    monkeypatch.setenv("HRE_CONTACT_EMAIL", "placeholder")
    monkeypatch.delenv("HRE_CONTACT_EMAIL")      # recorded, so the value load_dotenv writes is undone after the test
    env = tmp_path / ".env"
    env.write_text("# comment\nHRE_CONTACT_EMAIL=team@example.org\nDATA_DIR='x'\n")
    cache.load_dotenv(env)
    assert "team@example.org" in cache.user_agent()
    assert cache.raw_dir() == tmp_path / "raw"   # DATA_DIR was already set (conftest): .env never overrides
