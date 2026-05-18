"""Tests for the GodotBridge service layer."""

from unittest.mock import patch

import pytest

from godot_mcp.services.godot_bridge import GodotBridge


@pytest.fixture
def bridge():
    return GodotBridge()


def test_initial_state(bridge):
    assert bridge.connected is False
    assert bridge._sock is None
    assert bridge._godot_version is None
    assert bridge._request_seq == 0


def test_disconnect_not_connected(bridge):
    result = bridge.disconnect()
    assert result["success"] is True
    assert result["message"] == "Not connected"


def test_connect_idempotent(bridge):
    result = bridge.disconnect()
    assert result["success"] is True


@patch("godot_mcp.services.godot_bridge.socket.socket")
def test_connect_refused(mock_socket, bridge):
    mock_socket.return_value.connect.side_effect = ConnectionRefusedError
    result = bridge.connect()
    assert result["success"] is False
    assert "Connection refused" in result["error"]


@patch("godot_mcp.services.godot_bridge.socket.socket")
def test_connect_timeout(mock_socket, bridge):
    mock_socket.return_value.connect.side_effect = TimeoutError
    result = bridge.connect()
    assert result["success"] is False
    assert "timeout" in result["error"].lower()


@patch("godot_mcp.services.godot_bridge.socket.socket")
def test_send_when_disconnected(mock_socket, bridge):
    result = bridge.send("status")
    assert result["success"] is False
    assert "Not connected" in result["error"]
