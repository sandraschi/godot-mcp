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
    """Design a game from a natural-language concept using AI.

    The LLM decomposes your idea into a structured game plan: worlds to generate,
    scenes to create, scripts to write, player controls, scoring, and export settings.

    ## Return Format
    {
      "success": bool,
      "plan": { full GamePlan JSON },
      "summary": "Game: {title} — {genre}. {n_worlds} worlds, {n_scenes} scenes, {n_scripts} scripts."
    }
    """
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
    """Generate all Marble worlds defined in a game plan.

    Submits generation requests to worldlabs-mcp for each world, then polls until
    completion. Each world costs 1500 Marble credits (marble-1.1).

    ## Return Format
    {"success": bool, "worlds": {world_id: {status, world_id, assets}}, "summary": "N completed, M failed"}
    """
    try:
        data = json.loads(game_plan_json) if isinstance(game_plan_json, str) else game_plan_json
        plan = GamePlan.model_validate(data)
        result = await pipeline.generate_game_worlds(plan, worldlabs_url)
        return {"success": True, **result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def compose_game_scene(
    game_plan_json: Annotated[str, Field(description="JSON game plan from design_game.")],
) -> dict:
    """Assemble the Godot scene from a game plan.

    Imports Marble worlds, creates the scene structure (nodes, lighting, camera),
    and prepares the project for scripts.

    Requires Godot running with the bridge on port 9080 and worlds staged in the exchange.

    ## Return Format
    {"success": bool, "steps": ["lighting", "camera", "worlds_imported", "scene_structure"]}
    """
    try:
        data = json.loads(game_plan_json) if isinstance(game_plan_json, str) else game_plan_json
        plan = GamePlan.model_validate(data)
        result = await pipeline.compose_game_scene(plan)
        return {"success": True, **result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def generate_game_logic(
    game_plan_json: Annotated[str, Field(description="JSON game plan from design_game.")],
    ctx: Context = None,
) -> dict:
    """Generate all GDScript files defined in a game plan.

    Uses AI sampling (ctx.sample) to write complete GDScript for each script
    described in the plan. Scripts reference the existing scene structure and
    player controls defined in the plan.

    ## Return Format
    {
      "success": bool,
      "scripts": {filename: {code, size_bytes}},
      "summary": "N/M scripts generated"
    }
    """
    try:
        data = json.loads(game_plan_json) if isinstance(game_plan_json, str) else game_plan_json
        plan = GamePlan.model_validate(data)
        result = await pipeline.generate_game_logic(plan, ctx)
        return {"success": True, **result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def export_and_ship(
    game_plan_json: Annotated[str, Field(description="JSON game plan from design_game.")],
    game_project_path: Annotated[str, Field(description="Godot project directory path.")],
    itch_target: Annotated[str, Field(description="itch.io user/game slug (e.g. 'sandraschi/my-game').")] = "",
    channel: Annotated[str, Field(description="Butler channel: 'html', 'win', 'osx', 'linux'.")] = "html",
) -> dict:
    """Export the Godot project and optionally ship to itch.io.

    Requires GODOT_PATH (or auto-detect), BUTLER_API_KEY for itch.io push,
    and ITCH_TARGET for the itch.io slug.

    ## Return Format
    {
      "success": bool,
      "export": { godot_export_release result },
      "ship": { ship_to_itch result }  // if itch_target provided
    }
    """
    try:
        data = json.loads(game_plan_json) if isinstance(game_plan_json, str) else game_plan_json
        plan = GamePlan.model_validate(data)
        result = await pipeline.export_and_ship(plan, game_project_path, itch_target, channel)
        return result
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def build_game(
    game_concept: Annotated[str, Field(description="Natural language game description. E.g. 'a 2D endless runner with neon visuals'.")],
    worldlabs_url: Annotated[str, Field(description="worldlabs-mcp bridge URL.")] = "http://127.0.0.1:10865",
    game_project_path: Annotated[str, Field(description="Godot project directory for building the game.")] = "",
    ship: Annotated[bool, Field(description="Also ship to itch.io? Requires BUTLER_API_KEY.")] = False,
    ctx: Context = None,
) -> dict:
    """Build a complete game from a natural-language concept.

    MASTER TOOL. Runs the full pipeline: design → generate worlds → compose scene
    → generate logic → export → (optionally) ship.

    Requires worldlabs-mcp running on worldlabs_url and Godot with bridge on port 9080.

    ## Pipeline Steps
    1. design_game: LLM decomposes concept into GamePlan
    2. generate_game_worlds: Submits Marble generation for each world
    3. compose_game_scene: Imports GLBs into Godot, sets up scene
    4. generate_game_logic: AI writes all GDScript files
    5. export_and_ship: Exports HTML5, optionally ships to itch.io

    ## Return Format
    {
      "success": true,
      "plan": { game plan },
      "worlds": { generation results },
      "scene": { composition results },
      "scripts": { generated scripts },
      "export": { export results },
      "ship": { itch.io results }  // if ship=true
    }
    """
    result: dict = {"success": False}

    try:
        # Step 1: Design
        plan = await pipeline.design_game(game_concept, ctx)
        result["plan"] = json.loads(plan.to_json())
        result["summary"] = f"Game: {plan.title} ({plan.genre})"

        # Step 2: Generate worlds
        if plan.worlds:
            world_result = await pipeline.generate_game_worlds(plan, worldlabs_url)
            result["worlds"] = world_result

        # Step 3: Compose scene
        scene_result = await pipeline.compose_game_scene(plan)
        result["scene"] = scene_result

        # Step 4: Generate logic
        logic_result = await pipeline.generate_game_logic(plan, ctx)
        result["scripts"] = logic_result

        # Step 5: Export & ship
        if game_project_path:
            export = await pipeline.export_and_ship(
                plan, game_project_path, itch_target="", channel="html"
            )
            result["export"] = export
            if ship:
                result["ship"] = export.get("ship", {})

        result["success"] = True
        return result

    except Exception as exc:
        result["error"] = str(exc)
        result["recovery"] = "Check logs. Partial results included above for completed steps."
        return result


# Register all tools
def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.2.0")(design_game)
    mcp.tool(annotations=_MUTATING, version="0.2.0")(generate_game_worlds)
    mcp.tool(annotations=_MUTATING, version="0.2.0")(compose_game_scene)
    mcp.tool(annotations=_MUTATING, version="0.2.0")(generate_game_logic)
    mcp.tool(annotations=_MUTATING, version="0.2.0")(export_and_ship)
    mcp.tool(annotations=_MUTATING, version="0.2.0")(build_game)
