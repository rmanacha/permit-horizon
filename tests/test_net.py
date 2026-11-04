"""The standard-library HTTP helper (hre.data.net) against a real local server."""

import http.server
import json
import threading
import urllib.parse

import pytest

from hre.data import net


class Handler(http.server.BaseHTTPRequestHandler):
    hits: dict[str, int] = {}  # noqa: RUF012 (reset by the fixture)

    def log_message(self, *args):  # quiet
        pass

    def do_GET(self):
        path, _, query = self.path.partition("?")
        Handler.hits[path] = Handler.hits.get(path, 0) + 1
        if path == "/flaky" and Handler.hits[path] == 1:
            self.send_response(503)
            self.end_headers()
            return
        if path == "/missing":
            self.send_response(404)
            self.end_headers()
            return
        if path == "/json":
            body = json.dumps({"q": urllib.parse.parse_qs(query), "ua": self.headers.get("User-Agent")}).encode()
        elif path == "/big":
            body = b"x" * (3 * net.CHUNK + 17)
        else:
            body = b"ok"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def server():
    Handler.hits = {}
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown()


def test_a_503_is_retried_then_succeeds(server):
    out = net.with_retries(lambda: net.get_bytes(f"{server}/flaky"), retries=2, pause=lambda a: 0)
    assert out == b"ok" and Handler.hits["/flaky"] == 2


def test_a_404_is_raised_at_once(server):
    with pytest.raises(net.HTTPError) as e:
        net.with_retries(lambda: net.get_bytes(f"{server}/missing"), retries=3, pause=lambda a: 0)
    assert e.value.status == 404 and Handler.hits["/missing"] == 1


def test_json_with_params_and_headers(server):
    d = net.get_json(f"{server}/json", params={"where": "a = 'b'", "f": "json"}, headers={"User-Agent": "ph-test"})
    assert d == {"q": {"where": ["a = 'b'"], "f": ["json"]}, "ua": "ph-test"}


def test_download_streams_every_chunk(server, tmp_path):
    dest = tmp_path / "big.bin"
    net.download(f"{server}/big", dest)
    assert dest.stat().st_size == 3 * net.CHUNK + 17


def test_a_refused_connection_is_transient_and_gives_up():
    calls = []

    def call():
        calls.append(1)
        return net.get_bytes("http://127.0.0.1:9/", timeout=2)

    with pytest.raises(net.TRANSIENT):
        net.with_retries(call, retries=1, pause=lambda a: 0)
    assert len(calls) == 2


def test_build_url_keeps_an_existing_query():
    assert net.build_url("https://x/q?a=1", {"b": "2 3"}) == "https://x/q?a=1&b=2+3"
    assert net.build_url("https://x/q", None) == "https://x/q"


def test_ssl_context_falls_back_to_a_system_bundle(monkeypatch, tmp_path):
    import ssl
    from pathlib import Path

    system = next((b for b in net.SYSTEM_BUNDLES if Path(b).is_file()), None)
    if system is None:
        pytest.skip("no system certificate bundle on this machine")
    bundle = tmp_path / "bundle.pem"
    bundle.write_bytes(Path(system).read_bytes())
    monkeypatch.setattr(net, "SYSTEM_BUNDLES", ("/nonexistent.pem", str(bundle)))
    monkeypatch.setattr(ssl, "create_default_context", lambda: ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT))
    net.ssl_context.cache_clear()
    try:
        assert net.ssl_context().cert_store_stats()["x509_ca"] > 0
    finally:
        net.ssl_context.cache_clear()
