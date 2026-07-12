"""MCP tools for the Game Builder pipeline — design, generate, compose, ship."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Annotated, Any

from fastmcp import Context
from pydantic import Field

from godot_mcp.game_builder import pipeline
from godot_mcp.game_builder.dialogue import generate_dialogue_manager
from godot_mcp.game_builder.plan import GamePlan

logger = logging.getLogger("godot-mcp.game-builder-tools")

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


async def generate_game_tests(
    game_plan_json: Annotated[str, Field(description="JSON game plan from design_game.")],
    game_project_path: Annotated[str, Field(description="Godot project directory with generated scripts.")],
    ctx: Context = None,
) -> dict:
    """Generate GUT test scripts for generated game logic and optionally run them.

    Installs GUT plugin if not present, generates test scripts from the game
    plan's script specs, writes them to ``res://test/unit/``, and runs them
    via Godot headless CLI.

    ## Return Format
    {"success": bool, "tests": {str: {"passed": bool, "assertions": int, ...}}, "summary": str}

    ## Examples
    await generate_game_tests(game_plan_json='...', game_project_path='C:/MyGame')
    """
    from godot_mcp.game_builder.prompts import GDSCRIPT_TEST_PROMPT
    from godot_mcp.sampling.service import sample_text
    from godot_mcp.services.godot_bridge import find_godot

    project = Path(game_project_path)
    if not (project / "project.godot").is_file():
        return {"success": False, "error": f"No project.godot found at {game_project_path}"}

    try:
        data = json.loads(game_plan_json) if isinstance(game_plan_json, str) else game_plan_json
        plan = GamePlan.model_validate(data)
    except Exception as e:
        return {"success": False, "error": f"Invalid game plan: {e}"}

    # Install GUT plugin if missing
    gut_dir = project / "addons" / "gut"
    if not gut_dir.is_dir():
        try:
            from godot_mcp.tools.addon_tools import install_community_plugin as _install_plugin

            logger.info("Installing GUT plugin for %s", game_project_path)
            result = await _install_plugin("gut", game_project_path)
            if not result.get("success"):
                return {"success": False, "error": f"GUT install failed: {result.get('error')}"}
        except Exception as e:
            return {"success": False, "error": f"GUT install failed: {e}"}

    # Create test directory
    test_dir = project / "test" / "unit"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_results: dict[str, Any] = {}
    for script in plan.scripts:
        script_path = project / "scripts" / script.name
        if not script_path.is_file():
            test_results[script.name] = {"error": "Script file not found", "generated": False}
            continue

        code = script_path.read_text(encoding="utf-8")
        prompt = GDSCRIPT_TEST_PROMPT.format(
            title=plan.title,
            description=plan.description,
            genre=plan.genre or "arcade",
            viewport=plan.viewport,
            player_type=plan.player.type if plan.player else "runner",
            controls=str(plan.controls),
            script_name=script.name,
            code=code,
        )
        try:
            test_code = await sample_text(ctx, prompt=prompt, max_tokens=1536)
            test_code = test_code.strip().removeprefix("```gdscript").removeprefix("```").removesuffix("```").strip()
            test_filename = f"test_{script.name.replace('.gd', '')}.gd"
            (test_dir / test_filename).write_text(test_code, encoding="utf-8")
            test_results[script.name] = {"test_file": test_filename, "size_bytes": len(test_code), "generated": True}
        except Exception as e:
            test_results[script.name] = {"error": str(e), "generated": False}

    generated = sum(1 for r in test_results.values() if r.get("generated"))

    # Run tests via GUT CLI
    godot = await asyncio.to_thread(find_godot)
    run_output = ""
    if godot and generated > 0:
        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                [
                    godot,
                    "--headless",
                    "--path",
                    game_project_path,
                    "-s",
                    "addons/gut/gut_cmdln.gd",
                    "-d",
                    "res://test/unit/",
                    "-gtest",
                    "--exit-on-finish",
                    "-glog",
                    "2",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            run_output = proc.stdout[-2000:] if proc.stdout else proc.stderr[-2000:]
            # Parse test results from GUT output
            passed = run_output.count("PASS")
            failed = run_output.count("FAIL")
            test_results["_run"] = {"passed": passed, "failed": failed, "exit_code": proc.returncode}
        except subprocess.TimeoutExpired:
            test_results["_run"] = {"error": "Test run timed out after 120s"}
        except Exception as e:
            test_results["_run"] = {"error": str(e)}

    summary = f"{generated}/{len(plan.scripts)} test scripts generated"
    if run_output:
        summary += f" | Run: {test_results.get('_run', {}).get('passed', 0)} passed, {test_results.get('_run', {}).get('failed', 0)} failed"
    return {"success": True, "tests": test_results, "summary": summary, "run_output": run_output[-500:]}


async def generate_dialogue(
    game_plan_json: Annotated[str, Field(description="JSON game plan from design_game.")],
    game_project_path: Annotated[str, Field(description="Godot project directory.")],
    ctx: Context = None,
) -> dict:
    """Generate dialogue scripts and optional Dialogic timelines from GamePlan narrative.

    Creates a self-contained DialogueManager.gd from NPC dialogues.
    If Dialogic plugin is installed (addons/dialogic/), also generates
    .dtl timeline files for each NPC.

    ## Return Format
    {"success": bool, "files": [str], "count": int}

    ## Examples
    await generate_dialogue(game_plan_json='...', game_project_path='C:/MyGame')
    """
    try:
        data = json.loads(game_plan_json) if isinstance(game_plan_json, str) else game_plan_json
        plan = GamePlan.model_validate(data)
    except Exception as e:
        return {"success": False, "error": f"Invalid game plan: {e}"}

    npcs = [n.model_dump() for n in plan.npcs]
    narrative = plan.narrative.model_dump() if plan.narrative else None
    return generate_dialogue_manager(game_project_path, npcs, narrative)


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.3.0")(design_game)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(generate_game_worlds)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(compose_game_scene)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(generate_game_logic)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(export_and_ship)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(build_game)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(generate_game_tests)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(generate_dialogue)
