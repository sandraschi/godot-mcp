"""MCP tools for agentic workflow management."""

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from godot_mcp.workflows.engine import BUILTIN_WORKFLOWS

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}

PYTHON_TOOLS = {
    "itch_status",
    "godot_export_release",
    "itch_push_preview",
    "itch_push",
    "itch_latest_version",
    "ship_to_itch",
}


async def workflow_list(ctx: Context = None) -> dict:
    """List all built-in agentic workflows.

    ## Return Format
    {"success": bool, "workflows": [{"name": str, "description": str, "steps": int}]}

    ## Examples
    await workflow_list()
    """
    wfs = [{"name": k, "description": v.description, "steps": len(v.steps)} for k, v in BUILTIN_WORKFLOWS.items()]
    return {"success": True, "workflows": wfs}


async def workflow_run(
    workflow_name: Annotated[str, Field(description="Workflow name: scene_setup, particle_cfd, ship_web_itch.")],
    csv_path: Annotated[str | None, Field(description="CSV path (required for particle_cfd).", default=None)] = None,
    game: Annotated[str | None, Field(description="Sample game for ship_web_itch.", default="dodge")] = None,
    itch_target: Annotated[str | None, Field(description="user/game slug for ship_web_itch.", default=None)] = None,
    channel: Annotated[str | None, Field(description="Butler channel for ship_web_itch.", default="html")] = None,
    ctx: Context = None,
) -> dict:
    """Run a built-in agentic workflow.

    Executes a predefined multi-step workflow, injecting context variables.

    ## Return Format
    {"success": bool, "workflow": str, "steps_completed": int, "results": [...]}

    ## Examples
    await workflow_run(workflow_name="scene_setup")
    await workflow_run(workflow_name="particle_cfd", csv_path="C:/data/flow.csv")
    """
    if workflow_name not in BUILTIN_WORKFLOWS:
        return {"success": False, "error": f"Unknown workflow: {workflow_name}"}

    workflow = BUILTIN_WORKFLOWS[workflow_name]
    context = {}
    if csv_path:
        context["csv_path"] = csv_path
    if game:
        context["game"] = game
    if itch_target:
        context["itch_target"] = itch_target
    if channel:
        context["channel"] = channel

    async def exec_tool(tool: str, params: dict) -> dict:
        from godot_mcp.itch import service as itch_service

        if tool in PYTHON_TOOLS:
            try:
                handlers = {
                    "itch_status": lambda: itch_service.itch_status(),
                    "godot_export_release": lambda: itch_service.godot_export_release_tool(**params),
                    "itch_push_preview": lambda: itch_service.itch_push_preview(**params),
                    "itch_push": lambda: itch_service.itch_push(**params),
                    "itch_latest_version": lambda: itch_service.itch_latest_version(**params),
                    "ship_to_itch": lambda: itch_service.ship_to_itch(**params),
                }
                return handlers[tool]()
            except Exception as e:
                return {"success": False, "error": str(e)}

        try:
            from godot_mcp.services.godot_bridge import get_bridge

            bridge = get_bridge()
            if not bridge.connected:
                bridge.connect()
            action = tool.replace("godot_", "")
            return bridge.send(action, params)
        except Exception as e:
            return {"success": False, "error": str(e)}

    return await workflow.run(exec_tool, inject_context=context)


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(workflow_list)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(workflow_run)
