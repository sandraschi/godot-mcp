"""MCP tools for agentic workflow management."""

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from godot_mcp.workflows.engine import BUILTIN_WORKFLOWS

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


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
    workflow_name: Annotated[str, Field(description="Workflow name: scene_setup, particle_cfd.")],
    csv_path: Annotated[str | None, Field(description="CSV path (required for particle_cfd).", default=None)] = None,
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

    async def exec_tool(tool: str, params: dict) -> dict:
        bridge = None
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
