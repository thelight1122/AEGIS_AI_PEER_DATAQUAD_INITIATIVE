"""Base daemon framework for DataQuad retrieval operators.

Provides Unix domain socket IPC, JSONL ledger watching, and a run loop.
Zero external dependencies. Runs on Linux (Gabe) under aegis-verus.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import selectors
import threading
from pathlib import Path
from typing import Any, Callable


_MAX_MESSAGE_BYTES = 4_194_304


class DaemonSocket:
    """Unix domain socket server for inter-daemon communication."""

    def __init__(self, socket_path: Path, handler: Callable[[dict], dict]) -> None:
        self.socket_path = Path(socket_path)
        self._handler = handler
        self._server: socket.socket | None = None
        self._selector = selectors.DefaultSelector()
        self._transport = "unix" if hasattr(socket, "AF_UNIX") else "tcp-localhost"

    def start(self) -> None:
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        if self.socket_path.exists():
            self.socket_path.unlink()
        if self._transport == "unix":
            self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._server.bind(str(self.socket_path))
        else:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.bind(("127.0.0.1", 0))
            host, port = self._server.getsockname()
            self.socket_path.write_text(
                json.dumps(
                    {"host": host, "port": port, "transport": "tcp-localhost"},
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
        self._server.listen(8)
        self._server.setblocking(False)
        self._selector.register(self._server, selectors.EVENT_READ, self._accept)

    def _accept(self, server: socket.socket) -> None:
        conn, _ = server.accept()
        conn.setblocking(True)
        conn.settimeout(10.0)
        thread = threading.Thread(
            target=self._handle_connection, args=(conn,), daemon=True,
        )
        thread.start()

    def _handle_connection(self, conn: socket.socket) -> None:
        try:
            data = b""
            while len(data) < _MAX_MESSAGE_BYTES:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
                if b"\n" in data:
                    break
            if data:
                request = json.loads(data.decode("utf-8"))
                response = self._handler(request)
                wire = json.dumps(
                    response, sort_keys=True, separators=(",", ":"),
                    ensure_ascii=False, allow_nan=False,
                ).encode("utf-8") + b"\n"
                conn.sendall(wire)
        except Exception as exc:
            try:
                error_wire = json.dumps({"error": str(exc)[:512]}).encode("utf-8") + b"\n"
                conn.sendall(error_wire)
            except Exception:
                pass
        finally:
            conn.close()

    def poll(self, timeout: float = 1.0) -> None:
        events = self._selector.select(timeout=timeout)
        for key, _ in events:
            callback = key.data
            callback(key.fileobj)

    def stop(self) -> None:
        if self._server is not None:
            try:
                self._selector.unregister(self._server)
            except (KeyError, ValueError):
                pass
            self._server.close()
        self._selector.close()
        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
            except OSError:
                pass


class DaemonClient:
    """Client for querying a daemon via Unix domain socket."""

    def __init__(self, socket_path: str | Path, timeout: float = 10.0) -> None:
        self.socket_path = str(socket_path)
        self.timeout = timeout

    @property
    def available(self) -> bool:
        if not os.path.exists(self.socket_path):
            return False
        if hasattr(socket, "AF_UNIX"):
            return True
        try:
            return self._tcp_endpoint() is not None
        except (OSError, ValueError, json.JSONDecodeError):
            return False

    def query(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request = {"method": method, "params": params or {}}
        if hasattr(socket, "AF_UNIX"):
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            endpoint = self.socket_path
        else:
            endpoint = self._tcp_endpoint()
            if endpoint is None:
                raise OSError("daemon TCP endpoint marker is unavailable")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect(endpoint)
            wire = json.dumps(
                request, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False,
            ).encode("utf-8") + b"\n"
            sock.sendall(wire)
            data = b""
            while len(data) < _MAX_MESSAGE_BYTES:
                chunk = sock.recv(1_048_576)
                if not chunk:
                    break
                data += chunk
                if b"\n" in data:
                    break
            return json.loads(data.decode("utf-8"))
        finally:
            sock.close()

    def _tcp_endpoint(self) -> tuple[str, int] | None:
        marker = json.loads(Path(self.socket_path).read_text(encoding="utf-8"))
        if marker.get("transport") != "tcp-localhost":
            return None
        host = marker.get("host")
        port = marker.get("port")
        if host != "127.0.0.1" or not isinstance(port, int):
            return None
        return host, port


class LedgerWatcher:
    """Polls a JSONL ledger file for new appended records."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._last_size: int = 0
        self._line_count: int = 0

    def check(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            current_size = self.path.stat().st_size
        except OSError:
            return []
        if current_size == self._last_size:
            return []
        text = self.path.read_text(encoding="utf-8")
        lines = text.splitlines()
        new_lines = lines[self._line_count:]
        self._last_size = current_size
        self._line_count = len(lines)
        records: list[dict[str, Any]] = []
        for line in new_lines:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
        return records

    def load_all(self) -> list[dict[str, Any]]:
        """Load all records, resetting the watcher position."""
        if not self.path.exists():
            self._last_size = 0
            self._line_count = 0
            return []
        text = self.path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self._last_size = self.path.stat().st_size
        self._line_count = len(lines)
        records: list[dict[str, Any]] = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
        return records


class BaseDaemon:
    """Base class for DataQuad retrieval operator daemons."""

    def __init__(self, name: str, socket_path: str | Path) -> None:
        self.name = name
        self._socket = DaemonSocket(Path(socket_path), self._dispatch)
        self._running = False
        self._watchers: dict[str, LedgerWatcher] = {}

    def add_watcher(self, name: str, path: str | Path) -> None:
        self._watchers[name] = LedgerWatcher(Path(path))

    def _dispatch(self, request: dict[str, Any]) -> dict[str, Any]:
        method = request.get("method", "")
        params = request.get("params", {})
        handler = getattr(self, f"op_{method}", None)
        if handler is None:
            return {"error": f"unknown method: {method}"}
        try:
            result = handler(params)
            return {"result": result}
        except Exception as exc:
            return {"error": str(exc)[:512]}

    def op_health(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"daemon": self.name, "status": "ok", "running": self._running}

    def on_new_records(self, watcher_name: str, records: list[dict[str, Any]]) -> None:
        """Override to handle new records from a watched ledger."""

    def on_start(self) -> None:
        """Override for initialization after watchers load."""

    def run(self) -> None:
        self._socket.start()
        self._running = True

        def _shutdown(signum: int, frame: Any) -> None:
            self._running = False

        signal.signal(signal.SIGTERM, _shutdown)
        signal.signal(signal.SIGINT, _shutdown)

        for name, watcher in self._watchers.items():
            records = watcher.load_all()
            if records:
                self.on_new_records(name, records)

        self.on_start()

        while self._running:
            self._socket.poll(timeout=2.0)
            for name, watcher in self._watchers.items():
                new_records = watcher.check()
                if new_records:
                    self.on_new_records(name, new_records)

        self._socket.stop()

    def stop(self) -> None:
        self._running = False
