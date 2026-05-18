"""MCP tools for applying prefab templates."""

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from godot_mcp.prefabs.catalog import get_prefab, list_prefabs

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


async def prefab_list(
    category: Annotated[
        str | None, Field(description="Filter by category: lighting, camera, particles, materials.", default=None)
    ] = None,
    ctx: Context = None,
) -> dict:
    """List available prefab templates, optionally filtered by category.

    ## Return Format
    {"success": bool, "prefabs": [...]}

    ## Examples
    await prefab_list()
    await prefab_list(category="lighting")
    """
    prefabs = list_prefabs(category)
    return {"success": True, "prefabs": [p.model_dump() for p in prefabs]}


async def prefab_apply(
    prefab_id: Annotated[str, Field(description="Prefab ID to apply.")],
    params: Annotated[dict, Field(description="Parameter overrides as dict.", default={})] = {},
    ctx: Context = None,
) -> dict:
    """Apply a prefab template, executing its tool sequence with given parameters.

    ## Return Format
    {"success": bool, "prefab": str, "results": [...]}

    ## Examples
    await prefab_apply(prefab_id="standard_lighting", params={"intensity": 2.0})
    """
    prefab = get_prefab(prefab_id)
    if not prefab:
        return {"success": False, "error": f"Unknown prefab: {prefab_id}"}

    from godot_mcp.services.godot_bridge import get_bridge

    bridge = get_bridge()
    if not bridge.connected:
        bridge.connect()

    results = []
    for step in prefab.tools:
        tool = step["tool"]
        step_params = dict(step["params"])
        for k, v in step_params.items():
            if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                key = v[1:-1]
                step_params[k] = params.get(key, v)
        action = tool.replace("godot_", "")
        result = bridge.send(action, step_params)
        results.append({"tool": tool, "result": result})

    return {"success": True, "prefab": prefab_id, "results": results}


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(prefab_list)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(prefab_apply)
