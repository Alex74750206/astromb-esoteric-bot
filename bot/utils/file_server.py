"""Минимальный HTTP-сервер для скачивания Клиенты.xlsx с сервера."""
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

log = logging.getLogger(__name__)


def _make_handler(excel_path: str, token: str):
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path != "/clients":
                self._reply(404, b"Not found")
                return
            params = parse_qs(parsed.query)
            if params.get("token", [""])[0] != token:
                self._reply(403, b"Forbidden")
                return
            if not os.path.exists(excel_path):
                self._reply(404, b"File not ready yet")
                return
            with open(excel_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            self.send_header(
                "Content-Disposition",
                'attachment; filename="Klienty.xlsx"',
            )
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _reply(self, code: int, body: bytes):
            self.send_response(code)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):  # подавляем стандартный лог
            pass

    return _Handler


def start_file_server(excel_path: str, port: int, token: str) -> HTTPServer:
    handler = _make_handler(excel_path, token)
    server = HTTPServer(("0.0.0.0", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log.info("Файл-сервер запущен: порт %d  →  GET /clients?token=***", port)
    return server
