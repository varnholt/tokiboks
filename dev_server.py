#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
tokiboks dev server — mirrors the ESP32 config web server locally.

  uv run dev_server.py

Simulate an RFID scan while the page is open:
  http://localhost:8080/test-rfid?uid=ABCD1234
"""
from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "firmware", "data")
HOST, PORT = "localhost", 8080

DEFAULTS: dict[str, object] = {
    "credentials.json": {
        "wifi_ssid": "", "wifi_password": "",
        "admin_username": "admin", "admin_password": "admin",
    },
    "server.json": {"server_host": "192.168.0.92", "server_port": 8000},
    "mapping.json": {"entries": [{"rfid": "", "label": ""} for _ in range(100)]},
}

API_FILES = {
    "/api/credentials":   "credentials.json",
    "/api/server-config": "server.json",
    "/api/music-mapping": "mapping.json",
}

_last_rfid = ""


class Handler(BaseHTTPRequestHandler):

    def do_GET(self) -> None:
        global _last_rfid
        parsed = urlparse(self.path)
        path   = parsed.path
        query  = parse_qs(parsed.query)

        if path == "/test-rfid":
            uid = query.get("uid", [""])[0].strip().upper()
            if uid:
                _last_rfid = uid
                self._json(200, {"ok": True, "uid": uid})
            else:
                self._json(400, {"error": "uid required"})
            return

        if path == "/api/last-rfid":
            self._json(200, {"uid": _last_rfid})
            return

        if fname := API_FILES.get(path):
            self._api_get(fname)
            return

        self._static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/restart":
            self._json(200, {"ok": True})
            print("  [dev] restart requested — would reboot device here")
            return
        if fname := API_FILES.get(path):
            self._api_post(fname)
        else:
            self._json(405, {"error": "method not allowed"})

    def _api_get(self, fname: str) -> None:
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                body = f.read()
        else:
            body = json.dumps(DEFAULTS[fname]).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _api_post(self, fname: str) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        with open(os.path.join(DATA_DIR, fname), "wb") as f:
            f.write(body)
        self._json(200, {"ok": True})

    def _static(self, path: str) -> None:
        if path == "/":
            path = "/index.html"
        full = os.path.normpath(os.path.join(DATA_DIR, path.lstrip("/")))
        if not full.startswith(os.path.normpath(DATA_DIR)):
            self._json(403, {"error": "forbidden"})
            return
        if not os.path.isfile(full):
            self._json(404, {"error": "not found"})
            return
        mime, _ = mimetypes.guess_type(full)
        with open(full, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data: object) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"  {self.address_string()}  {fmt % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"tokiboks dev server  →  http://{HOST}:{PORT}/")
    print(f"simulate RFID scan:     http://{HOST}:{PORT}/test-rfid?uid=ABCD1234")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
