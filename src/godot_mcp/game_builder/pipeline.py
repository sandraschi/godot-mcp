"""Pipeline orchestration — chains worldlabs-mcp + godot-mcp for game-from-prompt."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from godot_mcp.game_builder import worlds as world_helpers
from godot_mcp.game_builder.plan import GamePlan
from godot_mcp.game_builder.project import (
    copy_world_meshes_to_project,
    ensure_project_path,
    sync_project_from_plan,
)
from godot_mcp.game_builder.prompts import GAME_DESIGNER_SYSTEM_PROMPT, GDScript_SPEC_PROMPT
from godot_mcp.mcp_bridge import get_or_create_bridge
from godot_mcp.sampling.service import sample_text

logger = logging.getLogger("godot_mcp.game_builder")

POLL_INTERVAL_SECONDS = 10
MAX_WORLD_WAIT_SECONDS = 600


async def design_game(game_concept: str, ctx: Any = None) -> GamePlan:
    """Use LLM sampling to decompose a natural-language game concept into a GamePlan."""
    response = await sample_text(
        ctx,
        prompt=f"Design a game from this concept:\n\n{game_concept}",
        system=GAME_DESIGNER_SYSTEM_PROMPT,
        max_tokens=2048,
    )

    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    try:
        return GamePlan.from_json(text)
    except Exception as exc:
        logger.error("Failed to parse GamePlan from LLM: %s\nRaw: %s", exc, text[:500])
        raise ValueError(f"LLM output could not be parsed as GamePlan: {exc}") from exc


async def generate_game_worlds(
    plan: GamePlan,
    worldlabs_url: str = "http://127.0.0.1:10865",
    *,
    stage_meshes: bool = True,
) -> dict[str, Any]:
    """Generate Marble worlds, then stage collider GLBs via fleet exchange."""
    if not plan.worlds:
        return {"worlds": {}, "message": "No worlds to generate."}

    bridge = await get_or_create_bridge(worldlabs_url)

    logger.info("Generating %d worlds via %s", len(plan.worlds), worldlabs_url)
    results: dict[str, Any] = {}
    operations: dict[str, str] = {}

    for world in plan.worlds:
        logger.info("  Submitting: %s", world.id)
        try:
            resp = await bridge.call_tool(
                "generate_world_from_text",
                {
                    "text_prompt": world.prompt,
                    "display_name": world.name or world.id,
                    "model": world.model,
                },
            )
            op_payload = world_helpers.unwrap_bridge_response(resp)
            if resp.get("success") is False and not op_payload.get("operation_id"):
                results[world.id] = {
                    "error": resp.get("error", "Unknown error"),
                    "status": "failed",
                    "plan_slug": world.id,
                }
                continue

            op_id = world_helpers.extract_operation_id(op_payload)
            if op_id:
                operations[world.id] = op_id
                results[world.id] = {
                    "operation_id": op_id,
                    "status": "submitted",
                    "plan_slug": world.id,
                }
            else:
                results[world.id] = {
                    "error": "No operation_id in response",
                    "status": "failed",
                    "plan_slug": world.id,
                    "raw": str(resp)[:200],
                }
        except Exception as exc:
            logger.exception("Failed to submit world %s: %s", world.id, exc)
            results[world.id] = {"error": str(exc), "status": "failed", "plan_slug": world.id}

    logger.info("Waiting for %d worlds to complete...", len(operations))
    pending = dict(operations)
    deadline = time.monotonic() + MAX_WORLD_WAIT_SECONDS

    while pending and time.monotonic() < deadline:
        for plan_slug, op_id in list(pending.items()):
            try:
                resp = await bridge.call_tool("get_operation", {"operation_id": op_id})
                op = world_helpers.unwrap_bridge_response(resp)
                if resp.get("success") is False and not op.get("done"):
                    continue

                if world_helpers.operation_failed(op):
                    results[plan_slug]["status"] = "failed"
                    err = op.get("error", {})
                    if isinstance(err, dict):
                        results[plan_slug]["error"] = err.get("message", str(err))
                    else:
                        results[plan_slug]["error"] = str(err or "generation failed")
                    del pending[plan_slug]
                    continue

                if not world_helpers.operation_is_done(op):
                    continue

                marble_id = world_helpers.extract_marble_world_id(op)
                results[plan_slug]["status"] = "completed"
                results[plan_slug]["marble_world_id"] = marble_id
                results[plan_slug]["world_id"] = marble_id
                results[plan_slug]["assets"] = world_helpers.extract_world_assets(op)
                if stage_meshes:
                    world_helpers.enrich_world_result(results[plan_slug], stage_mesh=True)
                del pending[plan_slug]
                logger.info("  Completed: %s → marble %s", plan_slug, marble_id[:12] if marble_id else "?")
            except Exception as exc:
                logger.exception("Poll failed for %s: %s", plan_slug, exc)

        if pending:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    if pending:
        logger.warning("%d worlds still pending after timeout", len(pending))
        for plan_slug in pending:
            results[plan_slug]["status"] = "timeout"

    completed = sum(1 for r in results.values() if r.get("status") == "completed")
    failed = sum(1 for r in results.values() if r.get("status") == "failed")
    staged = sum(1 for r in results.values() if r.get("mesh_path"))
    return {
        "worlds": results,
        "summary": f"{completed} completed, {failed} failed, {len(pending)} pending, {staged} staged",
    }


async def compose_game_scene(
    plan: GamePlan,
    world_results: dict[str, Any] | None = None,
    *,
    import_to_godot: bool = True,
) -> dict[str, Any]:
    """Set up Godot scene: import staged Marble GLBs, lights, camera, nodes."""
    from godot_mcp.fleet import pipeline as fleet_pipeline
    from godot_mcp.services.godot_bridge import get_bridge

    world_map = world_results or {}
    steps: list[str] = []
    world_imports: dict[str, Any] = {}

    bridge = None
    if import_to_godot:
        bridge = get_bridge()
        if not bridge.connected:
            bridge.connect()

    if bridge and plan.lighting and plan.viewport == "3d":
        try:
            bridge.send(
                "add_light",
                {"type": "directional", "intensity": plan.lighting.directional_intensity},
                timeout=10,
            )
            bridge.send(
                "add_light",
                {"type": "ambient", "intensity": plan.lighting.ambient_intensity},
                timeout=10,
            )
            steps.append("lighting")
        except Exception as exc:
            logger.warning("Lighting failed: %s", exc)

    if bridge and plan.camera and plan.viewport == "3d":
        try:
            bridge.send(
                "create_camera",
                {
                    "name": "GameCamera",
                    "position": {
                        "x": plan.camera.position[0],
                        "y": plan.camera.position[1],
                        "z": plan.camera.position[2],
                    },
                    "fov": plan.camera.fov,
                },
                timeout=10,
            )
            steps.append("camera")
        except Exception as exc:
            logger.warning("Camera creation failed: %s", exc)

    for world in plan.worlds:
        plan_slug = world.id
        entry = world_map.get(plan_slug, {})
        marble_id = world_helpers.marble_id_for_plan_slug(world_map, plan_slug)
        mesh_path = entry.get("mesh_path") if isinstance(entry, dict) else None
        node_name = f"World_{plan_slug}"

        if not import_to_godot:
            world_imports[plan_slug] = {
                "imported": False,
                "marble_world_id": marble_id,
                "mesh_path": mesh_path,
                "note": "import_to_godot=False",
            }
            continue

        try:
            if mesh_path and Path(str(mesh_path)).is_file():
                imported = fleet_pipeline.import_mesh_path(mesh_path, name=node_name, scale=1.0)
                world_imports[plan_slug] = {
                    "imported": imported.get("success", False),
                    "marble_world_id": marble_id,
                    "mesh_path": mesh_path,
                    "result": imported,
                }
            elif marble_id:
                imported = fleet_pipeline.worldlabs_mesh_to_godot(marble_id, node_name=node_name, scale=1.0)
                world_imports[plan_slug] = {
                    "imported": imported.get("success", False),
                    "marble_world_id": marble_id,
                    "mesh_path": imported.get("mesh_path"),
                    "spark_viewer_url": imported.get("spark_viewer_url"),
                    "result": imported,
                }
            else:
                world_imports[plan_slug] = {
                    "imported": False,
                    "error": "No marble_world_id or mesh_path — run generate_game_worlds first",
                }
        except Exception as exc:
            logger.warning("World import failed for %s: %s", plan_slug, exc)
            world_imports[plan_slug] = {"imported": False, "error": str(exc), "marble_world_id": marble_id}

    steps.append("worlds_imported")

    if bridge:
        for scene_spec in plan.scenes:
            if scene_spec.type in ("Node2D", "Node3D", "Control", "CanvasLayer", "CharacterBody2D"):
                try:
                    bridge.send(
                        "add_node",
                        {
                            "parent": ".",
                            "type": scene_spec.type,
                            "name": scene_spec.name,
                        },
                        timeout=10,
                    )
                except Exception as exc:
                    logger.debug("Node '%s' creation skipped: %s", scene_spec.name, exc)
        steps.append("scene_structure")

    imported_count = sum(1 for v in world_imports.values() if v.get("imported"))
    return {
        "success": True,
        "steps": steps,
        "world_imports": world_imports,
        "summary": f"{imported_count}/{len(plan.worlds)} worlds imported into Godot bridge",
    }


async def generate_game_logic(plan: GamePlan, ctx: Any = None) -> dict[str, Any]:
    """Generate all GDScript files from the game plan using LLM."""
    if not plan.scripts:
        return {"scripts": {}, "message": "No scripts to generate."}

    results: dict[str, Any] = {}
    scene_list = ", ".join(s.name for s in plan.scenes) if plan.scenes else "N/A"

    for script in plan.scripts:
        extends_type = "Node"
        for s in plan.scenes:
            if script.name in s.scripts:
                extends_type = s.type
                break

        prompt = GDScript_SPEC_PROMPT.format(
            title=plan.title,
            description=plan.description,
            genre=plan.genre or "arcade",
            viewport=plan.viewport,
            player_type=plan.player.type if plan.player else "runner",
            controls=str(plan.controls),
            scenes=scene_list,
            script_description=script.description,
            extends_type=extends_type,
            scene_structure=scene_list,
        )

        try:
            code = await sample_text(ctx, prompt=prompt, max_tokens=1024)
            results[script.name] = {
                "code": code,
                "size_bytes": len(code),
                "generated": True,
            }
            logger.info("Generated %s (%d bytes)", script.name, len(code))
        except Exception as exc:
            logger.exception("Failed to generate %s: %s", script.name, exc)
            results[script.name] = {"error": str(exc), "generated": False}

    completed = sum(1 for r in results.values() if r.get("generated"))
    return {"scripts": results, "summary": f"{completed}/{len(plan.scripts)} scripts generated"}


async def export_and_ship(
    plan: GamePlan,
    game_project_path: str,
    itch_target: str = "",
    channel: str = "html",
) -> dict[str, Any]:
    """Export the Godot project and optionally ship to itch.io."""
    from godot_mcp.itch.service import godot_export_release as _export
    from godot_mcp.itch.service import ship_to_itch as _ship

    target = plan.export.target if plan.export else "web"

    export_result = _export(target=target, game="custom", project_path=game_project_path)
    if not export_result.get("success"):
        return {"success": False, "export_error": export_result}

    result: dict[str, Any] = {"success": True, "export": export_result}

    if itch_target:
        try:
            ship_result = _ship(
                target=target,
                game="custom",
                project_path=game_project_path,
                itch_target=itch_target,
                channel=channel,
            )
            result["ship"] = ship_result
        except Exception as exc:
            result["ship_error"] = str(exc)
            logger.exception("itch.io ship failed: %s", exc)

    return result


async def build_game(
    game_concept: str,
    ctx: Any = None,
    *,
    worldlabs_url: str = "http://127.0.0.1:10865",
    game_project_path: str = "",
    ship: bool = False,
    itch_target: str = "",
) -> dict[str, Any]:
    """Full pipeline with fleet wiring: worlds staged, compose uses Marble ids, scripts written."""
    result: dict[str, Any] = {"success": False}

    try:
        plan = await design_game(game_concept, ctx)
        result["plan"] = plan.model_dump()
        result["summary"] = f"Game: {plan.title} ({plan.genre})"

        world_map: dict[str, Any] = {}
        if plan.worlds:
            world_result = await generate_game_worlds(plan, worldlabs_url, stage_meshes=True)
            result["worlds"] = world_result
            world_map = world_result.get("worlds", {})

        project = ensure_project_path(plan.title, game_project_path)
        result["project_path"] = str(project)

        if world_map:
            result["project_assets"] = copy_world_meshes_to_project(project, world_map)

        scene_result = await compose_game_scene(plan, world_map, import_to_godot=True)
        result["scene"] = scene_result

        logic_result = await generate_game_logic(plan, ctx)
        result["scripts"] = logic_result
        result["project_scripts"] = sync_project_from_plan(project, plan, logic_result)

        itch = itch_target or (plan.export.itch_target if plan.export else "")
        export = await export_and_ship(plan, str(project), itch_target=itch if ship else "", channel="html")
        result["export"] = export
        if ship and export.get("ship"):
            result["ship"] = export["ship"]

        result["success"] = bool(export.get("success"))
        return result
    except Exception as exc:
        result["error"] = str(exc)
        result["recovery"] = "Check logs. Partial results included above for completed steps."
        return result
