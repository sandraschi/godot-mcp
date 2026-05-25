"""Pipeline orchestration — chains worldlabs-mcp + godot-mcp for game-from-prompt."""

from __future__ import annotations

import logging
from typing import Any

from godot_mcp.game_builder.plan import GamePlan
from godot_mcp.game_builder.prompts import GAME_DESIGNER_SYSTEM_PROMPT, GDScript_SPEC_PROMPT
from godot_mcp.mcp_bridge import get_or_create_bridge
from godot_mcp.sampling.service import sample_text

logger = logging.getLogger("godot_mcp.game_builder")


async def design_game(game_concept: str, ctx: Any = None) -> GamePlan:
    """Use LLM sampling to decompose a natural-language game concept into a GamePlan."""
    response = await sample_text(
        ctx,
        prompt=f"Design a game from this concept:\n\n{game_concept}",
        system=GAME_DESIGNER_SYSTEM_PROMPT,
        max_tokens=2048,
    )

    # Extract JSON from response (LLM might wrap in markdown)
    text = response.strip()
    if text.startswith("```"):
        # Remove markdown fences
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    try:
        return GamePlan.from_json(text)
    except Exception as exc:
        logger.error("Failed to parse GamePlan from LLM: %s\nRaw: %s", exc, text[:500])
        raise ValueError(f"LLM output could not be parsed as GamePlan: {exc}") from exc


async def generate_game_worlds(plan: GamePlan, worldlabs_url: str = "http://127.0.0.1:10865") -> dict[str, Any]:
    """Generate all Marble worlds in the plan. Returns world_id -> result map."""
    if not plan.worlds:
        return {"worlds": {}, "message": "No worlds to generate."}

    bridge = await get_or_create_bridge(worldlabs_url)

    logger.info("Generating %d worlds via %s", len(plan.worlds), worldlabs_url)
    results: dict[str, Any] = {}
    operations: dict[str, str] = {}

    # Submit all
    for world in plan.worlds:
        logger.info("  Submitting: %s", world.id)
        try:
            resp = await bridge.call_tool("generate_world_from_text", {
                "text_prompt": world.prompt,
                "display_name": world.name or world.id,
                "model": world.model,
            })
            if resp.get("success"):
                result_data = resp.get("result", resp)
                op_id = result_data.get("operation_id", "")
                if not op_id:
                    # Try nested paths
                    op_id = result_data.get("data", {}).get("operation_id", "")
                if op_id:
                    operations[world.id] = op_id
                    results[world.id] = {"operation_id": op_id, "status": "submitted"}
                else:
                    results[world.id] = {"error": "No operation_id in response", "status": "failed", "raw": str(resp)[:200]}
            else:
                results[world.id] = {"error": resp.get("error", "Unknown error"), "status": "failed"}
        except Exception as exc:
            logger.exception("Failed to submit world %s: %s", world.id, exc)
            results[world.id] = {"error": str(exc), "status": "failed"}

    # Poll all
    logger.info("Waiting for %d worlds to complete...", len(operations))
    import asyncio

    pending = dict(operations)
    max_wait = 600  # 10 minutes total
    polled = 0
    while pending and polled < max_wait // 10:
        for w_id, op_id in list(pending.items()):
            try:
                resp = await bridge.call_tool("wait_for_world", {
                    "operation_id": op_id,
                    "timeout_seconds": 10,
                })
                if resp.get("success"):
                    world_data = resp.get("result", resp)
                    status = world_data.get("status", world_data.get("state", ""))
                    if status in ("completed", "done", "success"):
                        results[w_id]["status"] = "completed"
                        results[w_id]["world_id"] = world_data.get("world_id", "")
                        results[w_id]["assets"] = world_data.get("assets", {})
                        del pending[w_id]
                        logger.info("  Completed: %s", w_id)
                    elif status in ("failed", "error"):
                        results[w_id]["status"] = "failed"
                        results[w_id]["error"] = world_data.get("error", "Unknown")
                        del pending[w_id]
                        logger.warning("  Failed: %s — %s", w_id, world_data.get("error"))
            except Exception as exc:
                logger.exception("Poll failed for %s: %s", w_id, exc)

        if pending:
            await asyncio.sleep(10)
            polled += 1

    if pending:
        logger.warning("%d worlds still pending after timeout", len(pending))
        for w_id in pending:
            results[w_id]["status"] = "timeout"

    completed = sum(1 for r in results.values() if r.get("status") == "completed")
    failed = sum(1 for r in results.values() if r.get("status") == "failed")
    return {"worlds": results, "summary": f"{completed} completed, {failed} failed, {len(pending)} pending"}


async def compose_game_scene(plan: GamePlan) -> dict[str, Any]:
    """Set up the Godot scene: import worlds, add lights/camera, create scene structure."""
    from godot_mcp.services.godot_bridge import get_bridge

    bridge = get_bridge()
    if not bridge.connected:
        bridge.connect()

    steps: list[str] = []

    # 1. Scene setup (lights + camera)
    for _scene in plan.scenes:
        if plan.lighting and plan.viewport == "3d":
            try:
                bridge.send("add_light", {"type": "directional", "intensity": plan.lighting.directional_intensity}, timeout=10)
                bridge.send("add_light", {"type": "ambient", "intensity": plan.lighting.ambient_intensity}, timeout=10)
                steps.append("lighting")
            except Exception as exc:
                logger.warning("Lighting failed: %s", exc)

        if plan.camera and plan.viewport == "3d":
            try:
                bridge.send("create_camera", {
                    "name": "GameCamera",
                    "position": {"x": plan.camera.position[0], "y": plan.camera.position[1], "z": plan.camera.position[2]},
                    "fov": plan.camera.fov,
                }, timeout=10)
                steps.append("camera")
            except Exception as exc:
                logger.warning("Camera creation failed: %s", exc)

        break  # One scene setup call

    # 2. Import worlds into Godot
    from godot_mcp.fleet import pipeline as fleet_pipeline

    world_imports: dict[str, Any] = {}
    for world in plan.worlds:
        world_id = world.id
        # Try importing from the fleet pipeline (if GLB was staged)
        try:
            result = fleet_pipeline.import_mesh_path(
                path=str(_worldlabs_glb_path(world_id)),
                name=f"World_{world_id}",
                scale=1.0,
            )
            world_imports[world_id] = {"imported": True, "result": str(result)[:200]}
        except Exception:
            world_imports[world_id] = {"imported": False, "note": "GLB not yet staged — run generate_game_worlds first"}

    steps.append("worlds_imported")

    # 3. Create scene structure nodes
    for scene_spec in plan.scenes:
        # Only create container nodes; scripts are attached later
        if scene_spec.type in ("Node2D", "Node3D", "Control", "CanvasLayer"):
            try:
                bridge.send("add_node", {
                    "parent": ".",
                    "type": scene_spec.type,
                    "name": scene_spec.name,
                }, timeout=10)
            except Exception as exc:
                logger.debug("Node '%s' creation skipped: %s", scene_spec.name, exc)

    steps.append("scene_structure")
    return {"success": True, "steps": steps, "world_imports": world_imports}


async def generate_game_logic(plan: GamePlan, ctx: Any = None) -> dict[str, Any]:
    """Generate all GDScript files from the game plan using LLM."""
    if not plan.scripts:
        return {"scripts": {}, "message": "No scripts to generate."}

    results: dict[str, Any] = {}
    scene_list = ", ".join(s.name for s in plan.scenes) if plan.scenes else "N/A"

    for script in plan.scripts:
        # Determine extends type from scene association
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
            ship_result = _ship(target=target, game="custom", project_path=game_project_path,
                                itch_target=itch_target, channel=channel)
            result["ship"] = ship_result
        except Exception as exc:
            result["ship_error"] = str(exc)
            logger.exception("itch.io ship failed: %s", exc)

    return result


def _worldlabs_glb_path(world_id: str) -> str:
    """Return the expected exchange path for a World Labs collider GLB."""
    from godot_mcp.fleet import exchange

    return str(exchange.worldlabs_dir() / f"{world_id[:12]}_collider.glb")
