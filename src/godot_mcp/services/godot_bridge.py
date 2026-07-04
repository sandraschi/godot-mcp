"""Godot TCP bridge client — connects to the GDScript TCPServer bridge in Godot 4.x.

Protocol: newline-delimited JSON over a plain TCP socket (not WebSocket).
Requests carry a ``request_id``; responses are correlated against it so that
concurrent callers (e.g. the mobile status pusher and a tool call) can never
consume each other's replies.

Thread-safety: a single socket is shared behind a ``threading.Lock`` — one
request/response exchange in flight at a time. Callers on the asyncio side
should wrap ``connect``/``send`` in ``asyncio.to_thread`` (blocking I/O).

Configuration resolution order: environment variables (GODOT_HOST, GODOT_PORT,
GODOT_PATH) first, then ``~/.godot-mcp/settings.json`` (written by the
``PUT /api/v1/settings`` endpoint), then defaults.
"""

import json
import logging
import os
import socket
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger("godot-mcp.bridge")

_DEFAULT_TIMEOUT = 10.0
_SETTINGS_PATH = Path.home() / ".godot-mcp" / "settings.json"


def _load_settings_file() -> dict[str, Any]:
    if _SETTINGS_PATH.is_file():
        try:
            return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def resolve_config() -> dict[str, Any]:
    """Resolve bridge config: env > settings.json > defaults."""
    settings = _load_settings_file()
    host = os.getenv("GODOT_HOST") or settings.get("godot_host") or "127.0.0.1"
    try:
        port = int(os.getenv("GODOT_PORT") or settings.get("godot_ws_port") or 9080)
    except (TypeError, ValueError):
        port = 9080
    path = os.getenv("GODOT_PATH") or settings.get("godot_path") or ""
    return {"host": host, "port": port, "godot_path": path}


_initial = resolve_config()
# Backwards-compatible module constants (initial resolution; connect() re-resolves live).
GODOT_HOST = _initial["host"]
GODOT_PORT = _initial["port"]
GODOT_PATH = _initial["godot_path"]


class GodotBridge:
    def __init__(self):
        self._sock = None
        self._connected = False
        self._godot_version: str | None = None
        self._request_seq = 0
        self._recv_buffer = b""
        self._lock = threading.Lock()
        self._host = GODOT_HOST
        self._port = GODOT_PORT

    @property
    def connected(self) -> bool:
        return self._connected and self._sock is not None

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    def connect(self) -> dict[str, Any]:
        with self._lock:
            if self._connected:
                return {
                    "success": True,
                    "message": "Already connected",
                    "data": {"godot_version": self._godot_version},
                }

            cfg = resolve_config()
            self._host, self._port = cfg["host"], cfg["port"]

            try:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.settimeout(_DEFAULT_TIMEOUT)
                self._sock.connect((self._host, self._port))
                self._recv_buffer = b""

                handshake_raw = self._recv_line()
                if not handshake_raw:
                    self._sock.close()
                    self._sock = None
                    return {"success": False, "error": "No handshake received from Godot bridge"}

                handshake = json.loads(handshake_raw)
                if handshake.get("type") != "handshake":
                    logger.warning("Unexpected handshake type: %s", handshake.get("type"))

                self._connected = True
                self._godot_version = handshake.get("godot_version", "unknown")
                logger.info("Connected to Godot bridge. Version: %s", self._godot_version)

                return {
                    "success": True,
                    "message": f"Connected to Godot bridge v{handshake.get('version', '?')}",
                    "data": {
                        "version": handshake.get("version"),
                        "godot_version": handshake.get("godot_version"),
                        "ready": handshake.get("ready", False),
                    },
                }
            except ConnectionRefusedError:
                self._sock = None
                return {
                    "success": False,
                    "error": f"Connection refused at {self._host}:{self._port}. Is Godot running with the MCP bridge addon?",
                }
            except TimeoutError:
                self._sock = None
                return {"success": False, "error": f"Connection timeout at {self._host}:{self._port}"}
            except OSError as e:
                self._sock = None
                return {"success": False, "error": f"Socket error: {e}"}

    def disconnect(self) -> dict[str, Any]:
        with self._lock:
            if not self._connected:
                return {"success": True, "message": "Not connected"}
            try:
                if self._sock:
                    self._sock.close()
            except OSError:
                pass
            finally:
                self._sock = None
                self._connected = False
                self._godot_version = None
                self._recv_buffer = b""
            logger.info("Disconnected from Godot bridge")
            return {"success": True, "message": "Disconnected from Godot bridge"}

    def send(
        self, action: str, params: dict[str, Any] | None = None, timeout: float = _DEFAULT_TIMEOUT
    ) -> dict[str, Any]:
        """Send one request and return its correlated response.

        Holds the bridge lock for the full exchange — only one request is in
        flight at a time. Responses whose request_id does not match are drained
        (logged and skipped) so a stale reply can never be returned to the
        wrong caller.
        """
        if params is None:
            params = {}

        with self._lock:
            if not self._connected or self._sock is None:
                return {"success": False, "error": "Not connected to Godot bridge. Call connect() first."}

            self._request_seq += 1
            request_id = f"py_{self._request_seq}"

            try:
                self._sock.settimeout(timeout)
                self._sock.sendall(
                    (json.dumps({"action": action, "params": params, "request_id": request_id}) + "\n").encode("utf-8")
                )

                # Read lines until the matching response (drain pushes/stale replies).
                for _ in range(50):
                    response_raw = self._recv_line()
                    if not response_raw:
                        return {"success": False, "error": "No response from Godot bridge"}

                    response = json.loads(response_raw)
                    if response.get("type") != "response":
                        logger.debug("Skipping non-response message type=%s", response.get("type"))
                        continue
                    resp_id = response.get("request_id")
                    if resp_id and resp_id != request_id:
                        logger.warning("Draining stale bridge reply %s (waiting for %s)", resp_id, request_id)
                        continue

                    if not response.get("success", False):
                        return {"success": False, "error": response.get("error", "Unknown Godot bridge error")}
                    return {"success": True, "data": response.get("data", {})}

                return {"success": False, "error": "Bridge response correlation exhausted (50 messages drained)"}
            except TimeoutError:
                return {"success": False, "error": f"Request '{action}' timed out after {timeout}s"}
            except OSError as e:
                self._connected = False
                return {"success": False, "error": f"Connection lost: {e}"}

    def is_installed(self) -> bool:
        cfg = resolve_config()
        if cfg["godot_path"]:
            return Path(cfg["godot_path"]).is_file()
        import shutil

        return shutil.which("godot") is not None or shutil.which("godot.exe") is not None

    def _recv_line(self) -> str | None:
        """Read one newline-delimited JSON message, retaining leftover bytes.

        Bytes after the first newline stay in ``self._recv_buffer`` for the
        next read (the previous implementation discarded them, losing any
        pipelined message).
        """
        if self._sock is None:
            return None
        while b"\n" not in self._recv_buffer:
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                self._recv_buffer += chunk
            except TimeoutError:
                if self._recv_buffer:
                    break
                return None
            except OSError:
                return None

        newline_idx = self._recv_buffer.find(b"\n")
        if newline_idx == -1:
            line, self._recv_buffer = self._recv_buffer, b""
            return line.decode("utf-8") if line else None
        line = self._recv_buffer[:newline_idx]
        self._recv_buffer = self._recv_buffer[newline_idx + 1 :]
        return line.decode("utf-8")


# Module-level singleton — the ONE bridge instance for the whole process.
_bridge = GodotBridge()


def get_bridge() -> GodotBridge:
    return _bridge


def connect() -> dict[str, Any]:
    return _bridge.connect()


def disconnect() -> dict[str, Any]:
    return _bridge.disconnect()


def send(action: str, params: dict[str, Any] | None = None, timeout: float = _DEFAULT_TIMEOUT) -> dict[str, Any]:
    return _bridge.send(action, params, timeout)


def is_installed() -> bool:
    return _bridge.is_installed()
