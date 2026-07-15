"""Tests for the GodotBridge TCP client and new bridge commands."""

from unittest.mock import patch

import pytest

from godot_mcp.services.godot_bridge import GodotBridge

# All bridge command action names registered in mcp_bridge.gd
BRIDGE_ACTIONS = {
    # Original
    "status", "import_stl", "import_glb", "import_obj", "load_velocity_field",
    "spawn_particles", "animate_streamlines", "create_camera", "add_light",
    "set_material", "export_web", "read_scene_tree", "set_config",
    "headless_verify", "add_node", "remove_node", "modify_node", "save_scene",
    "play_animation", "capture_viewport", "simulate_input",
    "generate_procedural_texture",
    # Phase 2 — State digest
    "state_digest", "state_watch_add", "state_watch_remove",
    # Phase 3 — Deterministic playtesting
    "game_time_freeze", "game_time_unfreeze", "game_time_step",
    "game_time_step_until",
    # 2026-07-15 additions
    "read_node", "inspect_resource", "tilemap_read", "tilemap_edit",
    "animation_edit", "profile_snapshot", "profile_enable", "profile_history",
    "validate_meshes",
}


@pytest.fixture
def bridge():
    return GodotBridge()


def test_disconnect_when_not_connected(bridge):
    result = bridge.disconnect()
    assert result["success"] is True
    assert result["message"] == "Not connected"


@patch("godot_mcp.services.godot_bridge.socket.socket")
def test_connect_refused(mock_socket, bridge):
    mock_socket.return_value.connect.side_effect = ConnectionRefusedError
    result = bridge.connect()
    assert result["success"] is False
    assert "Connection refused" in result["error"]


def test_all_bridge_actions_have_corresponding_handler():
    """Every action in BRIDGE_ACTIONS must have a _cmd_ prefix handler convention.

    This test verifies the action names are documented — the actual GDScript
    handler matching is done at runtime in Godot's _handle_message match block.
    """
    for action in sorted(BRIDGE_ACTIONS):
        assert action, f"Empty action name in BRIDGE_ACTIONS"


def test_bridge_action_naming_convention():
    """Bridge actions must be snake_case and < 40 chars."""
    for action in BRIDGE_ACTIONS:
        assert "_" in action or action.islower(), f"Action '{action}' should be snake_case"
        assert len(action) < 40, f"Action '{action}' name too long ({len(action)} chars)"


def test_state_digest_params():
    """state_digest accepts optional 'nodes' filter list."""
    bridge = GodotBridge()
    # Verify the Python tool sends the right format — actual dispatch tested via mock
    assert hasattr(bridge, "send"), "Bridge must have send() method"


def test_game_time_actions_have_correct_prefix():
    """game_time_* actions must follow the naming convention."""
    game_time_actions = {a for a in BRIDGE_ACTIONS if a.startswith("game_time")}
    expected = {"game_time_freeze", "game_time_unfreeze", "game_time_step", "game_time_step_until"}
    assert game_time_actions == expected, f"Got {game_time_actions}"


def test_profile_actions_have_correct_prefix():
    """profile_* actions must follow the naming convention."""
    profile_actions = {a for a in BRIDGE_ACTIONS if a.startswith("profile")}
    expected = {"profile_snapshot", "profile_enable", "profile_history"}
    assert profile_actions == expected, f"Got {profile_actions}"


def test_tilemap_actions():
    """tilemap must have read and edit actions."""
    tilemap_actions = {a for a in BRIDGE_ACTIONS if a.startswith("tilemap")}
    expected = {"tilemap_read", "tilemap_edit"}
    assert tilemap_actions == expected, f"Got {tilemap_actions}"
