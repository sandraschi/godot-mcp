"""REST service layer for game_builder pipeline."""

from __future__ import annotations

import json
from typing import Any

from godot_mcp.game_builder import pipeline
from godot_mcp.game_builder.plan import GamePlan


def _parse_plan(raw: str | dict) -> GamePlan:
    data = json.loads(raw) if isinstance(raw, str) else raw
    return GamePlan.model_validate(data)


async def service_design_game(game_concept: str) -> dict[str, Any]:
    try:
        plan = await pipeline.design_game(game_concept, ctx=None)
        return {
            "success": True,
            "plan": json.loads(plan.to_json()),
            "summary": f"{plan.title} — {len(plan.worlds)} worlds",
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def service_generate_worlds(game_plan_json: str, worldlabs_url: str = "http://127.0.0.1:10865") -> dict[str, Any]:
    try:
        plan = _parse_plan(game_plan_json)
        result = await pipeline.generate_game_worlds(plan, worldlabs_url, stage_meshes=True)
        return {"success": True, **result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def service_compose_scene(
    game_plan_json: str,
    worlds_result_json: str = "",
) -> dict[str, Any]:
    try:
        plan = _parse_plan(game_plan_json)
        world_map: dict[str, Any] = {}
        if worlds_result_json.strip():
            parsed = json.loads(worlds_result_json)
            world_map = parsed.get("worlds", parsed) if isinstance(parsed, dict) else {}
        result = await pipeline.compose_game_scene(plan, world_map, import_to_godot=True)
        return {"success": True, **result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def service_generate_logic(game_plan_json: str, game_project_path: str = "") -> dict[str, Any]:
    try:
        plan = _parse_plan(game_plan_json)
        result = await pipeline.generate_game_logic(plan, ctx=None)
        payload: dict[str, Any] = {"success": True, **result}
        if game_project_path.strip():
            from godot_mcp.game_builder.project import materialize_scenes_from_plan, write_scripts_to_project

            payload["project_scripts"] = write_scripts_to_project(game_project_path, result)
            payload["project_scenes"] = materialize_scenes_from_plan(game_project_path, plan)
        return payload
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def service_export_and_ship(
    game_plan_json: str,
    game_project_path: str,
    itch_target: str = "",
    channel: str = "html",
) -> dict[str, Any]:
    try:
        plan = _parse_plan(game_plan_json)
        return await pipeline.export_and_ship(plan, game_project_path, itch_target, channel)
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def service_build_game(
    game_concept: str,
    worldlabs_url: str = "http://127.0.0.1:10865",
    game_project_path: str = "",
    ship: bool = False,
    itch_target: str = "",
) -> dict[str, Any]:
    return await pipeline.build_game(
        game_concept,
        ctx=None,
        worldlabs_url=worldlabs_url,
        game_project_path=game_project_path,
        ship=ship,
        itch_target=itch_target,
    )
