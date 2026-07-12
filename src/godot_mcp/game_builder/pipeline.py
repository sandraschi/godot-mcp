"""Pipeline orchestration — chains worldlabs-mcp + godot-mcp for game-from-prompt."""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import tempfile
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
from godot_mcp.game_builder.prompts import GAME_DESIGNER_SYSTEM_PROMPT, GDSCRIPT_REPAIR_PROMPT, GDScript_SPEC_PROMPT
from godot_mcp.mcp_bridge import get_or_create_bridge
from godot_mcp.sampling.service import sample_text
from godot_mcp.services.godot_bridge import find_godot

logger = logging.getLogger("godot_mcp.game_builder")

POLL_INTERVAL_SECONDS = 10
MAX_WORLD_WAIT_SECONDS = 600
MAX_REPAIR_ATTEMPTS = 2
KNOW_NODE_TYPES = frozenset(
    {
        "Node2D",
        "Node3D",
        "Control",
        "CanvasLayer",
        "CharacterBody2D",
        "CharacterBody3D",
        "RigidBody2D",
        "RigidBody3D",
        "StaticBody2D",
        "StaticBody3D",
        "Area2D",
        "Area3D",
        "Sprite2D",
        "Sprite3D",
        "AnimatedSprite2D",
        "AnimatedSprite3D",
        "AudioStreamPlayer2D",
        "AudioStreamPlayer3D",
        "Camera2D",
        "Camera3D",
        "MeshInstance3D",
        "GPUParticles3D",
        "CPUParticles3D",
        "Node",
        "Panel",
        "ColorRect",
        "TextureRect",
        "Label",
        "RichTextLabel",
        "Button",
        "TextureButton",
        "LineEdit",
        "HSlider",
        "VSlider",
        "ProgressBar",
        "HSplitContainer",
        "VSplitContainer",
        "TabContainer",
        "ScrollContainer",
        "MarginContainer",
        "HBoxContainer",
        "VBoxContainer",
        "GridContainer",
        "CenterContainer",
        "AspectRatioContainer",
        "NinePatchRect",
        "ParallaxBackground",
        "ParallaxLayer",
        "TileMap",
        "TileMapLayer",
        "MultiMeshInstance2D",
        "MultiMeshInstance3D",
        "PointLight2D",
        "DirectionalLight3D",
        "OmniLight3D",
        "SpotLight3D",
    }
)


async def _lint_with_gdlint(path: str) -> str:
    """Run gdlint on a .gd file and return combined error text (empty = clean)."""
    gdlint = shutil.which("gdlint") or str(Path.home() / ".local" / "bin" / "gdlint.exe")
    if not Path(gdlint).is_file():
        return ""
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            [gdlint, path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        errors = proc.stdout.strip() if proc.returncode != 0 else ""
        return errors[:500] if errors else ""
    except Exception:
        return ""


async def _compile_check_with_godot(path: str, godot: str) -> str:
    """Run godot --check-only and return stderr text (empty = clean)."""
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            [godot, "--headless", "--check-only", "--script", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return proc.stderr[:1000] if proc.returncode != 0 else ""
    except subprocess.TimeoutExpired:
        return "Godot check timed out after 30s"
    except FileNotFoundError:
        return "Godot not found"
    except Exception as exc:
        return str(exc)


async def _validate_and_repair_scripts(scripts: dict[str, Any], plan: GamePlan, ctx: Any = None) -> dict[str, Any]:
    """Validate generated GDScript via gdlint + godot --check-only, repair on failure.

    1. Run gdlint (fast style/naming check).
    2. Run godot --check-only (compilation check).
    3. If either fails, feed ALL errors to the LLM for up to MAX_REPAIR_ATTEMPTS rounds.
    """
    godot = await asyncio.to_thread(find_godot)
    has_gdlint = bool(shutil.which("gdlint")) or Path(Path.home() / ".local" / "bin" / "gdlint.exe").is_file()
    if not godot and not has_gdlint:
        logger.warning("Neither Godot nor gdlint found -- skipping GDScript validation")
        return {}

    report: dict[str, Any] = {}
    for name, data in scripts.items():
        if not data.get("generated"):
            continue
        code = data.get("code", "")
        if not code.strip():
            continue

        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".gd", delete=False, encoding="utf-8")
        try:
            tmp.write(code)
            tmp.close()

            for attempt in range(MAX_REPAIR_ATTEMPTS + 1):
                lint_errors = await _lint_with_gdlint(tmp.name) if has_gdlint else ""
                compile_errors = await _compile_check_with_godot(tmp.name, godot) if godot else ""
                combined = "\n".join(filter(None, [lint_errors, compile_errors]))

                if not combined:
                    report[name] = {"valid": True, "attempts": attempt}
                    break

                if attempt >= MAX_REPAIR_ATTEMPTS:
                    report[name] = {"valid": False, "error": combined[:500], "attempts": attempt}
                    logger.warning(
                        "Script '%s' still fails after %d repair attempts:\n%s", name, attempt, combined[:300]
                    )
                    break

                repair_prompt = GDSCRIPT_REPAIR_PROMPT.format(
                    script_name=name,
                    error_text=combined[:1000],
                    code=code,
                )
                try:
                    repaired = await sample_text(ctx, prompt=repair_prompt, max_tokens=2048)
                    repaired = (
                        repaired.strip().removeprefix("```gdscript").removeprefix("```").removesuffix("```").strip()
                    )
                    if repaired:
                        code = repaired
                        data["code"] = code
                        data["repaired_at_attempt"] = attempt + 1
                        with open(tmp.name, "w", encoding="utf-8") as f:
                            f.write(code)
                        lint_after = await _lint_with_gdlint(tmp.name) if has_gdlint else ""
                        compile_after = await _compile_check_with_godot(tmp.name, godot) if godot else ""
                        still_clean = not lint_after and not compile_after
                        if still_clean:
                            report[name] = {"repaired": True, "attempts": attempt + 1}
                            logger.info("Repaired '%s' cleanly (attempt %d)", name, attempt + 1)
                        else:
                            report[name] = {"repaired": True, "attempts": attempt + 1, "still_has_issues": True}
                            logger.info(
                                "Repaired '%s' (attempt %d) but %d checks still failing",
                                name,
                                attempt + 1,
                                bool(lint_after) + bool(compile_after),
                            )
                except Exception as exc:
                    logger.warning("Repair LLM call failed for '%s': %s", name, exc)
                    report[name] = {"valid": False, "error": str(exc), "attempts": attempt}
                    break
        except Exception as exc:
            report[name] = {"valid": False, "error": str(exc)}
        finally:
            try:
                Path(tmp.name).unlink(missing_ok=True)
            except Exception:
                logger.debug("Failed to clean up temp script %s", tmp.name)
    return report


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
                    await asyncio.to_thread(world_helpers.enrich_world_result, results[plan_slug], stage_mesh=True)
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
            await asyncio.to_thread(bridge.connect)

    if bridge and plan.lighting and plan.viewport == "3d":
        try:
            await asyncio.to_thread(
                bridge.send,
                "add_light",
                {"type": "directional", "intensity": plan.lighting.directional_intensity},
                10,
            )
            await asyncio.to_thread(
                bridge.send,
                "add_light",
                {"type": "ambient", "intensity": plan.lighting.ambient_intensity},
                10,
            )
            steps.append("lighting")
        except Exception as exc:
            logger.warning("Lighting failed: %s", exc)

    if bridge and plan.camera and plan.viewport == "3d":
        try:
            await asyncio.to_thread(
                bridge.send,
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
                10,
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
                imported = await asyncio.to_thread(fleet_pipeline.import_mesh_path, mesh_path, node_name, 1.0)
                world_imports[plan_slug] = {
                    "imported": imported.get("success", False),
                    "marble_world_id": marble_id,
                    "mesh_path": mesh_path,
                    "result": imported,
                }
            elif marble_id:
                imported = await asyncio.to_thread(fleet_pipeline.worldlabs_mesh_to_godot, marble_id, node_name, 1.0)
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

        async def _create_node_tree(spec, parent_path: str = "."):
            """Recursively create nodes from a SceneSpec tree."""
            if hasattr(spec, "type") and spec.type in KNOW_NODE_TYPES:
                try:
                    await asyncio.to_thread(
                        bridge.send, "add_node", {"parent": parent_path, "type": spec.type, "name": spec.name}, 10
                    )
                    child_path = parent_path.rstrip("/") + "/" + spec.name if parent_path != "." else spec.name
                    for child in getattr(spec, "children", []):
                        await _create_node_tree(child, child_path)
                except Exception as exc:
                    logger.debug("Node '%s' creation skipped: %s", spec.name, exc)

        for scene_spec in plan.scenes:
            await _create_node_tree(scene_spec, ".")
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
    if completed > 0:
        repair_report = await _validate_and_repair_scripts(results, plan, ctx)
        results["_validation"] = repair_report
        repaired = sum(1 for r in repair_report.values() if r.get("repaired"))
        if repaired:
            logger.info("Repaired %d script(s) via GDScript validation", repaired)
    return {
        "scripts": results,
        "summary": f"{completed}/{len(plan.scripts)} scripts generated",
        "validation": results.get("_validation", {}),
    }


async def export_and_ship(
    plan: GamePlan,
    game_project_path: str,
    itch_target: str = "",
    channel: str = "html",
) -> dict[str, Any]:
    """Export the Godot project and optionally ship to itch.io."""
    from godot_mcp.itch.service import godot_export_release_tool as _export
    from godot_mcp.itch.service import ship_to_itch as _ship_kwargs

    target = plan.export.target if plan.export else "web"

    export_result = await asyncio.to_thread(_export, target, "custom", game_project_path)
    if not export_result.get("success"):
        return {"success": False, "export_error": export_result}

    result: dict[str, Any] = {"success": True, "export": export_result}

    if itch_target:
        try:
            ship_result = await asyncio.to_thread(
                _ship_kwargs,
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
        if plan.narrative:
            result["summary"] += f" | Story: {plan.narrative.tone} — {plan.narrative.premise[:60]}"
        if plan.npcs:
            result["summary"] += f" | {len(plan.npcs)} NPCs"

        world_map: dict[str, Any] = {}
        if plan.worlds:
            world_result = await generate_game_worlds(plan, worldlabs_url, stage_meshes=True)
            result["worlds"] = world_result
            world_map = world_result.get("worlds", {})

        project = ensure_project_path(plan.title, game_project_path)
        result["project_path"] = str(project)

        # Auto-install plugins requested by the game plan
        effective_plugins = list(plan.plugins)
        if plan.npcs or plan.narrative:
            if "dialogic" not in effective_plugins:
                effective_plugins.append("dialogic")
        if effective_plugins:
            from godot_mcp.tools.addon_tools import install_community_plugin as _install_p

            plugin_results = []
            for pname in effective_plugins:
                try:
                    pr = await _install_p(pname, str(project))
                    plugin_results.append(
                        {
                            "plugin": pname,
                            "status": "installed" if pr.get("success") else "failed",
                            "error": pr.get("error"),
                        }
                    )
                except Exception as exc:
                    plugin_results.append({"plugin": pname, "status": "error", "error": str(exc)})
            result["plugins"] = plugin_results

        if world_map:
            result["project_assets"] = copy_world_meshes_to_project(project, world_map)

        scene_result = await compose_game_scene(plan, world_map, import_to_godot=True)
        result["scene"] = scene_result

        logic_result = await generate_game_logic(plan, ctx)
        result["scripts"] = logic_result
        result["project_scripts"] = sync_project_from_plan(project, plan, logic_result)

        # Generate tests for the generated scripts
        try:
            from godot_mcp.game_builder.tools import generate_game_tests

            test_result = await generate_game_tests(plan.to_json(), str(project), ctx)
            result["tests"] = test_result
        except Exception as exc:
            logger.warning("Test generation skipped: %s", exc)
            result["tests"] = {"success": False, "error": str(exc)}

        # Generate dialogue manager from narrative/NPCs
        if plan.npcs or plan.narrative:
            try:
                from godot_mcp.game_builder.dialogue import generate_dialogue_manager

                npcs_data = [n.model_dump() for n in plan.npcs]
                narrative_data = plan.narrative.model_dump() if plan.narrative else None
                dialogue_result = generate_dialogue_manager(str(project), npcs_data, narrative_data)
                result["dialogue"] = dialogue_result
            except Exception as exc:
                logger.warning("Dialogue generation skipped: %s", exc)

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
