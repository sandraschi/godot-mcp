"""Tests for game_builder world parsing and fleet staging helpers."""

from __future__ import annotations

from unittest.mock import patch

from godot_mcp.game_builder import project as project_helpers
from godot_mcp.game_builder import worlds


def test_extract_marble_world_id_from_operation_response():
    op = {"done": True, "response": {"world": {"id": "marble-uuid-12345", "assets": {}}}}
    assert worlds.extract_marble_world_id(op) == "marble-uuid-12345"


def test_extract_operation_id_from_name_field():
    assert worlds.extract_operation_id({"name": "operations/op-abc"}) == "op-abc"


def test_operation_is_done():
    assert worlds.operation_is_done({"done": True})
    assert worlds.operation_is_done({"status": "completed"})


def test_enrich_world_result_stages_mesh(monkeypatch, tmp_path):
    monkeypatch.setenv("FLEET_EXCHANGE_ROOT", str(tmp_path))
    entry = {"status": "completed", "marble_world_id": "abcdefghijklmnop"}

    with patch("godot_mcp.game_builder.worlds.fleet_pipeline.stage_worldlabs_mesh") as mock_stage:
        mock_stage.return_value = {
            "success": True,
            "mesh_path": str(tmp_path / "mesh.glb"),
            "spark_viewer_url": "http://127.0.0.1:10864/spark?splat_full=x",
        }
        out = worlds.enrich_world_result(entry, stage_mesh=True)

    assert out["mesh_path"].endswith("mesh.glb")
    assert out["staged"] is True
    mock_stage.assert_called_once_with("abcdefghijklmnop")


def test_marble_id_for_plan_slug():
    world_map = {"level_bg": {"marble_world_id": "uuid-1", "mesh_path": "/x.glb"}}
    assert worlds.marble_id_for_plan_slug(world_map, "level_bg") == "uuid-1"


def test_strip_code_fences():
    raw = "```gdscript\nextends Node2D\nfunc _ready(): pass\n```"
    assert "extends Node2D" in project_helpers.strip_code_fences(raw)
    assert "```" not in project_helpers.strip_code_fences(raw)


def test_write_scripts_to_project(tmp_path):
    logic = {
        "scripts": {
            "player.gd": {"generated": True, "code": "extends CharacterBody2D\n"},
            "bad.gd": {"generated": False},
        }
    }
    result = project_helpers.write_scripts_to_project(tmp_path, logic)
    assert result["count"] == 1
    assert (tmp_path / "scripts" / "player.gd").is_file()


def test_copy_world_meshes_to_project(tmp_path):
    src = tmp_path / "exchange" / "mesh.glb"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"glb")
    world_map = {
        "bg": {
            "marble_world_id": "abcdefghijklmnop",
            "mesh_path": str(src),
        }
    }
    project = tmp_path / "game"
    project.mkdir()
    result = project_helpers.copy_world_meshes_to_project(project, world_map)
    assert result["count"] == 1
    assert (project / "assets" / "worldlabs" / "abcdefghijkl_collider.glb").is_file()
