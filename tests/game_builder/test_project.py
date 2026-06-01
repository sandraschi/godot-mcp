"""Tests for scene materialization."""

from __future__ import annotations

from godot_mcp.game_builder.plan import GamePlan, SceneSpec, ScriptSpec
from godot_mcp.game_builder.project import materialize_scenes_from_plan, sync_project_from_plan


def test_materialize_scenes_from_plan(tmp_path):
    (tmp_path / "project.godot").write_text(
        '[application]\nconfig/name="T"\nrun/main_scene="res://main.tscn"\n',
        encoding="utf-8",
    )
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "game.gd").write_text("extends Node2D\n", encoding="utf-8")

    plan = GamePlan(
        title="T",
        scenes=[
            SceneSpec(name="Game", type="Node2D", scripts=["game.gd"]),
            SceneSpec(name="Player", type="CharacterBody2D", scripts=["player.gd"]),
        ],
        scripts=[ScriptSpec(name="game.gd", description="main")],
    )

    result = materialize_scenes_from_plan(tmp_path, plan)
    assert result["count"] == 2
    assert (tmp_path / "scenes" / "Game.tscn").is_file()
    assert 'run/main_scene="res://scenes/Game.tscn"' in (tmp_path / "project.godot").read_text(encoding="utf-8")


def test_sync_project_from_plan(tmp_path):
    plan = GamePlan(
        title="Sync",
        scenes=[SceneSpec(name="Game", type="Node2D", scripts=["game.gd"])],
        scripts=[ScriptSpec(name="game.gd", description="loop")],
    )
    logic = {"scripts": {"game.gd": {"generated": True, "code": "extends Node2D\nfunc _ready(): pass\n"}}}
    out = sync_project_from_plan(tmp_path, plan, logic)
    assert out["scripts"]["count"] == 1
    assert out["scenes"]["count"] == 1
