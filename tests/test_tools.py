"""Tests for the Godot MCP tool registration and signatures."""

from godot_mcp.tools.core_tools import register


def test_register_accepts_mcp():
    class FakeMCP:
        def __init__(self):
            self.registered = []

        def tool(self, **kwargs):
            def wrapper(fn):
                self.registered.append((fn.__name__, kwargs))
                return fn

            return wrapper

    mcp = FakeMCP()
    register(mcp)
    names = [name for name, _ in mcp.registered]
    assert "godot_status" in names
    assert "godot_import_stl" in names
    assert "godot_load_velocity_field" in names
    assert "godot_spawn_particles" in names
    assert "godot_animate_streamlines" in names
    assert "godot_create_camera" in names
    assert "godot_add_light" in names
    assert "godot_set_material" in names
    assert "godot_export_web" in names
    assert "godot_read_scene_tree" in names
    assert "godot_set_config" in names
    assert "godot_headless_verify" in names
    assert "godot_import_glb" in names
    assert "godot_play_animation" in names
    assert "start_bridge" in names
    assert "godot_capture_viewport" in names
    assert "godot_simulate_input" in names
    assert "godot_scene" in names
    assert "godot_generate_procedural_texture" in names
    assert len(mcp.registered) >= 29  # growing as tools are added
