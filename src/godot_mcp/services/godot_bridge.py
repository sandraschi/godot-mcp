"""Godot WebSocket bridge client — connects to the GDScript TCPServer bridge in Godot 4.0+."""

import json
import logging
import os
import socket
from pathlib import Path
from typing import Any

logger = logging.getLogger("godot-mcp.bridge")

GODOT_HOST = os.getenv("GODOT_HOST", "127.0.0.1")
GODOT_PORT = int(os.getenv("GODOT_PORT", "9080"))
GODOT_PATH = os.getenv("GODOT_PATH", "")

_DEFAULT_TIMEOUT = 10.0


class GodotBridge:
    def __init__(self):
        self._sock: socket.socket | None = None
        self._connected = False
        self._godot_version: str | None = None
        self._request_seq = 0

    @property
    def connected(self) -> bool:
        return self._connected and self._sock is not None

    def connect(self) -> dict[str, Any]:
        if self._connected:
            return {"success": True, "message": "Already connected", "data": {"godot_version": self._godot_version}}

        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(_DEFAULT_TIMEOUT)
            self._sock.connect((GODOT_HOST, GODOT_PORT))

            handshake_raw = self._recv_json()
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
            return {
                "success": False,
                "error": f"Connection refused at {GODOT_HOST}:{GODOT_PORT}. Is Godot running with the MCP bridge addon?",
            }
        except TimeoutError:
            return {"success": False, "error": f"Connection timeout at {GODOT_HOST}:{GODOT_PORT}"}
        except OSError as e:
            return {"success": False, "error": f"Socket error: {e}"}

    def disconnect(self) -> dict[str, Any]:
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
        logger.info("Disconnected from Godot bridge")
        return {"success": True, "message": "Disconnected from Godot bridge"}

    def send(
        self, action: str, params: dict[str, Any] | None = None, timeout: float = _DEFAULT_TIMEOUT
    ) -> dict[str, Any]:
        if not self._connected or self._sock is None:
            return {"success": False, "error": "Not connected to Godot bridge. Call connect() first."}

        if params is None:
            params = {}

        self._request_seq += 1
        request_id = f"py_{self._request_seq}"

        try:
            self._sock.settimeout(timeout)
            self._sock.sendall(
                (json.dumps({"action": action, "params": params, "request_id": request_id}) + "\n").encode("utf-8")
            )

            response_raw = self._recv_json()
            if not response_raw:
                return {"success": False, "error": "No response from Godot bridge"}

            response = json.loads(response_raw)
            if response.get("type") != "response":
                return {"success": False, "error": f"Unexpected response type: {response.get('type')}"}

            if not response.get("success", False):
                return {"success": False, "error": response.get("error", "Unknown Godot bridge error")}

            return {"success": True, "data": response.get("data", {})}
        except TimeoutError:
            return {"success": False, "error": f"Request '{action}' timed out after {timeout}s"}
        except OSError as e:
            self._connected = False
            return {"success": False, "error": f"Connection lost: {e}"}

    def is_installed(self) -> bool:
        if GODOT_PATH:
            return Path(GODOT_PATH).is_file()
        import shutil

        return shutil.which("godot") is not None or shutil.which("godot.exe") is not None

    def _recv_json(self) -> str | None:
        """Read a newline-delimited JSON message from the TCP stream."""
        if self._sock is None:
            return None
        buffer = b""
        while b"\n" not in buffer:
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk
            except TimeoutError:
                if buffer:
                    break
                return None
            except OSError:
                return None

        newline_idx = buffer.find(b"\n")
        if newline_idx == -1:
            return buffer.decode("utf-8") if buffer else None
        return buffer[:newline_idx].decode("utf-8")


# Module-level singleton
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
