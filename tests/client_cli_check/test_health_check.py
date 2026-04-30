from __future__ import annotations

import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from kinnoo.health_check import run_service_health_check


def test_feature25_http_health_check_2xx_and_timeout() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/ok":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")
                return
            if self.path == "/fail":
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b"down")
                return
            if self.path == "/slow":
                time.sleep(0.2)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"slow")
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            del format, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        ok_result = run_service_health_check(
            {
                "name": "local-api",
                "type": "api",
                "health_check": {
                    "method": "http",
                    "url": f"http://{host}:{port}/ok",
                },
            }
        )
        assert ok_result.healthy is True
        assert "status 200" in ok_result.message
        assert "timeout 5s" in ok_result.message

        fail_result = run_service_health_check(
            {
                "name": "local-api",
                "type": "api",
                "health_check": {
                    "method": "http",
                    "url": f"http://{host}:{port}/fail",
                },
            }
        )
        assert fail_result.healthy is False
        assert "status 503" in fail_result.message

        timeout_result = run_service_health_check(
            {
                "name": "local-api",
                "type": "api",
                "health_check": {
                    "method": "http",
                    "url": f"http://{host}:{port}/slow",
                    "timeout_seconds": 0.05,
                },
            }
        )
        assert timeout_result.healthy is False
        assert "0.05s" in timeout_result.message

        override_result = run_service_health_check(
            {
                "name": "local-api",
                "type": "api",
                "health_check": {
                    "method": "http",
                    "url": f"http://{host}:{port}/slow",
                    "timeout_seconds": 0.5,
                },
            }
        )
        assert override_result.healthy is True
        assert "timeout 0.5s" in override_result.message
    finally:
        server.shutdown()
        server.server_close()


def test_feature25_tcp_health_check_localhost_and_timeout() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 0))
    server_socket.listen(1)
    open_port = server_socket.getsockname()[1]

    stop_accept = threading.Event()

    def accept_loop() -> None:
        while not stop_accept.is_set():
            try:
                server_socket.settimeout(0.1)
                conn, _ = server_socket.accept()
                conn.close()
            except TimeoutError:
                continue
            except OSError:
                break

    thread = threading.Thread(target=accept_loop, daemon=True)
    thread.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe_socket:
        probe_socket.bind(("127.0.0.1", 0))
        closed_port = probe_socket.getsockname()[1]

    try:
        open_result = run_service_health_check(
            {
                "name": "postgres",
                "type": "database",
                "health_check": {
                    "method": "tcp",
                    "port": open_port,
                    "timeout_seconds": 0.4,
                },
            }
        )
        assert open_result.healthy is True
        assert f"127.0.0.1:{open_port}" in open_result.message
        assert "timeout 0.4s" in open_result.message

        closed_result = run_service_health_check(
            {
                "name": "postgres",
                "type": "database",
                "health_check": {
                    "method": "tcp",
                    "port": closed_port,
                    "timeout_seconds": 0.05,
                },
            }
        )
        assert closed_result.healthy is False
        assert f"127.0.0.1:{closed_port}" in closed_result.message
        assert "timeout 0.05s" in closed_result.message
    finally:
        stop_accept.set()
        server_socket.close()


def test_feature25_process_health_check() -> None:
    process_token = "feature25-process-fixture"
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(20)",
            process_token,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        time.sleep(0.2)
        running_result = run_service_health_check(
            {
                "name": "redis",
                "type": "local-process",
                "health_check": {
                    "method": "process",
                    "process_name": process_token,
                },
            }
        )
        assert running_result.healthy is True
        assert process_token in running_result.message

        missing_result = run_service_health_check(
            {
                "name": "redis",
                "type": "local-process",
                "health_check": {
                    "method": "process",
                    "process_name": "definitely-missing-feature25-process",
                },
            }
        )
        assert missing_result.healthy is False
        assert "Start the required process" in missing_result.guidance
    finally:
        process.terminate()
        process.wait(timeout=5)
