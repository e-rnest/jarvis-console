"""Console JSON API and allowlisted static-file server."""

from __future__ import annotations

import json
import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from . import __version__
from .config import Config
from .status import aggregate

LOG = logging.getLogger(__name__)
WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/assets/app.css": ("app.css", "text/css; charset=utf-8"),
    "/assets/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class ConsoleServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], config: Config,
                 web_root: Path = WEB_ROOT):
        super().__init__(address, ConsoleHandler)
        self.config = config
        self.web_root = web_root


class ConsoleHandler(BaseHTTPRequestHandler):
    server: ConsoleServer

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            LOG.info("client_disconnected path=%s", self.path)

    def _json(self, status: HTTPStatus, payload: dict) -> None:
        self._send(status, json.dumps(payload).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _static(self, path: str) -> None:
        filename, content_type = STATIC_FILES[path]
        try:
            body = (self.server.web_root / filename).read_bytes()
        except OSError:
            LOG.exception("static_asset_unavailable path=%s", path)
            self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Asset unavailable"})
            return
        self._send(HTTPStatus.OK, body, content_type)

    def do_GET(self) -> None:
        url = urlsplit(self.path)
        if url.query:
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
        elif url.path in STATIC_FILES:
            self._static(url.path)
        elif url.path == "/health":
            self._json(HTTPStatus.OK, {
                "status": "ok", "service": "jarvis-console", "version": __version__,
            })
        elif url.path == "/api/status":
            self._json(HTTPStatus.OK, aggregate(self.server.config))
        else:
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def log_message(self, format: str, *args: object) -> None:
        LOG.info("http client=%s %s", self.client_address[0], format % args)


def make_server(config: Config, host: str | None = None, port: int | None = None,
                web_root: Path = WEB_ROOT) -> ConsoleServer:
    return ConsoleServer((host or config.host, config.port if port is None else port),
                         config, web_root)
