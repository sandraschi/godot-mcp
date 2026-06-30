"""Godot MCP Bridge addon installation tools."""

from pathlib import Path
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

BRIDGE_GD = Path(__file__).parent.parent / "bridge" / "mcp_bridge.gd"
PLUGIN_CFG = """[plugin]
name=MCP Bridge
description=TCP server for MCP commands
author=godot-mcp
version=0.1.0
script=mcp_bridge.gd
"""

_READ_ONLY = {"readonly": True}
_MUTATING = {}


def register(mcp: FastMCP):
    @mcp.tool(annotations=_MUTATING)
    async def install_godot_addon(
        project_path: Annotated[
            str, Field(description="Absolute path to the Godot project root (contains project.godot)")
        ],
        ctx: Context = None,
    ) -> dict:
        """Install the Godot MCP bridge addon into a Godot project.

        Copies mcp_bridge.gd and creates plugin.cfg in the project's
        addons/mcp_bridge/ directory. The addon must be registered as an
        Autoload in Godot (Project > Project Settings > Autoload).

        ## Return Format
        {"success": bool, "message": str, "addon_path": str}

        ## Examples
        install_godot_addon(project_path="C:/MyGodotProject")
        """
        project = Path(project_path).resolve()
        addon_dir = project / "addons" / "mcp_bridge"

        if not (project / "project.godot").is_file():
            return {"success": False, "error": f"No project.godot found at {project}", "addon_path": ""}

        if not BRIDGE_GD.is_file():
            return {"success": False, "error": f"Bridge GDScript not found at {BRIDGE_GD}", "addon_path": ""}

        addon_dir.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.copy2(str(BRIDGE_GD), str(addon_dir / "mcp_bridge.gd"))
        (addon_dir / "plugin.cfg").write_text(PLUGIN_CFG, encoding="utf-8")

        msg = f"Addon installed to {addon_dir}. Add as Autoload in Project > Project Settings > Autoload."
        return {"success": True, "message": msg, "addon_path": str(addon_dir)}
