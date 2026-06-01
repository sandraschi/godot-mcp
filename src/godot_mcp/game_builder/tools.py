"""MCP tools for the Game Builder pipeline — design, generate, compose, ship."""

from __future__ import annotations

import json
from typing import Annotated

from fastmcp import Context
from pydantic import Field

from godot_mcp.game_builder import pipeline
from godot_mcp.game_builder.plan import GamePlan

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


async def design_game(
    game_concept: Annotated[str, Field(description="Natural language description of the game to build.")],
    ctx: Context = None,
) -> dict:
    """Design a game from a natural-language concept using AI."""
    try:
        plan = await pipeline.design_game(game_concept, ctx)
        return {
            "success": True,
            "plan": json.loads(plan.to_json()),
            "summary": (
                f"Game: {plan.title} — {plan.genre or 'arcade'}. "
                f"{len(plan.worlds)} worlds, {len(plan.scenes)} scenes, {len(plan.scripts)} scripts."
            ),
        }
    except Exception as exc:
        return {"success": False, "error": str(exc), "recovery": "Check the game concept is descriptive enough."}


async def generate_game_worlds(
    game_plan_json: Annotated[str, Field(description="JSON game plan from design_game.")],
    worldlabs_url: Annotated[str, Field(description="worldlabs-mcp bridge URL.")] = "http://127.0.0.1:10865",
) -> dict:
    """Generate Marble worlds and stage collider GLBs to fleet exchange."""
    try:
        data = json.loads(game_plan_json) if isinstance(game_plan_json, str) else game_plan_json
        plan = GamePlan.model_validate(data)
        result = await pipeline.generate_game_worlds(plan, worldlabs_url, stage_meshes=True)
        return {"success": True, **result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def compose_game_scene(
    game_plan_json: Annotated[str, Field(description="JSON game plan from design_game.")],
    worlds_result_json: Annotated[
        str,
        Field(
            default="",
            description="Optional JSON from generate_game_worlds (uses marble_world_id + mesh_path).",
        ),
    ] = "",
) -> dict:
    """Assemble the Godot scene — imports staged Marble GLBs via fleet + bridge."""
    try:
        data = json.loads(game_plan_json) if isinstance(game_plan_json, str) else game_plan_json
        plan = GamePlan.model_validate(data)
        world_map: dict = {}
        if worlds_result_json.strip():
            parsed = json.loads(worlds_result_json)
            world_map = parsed.get("worlds", parsed) if isinstance(parsed, dict) else {}
        result = await pipeline.compose_game_scene(plan, world_map, import_to_godot=True)
        return {"success": True, **result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def generate_game_logic(
    game_plan_json: Annotated[str, Field(description="JSON game plan from design_game.")],
    game_project_path: Annotated[
        str,
        Field(default="", description="If set, write generated .gd files into project scripts/."),
    ] = "",
    ctx: Context = None,
) -> dict:
    """Generate GDScript files; optionally persist to a Godot project."""
    try:
        data = json.loads(game_plan_json) if isinstance(game_plan_json, str) else game_plan_json
        plan = GamePlan.model_validate(data)
        result = await pipeline.generate_game_logic(plan, ctx)
        payload: dict = {"success": True, **result}
        if game_project_path.strip():
            from godot_mcp.game_builder.project import sync_project_from_plan

            payload["project_sync"] = sync_project_from_plan(game_project_path, plan, result)
        return payload
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def export_and_ship(
    game_plan_json: Annotated[str, Field(description="JSON game plan from design_game.")],
    game_project_path: Annotated[str, Field(description="Godot project directory path.")],
    itch_target: Annotated[str, Field(description="itch.io user/game slug (e.g. 'sandraschi/my-game').")] = "",
    channel: Annotated[str, Field(description="Butler channel: 'html', 'win', 'osx', 'linux'.")] = "html",
) -> dict:
    """Export the Godot project and optionally ship to itch.io."""
    try:
        data = json.loads(game_plan_json) if isinstance(game_plan_json, str) else game_plan_json
        plan = GamePlan.model_validate(data)
        result = await pipeline.export_and_ship(plan, game_project_path, itch_target, channel)
        return result
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def build_game(
    game_concept: Annotated[str, Field(description="Natural language game description.")],
    worldlabs_url: Annotated[str, Field(description="worldlabs-mcp bridge URL.")] = "http://127.0.0.1:10865",
    game_project_path: Annotated[
        str,
        Field(description="Godot project directory; empty uses templates/game-template copy under build/."),
    ] = "",
    ship: Annotated[bool, Field(description="Also ship to itch.io? Requires BUTLER_API_KEY.")] = False,
    itch_target: Annotated[str, Field(default="", description="Override itch.io slug when ship=true.")] = "",
    ctx: Context = None,
) -> dict:
    """Build a complete game: design → worlds (fleet stage) → compose → logic → export."""
    return await pipeline.build_game(
        game_concept,
        ctx,
        worldlabs_url=worldlabs_url,
        game_project_path=game_project_path,
        ship=ship,
        itch_target=itch_target,
    )


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.3.0")(design_game)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(generate_game_worlds)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(compose_game_scene)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(generate_game_logic)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(export_and_ship)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(build_game)
