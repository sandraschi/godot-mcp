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

BUILTIN_WORKFLOWS = {
    "scene_setup": SCENE_SETUP_WORKFLOW,
    "particle_cfd": PARTICLE_CFD_WORKFLOW,
}
