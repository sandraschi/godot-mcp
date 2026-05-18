"""MCP tools for MCPB bundle creation and management."""

from pathlib import Path
from typing import Annotated

from fastmcp import Context
from pydantic import Field

from godot_mcp.mcpb.format import build_bundle

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


async def mcpb_build(
    name: Annotated[str, Field(description="Bundle name.")],
    description: Annotated[str, Field(description="Bundle description.", default="")] = "",
    tool_sequence: Annotated[list[dict], Field(description="List of {tool, params} dicts.")] = [],
    output: Annotated[str, Field(description="Output .mcpb file path.", default="")] = "",
    ctx: Context = None,
) -> dict:
    """Build an MCPB bundle from a tool sequence. This creates a portable .mcpb file.

    ## Return Format
    {"success": bool, "path": str, "manifest": {...}}

    ## Examples
    await mcpb_build(name="My Scene", description="A test scene", tool_sequence=[{"tool": "godot_create_camera", "params": {}}])
    """
    out = Path(output) if output else Path.cwd() / f"{name.lower().replace(' ', '_')}.mcpb"
    manifest = {
        "type": "bundle",
        "name": name,
        "description": description,
        "tools": tool_sequence,
        "tags": [],
    }
    result = build_bundle(manifest, [], out)
    return {"success": True, "path": str(result), "manifest": manifest}


async def mcpb_inspect(
    bundle_path: Annotated[str, Field(description="Path to .mcpb file.")],
    ctx: Context = None,
) -> dict:
    """Inspect the contents of an .mcpb bundle without extracting.

    ## Return Format
    {"success": bool, "manifest": {...}}

    ## Examples
    await mcpb_inspect(bundle_path="my_scene.mcpb")
    """
    bp = Path(bundle_path)
    if not bp.exists():
        return {"success": False, "error": f"File not found: {bundle_path}"}

    import json
    import tarfile

    try:
        with tarfile.open(bp, "r:gz") as tar:
            member = tar.getmember("manifest.json")
            f = tar.extractfile(member)
            manifest = json.loads(f.read())
        return {"success": True, "manifest": manifest, "file_size": bp.stat().st_size}
    except Exception as e:
        return {"success": False, "error": str(e)}


def register(mcp):
    mcp.tool(annotations=_MUTATING, version="0.1.0")(mcpb_build)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(mcpb_inspect)
