"""Agentic workflow engine for multi-step tool orchestration."""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("godot-mcp.workflows")


class WorkflowStep:
    def __init__(self, name: str, tool: str, params: dict | None = None):
        self.name = name
        self.tool = tool
        self.params = params or {}
        self.result: dict | None = None

    async def execute(self, execute_tool_fn) -> dict:
        logger.info("Workflow step: %s -> %s", self.name, self.tool)
        self.result = await execute_tool_fn(self.tool, self.params)
        return self.result


class Workflow:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: list[WorkflowStep] = []
        self.context: dict[str, Any] = {}
        self.status = "pending"
        self.started_at: str | None = None
        self.completed_at: str | None = None

    def add_step(self, name: str, tool: str, params: dict | None = None):
        self.steps.append(WorkflowStep(name, tool, params))
        return self

    async def run(self, execute_tool_fn, inject_context: dict | None = None) -> dict:
        self.status = "running"
        self.started_at = datetime.now(UTC).isoformat()
        if inject_context:
            self.context.update(inject_context)

        results = []
        for step in self.steps:
            params = dict(step.params)
            for k, v in params.items():
                if isinstance(v, str) and v.startswith("{context."):
                    key = v[9:-1]
                    params[k] = self.context.get(key, v)
            result = await step.execute(execute_tool_fn)
            results.append({"step": step.name, "tool": step.tool, "result": result})
            if result.get("success") and step.tool == "godot_export_release":
                data = result.get("data") or {}
                if data.get("upload_dir"):
                    self.context["upload_dir"] = data["upload_dir"]
            if result.get("success") and step.tool == "steam_stage_build":
                stage = result.get("stage") or {}
                if stage.get("content_root"):
                    self.context["content_root"] = stage["content_root"]
            if not result.get("success", False):
                self.status = "failed"
                self.completed_at = datetime.now(UTC).isoformat()
                return {"success": False, "workflow": self.name, "failed_step": step.name, "results": results}

        self.status = "completed"
        self.completed_at = datetime.now(UTC).isoformat()
        return {"success": True, "workflow": self.name, "steps_completed": len(results), "results": results}


SCENE_SETUP_WORKFLOW = (
    Workflow(
        "Scene Setup",
        "Creates a complete scene with camera, lights, and environment.",
    )
    .add_step("Create Camera", "godot_create_camera", {"name": "MainCamera", "position_y": 5, "position_z": 10})
    .add_step("Add Directional Light", "godot_add_light", {"light_type": "directional", "intensity": 1.5})
    .add_step("Add Ambient Light", "godot_add_light", {"light_type": "ambient", "intensity": 0.3})
)

PARTICLE_CFD_WORKFLOW = (
    Workflow(
        "CFD Particle Visualization",
        "Loads a velocity field and spawns animated particles.",
    )
    .add_step("Load Velocity Field", "godot_load_velocity_field", {"csv_path": "{context.csv_path}"})
    .add_step(
        "Spawn Particles", "godot_spawn_particles", {"count": 5000, "spread_x": 10, "spread_y": 10, "spread_z": 10}
    )
    .add_step("Animate Streamlines", "godot_animate_streamlines", {})
)

SHIP_WEB_WORKFLOW = (
    Workflow(
        "Ship Web to itch.io",
        "Export HTML5 build, preview Butler diff, push to itch.io.",
    )
    .add_step(
        "Export Web",
        "godot_export_release",
        {"target": "web", "game": "{context.game}"},
    )
    .add_step(
        "Preview Push",
        "itch_push_preview",
        {"upload_dir": "{context.upload_dir}", "itch_target": "{context.itch_target}", "channel": "{context.channel}"},
    )
    .add_step(
        "Push",
        "itch_push",
        {"upload_dir": "{context.upload_dir}", "itch_target": "{context.itch_target}", "channel": "{context.channel}"},
    )
)

SHIP_STEAM_BETA_WORKFLOW = (
    Workflow(
        "Ship Windows to Steam (beta)",
        "Export Windows build, stage to exchange, upload to Steam beta branch.",
    )
    .add_step(
        "Stage Windows Build",
        "steam_stage_build",
        {"game": "{context.game}"},
    )
    .add_step(
        "Upload Prerelease",
        "ship_to_steam_prerelease",
        {"content_root": "{context.content_root}", "dry_run": True},
    )
)

SHIP_STEAM_RELEASE_WORKFLOW = (
    Workflow(
        "Ship Windows to Steam (release)",
        "Export Windows build, stage to exchange, upload to Steam default branch.",
    )
    .add_step(
        "Stage Windows Build",
        "steam_stage_build",
        {"game": "{context.game}"},
    )
    .add_step(
        "Upload Release",
        "ship_to_steam_release",
        {"content_root": "{context.content_root}", "dry_run": True},
    )
)

BUILTIN_WORKFLOWS = {
    "scene_setup": SCENE_SETUP_WORKFLOW,
    "particle_cfd": PARTICLE_CFD_WORKFLOW,
    "ship_web_itch": SHIP_WEB_WORKFLOW,
    "ship_windows_steam_beta": SHIP_STEAM_BETA_WORKFLOW,
    "ship_windows_steam_release": SHIP_STEAM_RELEASE_WORKFLOW,
}
