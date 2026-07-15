"""Godot MCP addon installation tools — bridge addon + community plugin registry."""

import io
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Annotated

import httpx
from fastmcp import Context, FastMCP
from pydantic import Field

logger = logging.getLogger("godot-mcp.addon")

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

# Community plugin registry: {name: {repo, path_in_zip, description}}
# Add new plugins here — the install tool discovers them automatically.
PLUGIN_REGISTRY: dict[str, dict[str, str]] = {
    "dialogic": {
        "repo": "dialogic-godot/dialogic",
        "path_in_zip": "addons/dialogic/",
        "description": "Visual dialogue system for Godot — branching conversations, timelines, characters",
    },
    "godot-behavior-tree": {
        "repo": "viniciusgerevini/godot-behavior-tree",
        "path_in_zip": "addons/godot-behavior-tree/",
        "description": "Behavior tree AI for NPCs — composite, decorator, leaf nodes with GDScript API",
    },
    "gut": {
        "repo": "bitwes/Gut",
        "path_in_zip": "addons/gut/",
        "description": "GDScript unit testing framework — test runner, asserts, mocking, CI-friendly",
    },
    "aseprite-wizard": {
        "repo": "viniciusgerevini/godot-aseprite-wizard",
        "path_in_zip": "addons/AsepriteWizard/",
        "description": "Aseprite sprite sheet importer with auto-reimport on file changes",
    },
    "terrain3d": {
        "repo": "TokisanGames/Terrain3D",
        "path_in_zip": "addons/terrain3d/",
        "description": "High-performance 3D terrain system for Godot 4 — painting, holes, LOD",
    },
    "godot-voxel": {
        "repo": "Zylann/godot_voxel",
        "path_in_zip": "addons/voxel/",
        "description": "Voxel terrain engine — infinite worlds, editable, Minecraft-like block games",
    },
    "godot-xr-tools": {
        "repo": "GodotVR/godot-xr-tools",
        "path_in_zip": "addons/godot-xr-tools/",
        "description": "AR/VR interaction toolkit — grab, teleport, UI, locomotion for XR games",
    },
    "vrm": {
        "repo": "V-Sekai/godot-vrm",
        "path_in_zip": "addons/",
        "description": "VRM avatar loader for Godot 4 — import .vrm with humanoid retargeting, spring bones, MToon shader",
    },
}


async def install_community_plugin(
    plugin_name: str,
    project_path: str,
    ctx: Context = None,
) -> dict:
    """Install a community Godot plugin from GitHub into the project.

    Module-level entry point for programmatic use (not just MCP tool).
    See addon_tools.py's PLUGIN_REGISTRY for available plugins.
    """
    from pathlib import Path

    project = Path(project_path).resolve()
    if not (project / "project.godot").is_file():
        return {"success": False, "error": f"No project.godot found at {project}"}

    entry = PLUGIN_REGISTRY.get(plugin_name)
    if not entry:
        known = ", ".join(sorted(PLUGIN_REGISTRY.keys()))
        return {"success": False, "error": f"Unknown plugin '{plugin_name}'. Known: {known}"}

    repo = entry["repo"]
    path_in_zip = entry["path_in_zip"]
    target_dir = project / "addons" / plugin_name

    archive_url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(archive_url)
            tag = resp.json().get("tag_name", "") if resp.status_code == 200 else ""
            dl_url = (
                f"https://github.com/{repo}/archive/refs/tags/{tag}.zip"
                if tag
                else f"https://github.com/{repo}/archive/refs/heads/main.zip"
            )
            logger.info("Downloading %s from %s", plugin_name, dl_url)
            zip_resp = await client.get(dl_url, timeout=60, follow_redirects=True)
            zip_resp.raise_for_status()
    except Exception as e:
        return {"success": False, "error": f"Failed to download {repo}: {e}"}

    extracted = 0
    try:
        with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as zf:
            prefix = next(
                (n.split("/")[0] for n in zf.namelist() if path_in_zip.rstrip("/") in n and n.count("/") >= 2),
                None,
            )
            if not prefix:
                return {"success": False, "error": f"Could not find addon path '{path_in_zip}' in archive"}
            for name in zf.namelist():
                rel = name.removeprefix(prefix + "/")
                if not rel.startswith(path_in_zip):
                    continue
                dest = target_dir / rel.removeprefix(path_in_zip).lstrip("/")
                if name.endswith("/"):
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(name) as src, open(dest, "wb") as dst:
                        dst.write(src.read())
                        extracted += 1
    except Exception as e:
        return {"success": False, "error": f"Failed to extract plugin: {e}"}

    return {
        "success": True,
        "plugin": plugin_name,
        "addon_path": str(target_dir),
        "files_extracted": extracted,
    }


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
        shutil.copy2(str(BRIDGE_GD), str(addon_dir / "mcp_bridge.gd"))
        (addon_dir / "plugin.cfg").write_text(PLUGIN_CFG, encoding="utf-8")

        msg = f"Addon installed to {addon_dir}. Add as Autoload in Project > Project Settings > Autoload."
        return {"success": True, "message": msg, "addon_path": str(addon_dir)}

    @mcp.tool(annotations=_MUTATING)
    async def install_community_plugin(
        plugin_name: Annotated[
            str,
            Field(
                description="Plugin name from the registry: dialogic, godot-behavior-tree, gut, aseprite-wizard, terrain3d, godot-voxel, godot-xr-tools, vrm",
            ),
        ],
        project_path: Annotated[
            str, Field(description="Absolute path to the Godot project root (contains project.godot)")
        ],
        ctx: Context = None,
    ) -> dict:
        """Download and install a community Godot plugin from GitHub into the project.

        Delegates to the module-level install_community_plugin().
        See docs/godot-ecosystem.md for the full plugin catalog.

        ## Return Format
        {"success": bool, "plugin": str, "addon_path": str, "message": str}

        ## Examples
        install_community_plugin(plugin_name="dialogic", project_path="C:/MyGame")
        install_community_plugin(plugin_name="gut", project_path="C:/MyGame")
        """
        from godot_mcp.tools.addon_tools import install_community_plugin as _install

        return await _install(plugin_name, project_path, ctx)
