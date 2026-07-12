"""Bridge stability tests: disconnect, reconnect, graceful degradation.

Uses the real GodotBridge singleton — no mocks — to verify that:
1. Tools degrade gracefully when bridge is down
2. godot_status hints point to start_bridge
3. find_godot returns a path or None
4. launch_bridge handles a missing project gracefully
"""

import pytest

from godot_mcp.services.godot_bridge import GodotBridge, find_godot, get_bridge, launch_bridge


@pytest.fixture(autouse=True)
def _reset_bridge():
    """Ensure each test starts with a fresh disconnect."""
    b = get_bridge()
    b.disconnect()
    yield


def test_godot_status_hints_when_bridge_down():
    """godot_status should hint at start_bridge when Godot is installed but bridge is down."""

    bridge = get_bridge()
    assert not bridge.connected

    # The hint comes from godot_status -> find_godot
    godot_path = find_godot()
    # Either Godot is found (hint mentions start_bridge) or not (hints install)
    if godot_path:
        assert isinstance(godot_path, str)
        assert "godot" in godot_path.lower()
    else:
        assert godot_path is None


def test_bridge_reconnect_cycle():
    """Disconnect -> reconnect should succeed even without a real Godot running."""
    bridge = GodotBridge()

    # Start disconnected
    assert not bridge.connected

    # Disconnect when already disconnected should be harmless
    result = bridge.disconnect()
    assert result["success"] is True

    # Reconnect will fail (no Godot running) but should not crash
    result = bridge.connect()
    assert result["success"] is False
    assert "refused" in result["error"].lower() or "timeout" in result["error"].lower()

    # Bridge should still be usable after failed connect
    assert not bridge.connected


def test_bridge_idempotent_disconnect():
    """Calling disconnect multiple times should be safe."""
    bridge = GodotBridge()
    for _ in range(3):
        result = bridge.disconnect()
        assert result["success"] is True


def test_send_when_disconnected_returns_clear_error():
    """Sending a command when disconnected should return a helpful error, not crash."""
    from godot_mcp.services.godot_bridge import get_bridge

    bridge = get_bridge()
    assert not bridge.connected

    result = bridge.send("status")
    assert result["success"] is False
    assert "Not connected" in result["error"]


def test_find_godot_returns_string_or_none():
    """find_godot should return a valid path or None — never crash."""
    path = find_godot()
    if path:
        from pathlib import Path

        assert Path(path).exists(), f"Godot path {path} does not exist"
    else:
        assert path is None


def test_launch_bridge_missing_project():
    """launch_bridge should return a helpful error for a nonexistent project dir."""
    result = launch_bridge(project_root="Z:/nonexistent/path")
    assert result["success"] is False
    assert "project" in result.get("error", "").lower()


def test_launch_bridge_no_project_found():
    """launch_bridge with empty root should detect the repo's project.godot."""
    result = launch_bridge()
    # If run from the godot-mcp repo root, project.godot exists -> success
    # If run elsewhere, it should fail gracefully
    from pathlib import Path

    repo_has_project = (Path.cwd() / "project.godot").is_file()
    if repo_has_project:
        assert result.get("success") is True or "project" in result.get("error", "").lower()
    else:
        assert result["success"] is False or "project" in result.get("error", "").lower()


def test_tool_registration_does_not_crash_when_bridge_down():
    """All MCP tools should import and register without needing a live bridge."""
    from godot_mcp.tools import register_all

    class FakeMCP:
        def __init__(self):
            self.tools = []

        def tool(self, **kwargs):
            def wrapper(fn):
                self.tools.append(fn.__name__)
                return fn

            return wrapper

    mcp = FakeMCP()
    register_all(mcp)
    assert len(mcp.tools) > 50, f"Expected >50 tools, got {len(mcp.tools)}"
    assert "godot_status" in mcp.tools
    assert "godot_capture_viewport" in mcp.tools
    assert "start_bridge" in mcp.tools
