"""Prefab UI card tools for status/list/stats tools (fleet Prefab standard)."""

import asyncio
import logging

from fastmcp import Context
from fastmcp.server.server import ToolResult
from prefab_ui import PrefabApp
from prefab_ui.components import Heading, Row

from godot_mcp.fleet import service as fleet_service
from godot_mcp.itch import service as itch_service
from godot_mcp.services.godot_bridge import find_godot, get_bridge
from godot_mcp.steam import service as steam_service

logger = logging.getLogger("godot-mcp.cards")

_READ_ONLY = {"readonly": True}


async def show_godot_status_card(ctx: Context = None) -> ToolResult:
    """Show Godot engine status as a rich Prefab card.

    ## Return Format
    ToolResult with PrefabApp structured_content; plain text fallback.

    ## Examples
    await show_godot_status_card()
    """
    bridge = get_bridge()
    data = {}
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if result["success"]:
            result = await asyncio.to_thread(bridge.send, "status")
            data = result.get("data", {}) if result["success"] else {}
    else:
        result = await asyncio.to_thread(bridge.send, "status")
        data = result.get("data", {}) if result["success"] else {}

    with PrefabApp(title="Godot Engine") as app:
        Heading("Status")
        if data:
            Row("Version", data.get("godot_version", "unknown"))
            Row("FPS", str(data.get("fps", "N/A")))
            Row("Nodes", str(data.get("node_count", 0)))
            Row("Bridge", "Connected" if bridge.connected else "Disconnected")
        else:
            Row("Bridge", "Not connected — start Godot with the bridge addon")

    plain = (
        f"Godot {data.get('godot_version', 'N/A')} | {data.get('fps', 'N/A')} FPS | {data.get('node_count', 0)} nodes"
    )
    return ToolResult(content=plain, structured_content=app)


async def show_itch_status_card(ctx: Context = None) -> ToolResult:
    """Show itch.io/Butler publishing status as a rich Prefab card.

    ## Return Format
    ToolResult with PrefabApp structured_content; plain text fallback.

    ## Examples
    await show_itch_status_card()
    """
    status = itch_service.itch_status()

    with PrefabApp(title="Itch.io Publisher") as app:
        Heading("Butler")
        Row("Installed", "Yes" if status.get("butler", {}).get("installed") else "No")
        butler_ver = status.get("butler", {}).get("version", "N/A")
        if butler_ver:
            Row("Version", str(butler_ver))
        Row("API Key Set", "Yes" if status.get("auth", {}).get("has_api_key") else "No")
        Heading("Target")
        target = status.get("defaults", {}).get("itch_target", "Not configured")
        Row("Default Slug", target)

    plain = f"Butler: {'OK' if status.get('butler', {}).get('installed') else 'Missing'} | Target: {target}"
    return ToolResult(content=plain, structured_content=app)


async def show_steam_status_card(ctx: Context = None) -> ToolResult:
    """Show Steam publishing readiness as a rich Prefab card.

    ## Return Format
    ToolResult with PrefabApp structured_content; plain text fallback.

    ## Examples
    await show_steam_status_card()
    """
    status = steam_service.steam_status()

    with PrefabApp(title="Steam Publisher") as app:
        Heading("SteamPipe")
        Row("App ID", str(status.get("app_id", "Not set")))
        Row("Depot ID", str(status.get("depot_id", "Not set")))
        Row("Username", status.get("username", "Not set"))
        Row("steamcmd", status.get("steamcmd_path", "Not found"))

    plain = f"App: {status.get('app_id', 'N/A')} | Depot: {status.get('depot_id', 'N/A')} | steamcmd: {'OK' if status.get('steamcmd_path') else 'Missing'}"
    return ToolResult(content=plain, structured_content=app)


async def show_fleet_status_card(ctx: Context = None) -> ToolResult:
    """Show fleet exchange depot status as a rich Prefab card.

    ## Return Format
    ToolResult with PrefabApp structured_content; plain text fallback.

    ## Examples
    await show_fleet_status_card()
    """
    status = fleet_service.fleet_exchange_status()

    with PrefabApp(title="Fleet Exchange") as app:
        Heading("Depot")
        Row("Root", str(status.get("exchange_root", "N/A")))
        Row("Exists", "Yes" if status.get("exchange_exists") else "No")
        Row("Assets", str(status.get("asset_count", 0)))
        Heading("World Labs")
        Row("Mesh Import", "Available" if status.get("godot_mesh_import") else "No")
        Row("Splat Import", "Available" if status.get("godot_splat_import") else "Not yet (Spark viewer)")

    plain = f"Exchange: {status.get('asset_count', 0)} assets | WorldLabs mesh: {'OK' if status.get('godot_mesh_import') else 'N/A'}"
    return ToolResult(content=plain, structured_content=app)


async def show_workflows_card(ctx: Context = None) -> ToolResult:
    """Show built-in workflows as a rich Prefab card.

    ## Return Format
    ToolResult with PrefabApp structured_content; plain text fallback.

    ## Examples
    await show_workflows_card()
    """
    from godot_mcp.workflows.engine import BUILTIN_WORKFLOWS

    with PrefabApp(title="Agentic Workflows") as app:
        Heading("Available")
        for name, wf in BUILTIN_WORKFLOWS.items():
            Row(name, f"{wf.description} ({len(wf.steps)} steps)")

    names = list(BUILTIN_WORKFLOWS.keys())
    plain = f"{len(names)} workflows: {', '.join(names)}"
    return ToolResult(content=plain, structured_content=app)


async def show_viewport_card(ctx: Context = None) -> ToolResult:
    """Capture and show the Godot viewport as a Prefab card.

    Requires the Godot bridge to be connected. Falls back to a hint
    if the bridge is not running.

    ## Return Format
    ToolResult with PrefabApp structured_content; plain text fallback.

    ## Examples
    await show_viewport_card()
    """
    import asyncio

    bridge = get_bridge()
    if not bridge.connected:
        godot = await asyncio.to_thread(find_godot)
        if godot:
            return ToolResult(
                content="Bridge not connected. Launch it with start_bridge().",
                structured_content=PrefabApp(title="Viewport"),
            )
        return ToolResult(
            content="Godot not found. Install and start the bridge.", structured_content=PrefabApp(title="Viewport")
        )

    result = await asyncio.to_thread(bridge.send, "capture_viewport", {}, 30)
    if not result.get("success"):
        with PrefabApp(title="Viewport Capture") as app:
            Heading("Error")
            Row("Details", result.get("error", "Capture failed"))
        return ToolResult(content=result.get("error", "Capture failed"), structured_content=app)

    data = result.get("data", {})
    path = data.get("path", "")
    w = data.get("width", 0)
    h = data.get("height", 0)

    with PrefabApp(title="Godot Viewport") as app:
        Heading(f"Capture {w}x{h}")
        Row("Path", path)
        Row("Resolution", f"{w}x{h}")

    plain = f"Viewport captured: {w}x{h} at {path}"
    return ToolResult(content=plain, structured_content=app)


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, name="show_godot_status_card", app=True)(show_godot_status_card)
    mcp.tool(annotations=_READ_ONLY, name="show_itch_status_card", app=True)(show_itch_status_card)
    mcp.tool(annotations=_READ_ONLY, name="show_steam_status_card", app=True)(show_steam_status_card)
    mcp.tool(annotations=_READ_ONLY, name="show_fleet_status_card", app=True)(show_fleet_status_card)
    mcp.tool(annotations=_READ_ONLY, name="show_workflows_card", app=True)(show_workflows_card)
    mcp.tool(annotations=_READ_ONLY, name="show_viewport_card", app=True)(show_viewport_card)
