"""Godot project bootstrap and script persistence for game_builder."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from godot_mcp.game_builder.plan import GamePlan

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TEMPLATE = REPO_ROOT / "templates" / "game-template"

_GODOT_SCENE_TYPES = {
    "Node2D",
    "Node3D",
    "Control",
    "CanvasLayer",
    "CharacterBody2D",
    "RigidBody2D",
    "StaticBody2D",
    "Area2D",
    "Sprite2D",
    "Label",
    "Button",
}


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower()).strip("-")
    return slug or "game"


def ensure_project_path(title: str, game_project_path: str = "") -> Path:
    """Return an existing project dir or copy the minimal game template."""
    if game_project_path.strip():
        path = Path(game_project_path).resolve()
        if not (path / "project.godot").is_file():
            raise ValueError(f"Not a Godot project (missing project.godot): {path}")
        return path

    dest = REPO_ROOT / "build" / "game-builder" / _slugify(title)
    if (dest / "project.godot").is_file():
        return dest

    if not DEFAULT_TEMPLATE.is_dir():
        raise ValueError(
            f"game_project_path required — template missing at {DEFAULT_TEMPLATE}"
        )

    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(DEFAULT_TEMPLATE, dest)
    return dest


def strip_code_fences(code: str) -> str:
    text = code.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip() + "\n"


def write_scripts_to_project(project_path: str | Path, logic_result: dict[str, Any]) -> dict[str, Any]:
    """Write generated GDScript files into project scripts/."""
    root = Path(project_path).resolve()
    scripts_dir = root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    scripts = logic_result.get("scripts", {})
    written: list[str] = []
    errors: dict[str, str] = {}

    for filename, info in scripts.items():
        if not isinstance(info, dict) or not info.get("generated"):
            continue
        name = filename if filename.endswith(".gd") else f"{filename}.gd"
        try:
            code = strip_code_fences(str(info.get("code", "")))
            if not code.strip():
                errors[name] = "empty code"
                continue
            (scripts_dir / name).write_text(code, encoding="utf-8")
            written.append(str(scripts_dir / name))
        except OSError as exc:
            errors[name] = str(exc)

    return {"written": written, "errors": errors, "count": len(written)}


def copy_world_meshes_to_project(
    project_path: str | Path,
    world_results: dict[str, Any],
) -> dict[str, Any]:
    """Copy staged World Labs GLBs into project assets/worldlabs/."""
    root = Path(project_path).resolve()
    dest_dir = root / "assets" / "worldlabs"
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for _slug, entry in world_results.items():
        if not isinstance(entry, dict):
            continue
        mesh_path = entry.get("mesh_path")
        if not mesh_path:
            continue
        src = Path(str(mesh_path))
        if not src.is_file():
            continue
        marble_id = entry.get("marble_world_id") or entry.get("world_id") or src.stem
        dest = dest_dir / f"{str(marble_id)[:12]}_collider.glb"
        shutil.copy2(src, dest)
        entry["project_mesh_path"] = str(dest)
        copied.append(str(dest))

    return {"copied": copied, "count": len(copied)}


def _scene_tscn(scene_name: str, node_type: str, script_file: str | None) -> str:
    uid = re.sub(r"[^a-z0-9]", "", scene_name.lower()) or "scene"
    lines: list[str] = [f'[gd_scene load_steps={"2" if script_file else "1"} format=3 uid="uid://gb_{uid}"]']
    if script_file:
        lines.append(f'[ext_resource type="Script" path="res://scripts/{script_file}" id="1_script"]')
        lines.append("")
    lines.append(f'[node name="{scene_name}" type="{node_type}"]')
    if script_file:
        lines.append('script = ExtResource("1_script")')
    return "\n".join(lines) + "\n"


def materialize_scenes_from_plan(project_path: str | Path, plan: GamePlan) -> dict[str, Any]:
    """Create .tscn files from GamePlan and set run/main_scene on the Game node."""
    root = Path(project_path).resolve()
    scenes_dir = root / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    main_scene = "res://main.tscn"

    for spec in plan.scenes:
        node_type = spec.type if spec.type in _GODOT_SCENE_TYPES else "Node2D"
        script_file: str | None = None
        if spec.scripts:
            raw = spec.scripts[0]
            script_file = raw if raw.endswith(".gd") else f"{raw}.gd"
            script_path = root / "scripts" / script_file
            if not script_path.is_file():
                script_file = None

        fname = f"{spec.name}.tscn"
        out = scenes_dir / fname
        out.write_text(_scene_tscn(spec.name, node_type, script_file), encoding="utf-8")
        created.append(str(out))
        if spec.name == "Game":
            main_scene = f"res://scenes/{fname}"

    proj_file = root / "project.godot"
    if proj_file.is_file():
        text = proj_file.read_text(encoding="utf-8")
        if "run/main_scene=" in text:
            text = re.sub(r'run/main_scene="[^"]*"', f'run/main_scene="{main_scene}"', text)
        else:
            text += f'\nrun/main_scene="{main_scene}"\n'
        proj_file.write_text(text, encoding="utf-8")

    return {"scenes": created, "main_scene": main_scene, "count": len(created)}


def sync_project_from_plan(
    project_path: str | Path,
    plan: GamePlan,
    logic_result: dict[str, Any],
) -> dict[str, Any]:
    """Write scripts, materialize scenes, return combined summary."""
    scripts = write_scripts_to_project(project_path, logic_result)
    scenes = materialize_scenes_from_plan(project_path, plan)
    return {"scripts": scripts, "scenes": scenes}
