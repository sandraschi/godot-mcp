"""Prefab UI card tools for status/list/stats tools (fleet Prefab standard)."""

import asyncio
import logging
from typing import Annotated

from fastmcp import Context
from fastmcp.server.server import ToolResult
from prefab_ui import PrefabApp
from prefab_ui.components import Heading, Row
from pydantic import Field

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
        Row("Splat Import", "Available (godot_import_splat)")

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


async def show_profile_card(ctx: Context = None) -> ToolResult:
    """Show Godot performance metrics as a rich Prefab card.

    ## Return Format
    ToolResult with PrefabApp structured_content; plain text fallback.

    ## Examples
    await show_profile_card()
    """
    bridge = get_bridge()
    snap = {}
    if bridge.connected:
        result = await asyncio.to_thread(bridge.send, "profile_snapshot")
        snap = result.get("data", {}).get("snapshot", {}) if result["success"] else {}

    with PrefabApp(title="Performance") as app:
        Heading("Frame Timing")
        Row("FPS", f'{snap.get("fps", "N/A"):.1f}' if isinstance(snap.get("fps"), (int, float)) else "N/A")
        Row("Process", f'{snap.get("process_time", 0):.2f} ms')
        Row("Physics", f'{snap.get("physics_time", 0):.2f} ms')
        Heading("Memory")
        Row("Static", f'{snap.get("memory_static", 0) / 1e6:.1f} MB' if snap.get("memory_static") else "N/A")
        Row("Dynamic", f'{snap.get("memory_dynamic", 0) / 1e6:.1f} MB' if snap.get("memory_dynamic") else "N/A")
        Heading("Render")
        Row("Draw Calls", str(snap.get("render_draw_calls", "N/A")))
        Row("Video Mem", f'{snap.get("render_video_mem", 0) / 1e6:.1f} MB' if snap.get("render_video_mem") else "N/A")
        Heading("Physics")
        Row("Active Objects", str(snap.get("physics_active", "N/A")))
        Row("Collision Pairs", str(snap.get("physics_collisions", "N/A")))

    fps = snap.get("fps", "?")
    draw = snap.get("render_draw_calls", "?")
    plain = f"Profile: {fps} FPS | {draw} draw calls | mem {snap.get('memory_static', 0) / 1e6:.0f} MB"
    return ToolResult(content=plain, structured_content=app)


async def show_validate_meshes_card(ctx: Context = None) -> ToolResult:
    """Show mesh validation results as a rich Prefab card.

    ## Return Format
    ToolResult with PrefabApp structured_content; plain text fallback.

    ## Examples
    await show_validate_meshes_card()
    """
    bridge = get_bridge()
    data = {"total_meshes": 0, "corrupt_meshes": 0, "total_issues": 0, "issues": []}
    if bridge.connected:
        result = await asyncio.to_thread(bridge.send, "validate_meshes")
        if result["success"]:
            data = result["data"]

    with PrefabApp(title="Mesh Validation") as app:
        Heading("Summary")
        Row("Total Meshes", str(data.get("total_meshes", 0)))
        c = data.get("corrupt_meshes", 0)
        Row("Corrupt", str(c), color="red" if c > 0 else "green")
        Row("Issues", str(data.get("total_issues", 0)))
        issues = data.get("issues", [])
        if issues:
            Heading("Issues")
            for issue in issues[:8]:
                sev = issue.get("severity", "info")
                Row(issue.get("node", "?"), f"[{sev}] {issue.get('detail', '?')[:60]}")

    plain = f"Meshes: {data.get('total_meshes', 0)} total, {data.get('corrupt_meshes', 0)} corrupt, {data.get('total_issues', 0)} issues"
    return ToolResult(content=plain, structured_content=app)


async def show_state_digest_card(
    node_names: Annotated[list[str] | None, Field(description="Optional node name filter. Omit for all watched nodes.", default=None)] = None,
    ctx: Context = None,
) -> ToolResult:
    """Show structured game state as a rich Prefab card.

    ## Return Format
    ToolResult with PrefabApp structured_content; plain text fallback.

    ## Examples
    await show_state_digest_card()
    await show_state_digest_card(node_names=["Player"])
    """
    bridge = get_bridge()
    nodes = {}
    if bridge.connected:
        params = {"nodes": node_names} if node_names else {}
        result = await asyncio.to_thread(bridge.send, "state_digest", params)
        nodes = result.get("data", {}).get("nodes", {}) if result["success"] else {}

    with PrefabApp(title="Game State") as app:
        Heading(f"Nodes ({len(nodes)})")
        for name, state in nodes.items():
            if "error" in state:
                Row(name, state["error"])
                continue
            parts = []
            if "position" in state:
                p = state["position"]
                parts.append(f"pos({p.get('x',0):.1f},{p.get('y',0):.1f},{p.get('z',0):.1f})")
            if "velocity" in state:
                v = state["velocity"]
                parts.append(f"vel({v.get('x',0):.1f},{v.get('y',0):.1f})")
            if "visible" in state:
                parts.append("visible" if state["visible"] else "hidden")
            if "current_animation" in state:
                parts.append(f"anim:{state['current_animation']}")
            Row(name, " | ".join(parts) if parts else state.get("type", "?"))

    count = len(nodes)
    plain = f"Game State: {count} node{'s' if count != 1 else ''}" + (f" ({', '.join(nodes.keys())})" if count <= 5 else "")
    return ToolResult(content=plain, structured_content=app)


async def show_read_node_card(
    node: Annotated[str, Field(description="Node path or name to inspect.")],
    ctx: Context = None,
) -> ToolResult:
    """Show a single node's properties as a rich Prefab card.

    ## Return Format
    ToolResult with PrefabApp structured_content; plain text fallback.

    ## Examples
    await show_read_node_card(node="Player")
    """
    bridge = get_bridge()
    node_data = {}
    if bridge.connected:
        result = await asyncio.to_thread(bridge.send, "read_node", {"node": node})
        node_data = result.get("data", {}).get("node", {}) if result["success"] else {}

    with PrefabApp(title=f"Node: {node}") as app:
        if not node_data:
            Row("Error", f"Node '{node}' not found")
        else:
            Heading(node_data.get("type", "Node"))
            if "position" in node_data:
                p = node_data["position"]
                Row("Position", f"({p.get('x',0):.2f}, {p.get('y',0):.2f}, {p.get('z',0):.2f})")
            if "rotation_deg" in node_data:
                r = node_data["rotation_deg"]
                Row("Rotation", f"({r.get('x',0):.1f}, {r.get('y',0):.1f}, {r.get('z',0):.1f}) deg")
            if "velocity" in node_data:
                v = node_data["velocity"]
                Row("Velocity", f"({v.get('x',0):.2f}, {v.get('y',0):.2f}, {v.get('z',0):.2f})")
            if "visible" in node_data:
                Row("Visible", "Yes" if node_data["visible"] else "No")
            if "current_animation" in node_data:
                Row("Animation", node_data["current_animation"])
            if "mcp_state" in node_data:
                Row("State", "Custom _mcp_state()")
            children = node_data.get("children", [])
            if children:
                Row("Children", ", ".join(c["name"] for c in children[:6]))
                if len(children) > 6:
                    Row("", f"... and {len(children) - 6} more")

    plain = f"Node {node}: {node_data.get('type', '?')} pos={node_data.get('position', {}).get('x', '?')}"
    return ToolResult(content=plain, structured_content=app)


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, name="show_godot_status_card", app=True)(show_godot_status_card)
    mcp.tool(annotations=_READ_ONLY, name="show_itch_status_card", app=True)(show_itch_status_card)
    mcp.tool(annotations=_READ_ONLY, name="show_steam_status_card", app=True)(show_steam_status_card)
    mcp.tool(annotations=_READ_ONLY, name="show_fleet_status_card", app=True)(show_fleet_status_card)
    mcp.tool(annotations=_READ_ONLY, name="show_workflows_card", app=True)(show_workflows_card)
    mcp.tool(annotations=_READ_ONLY, name="show_viewport_card", app=True)(show_viewport_card)
    mcp.tool(annotations=_READ_ONLY, name="show_profile_card", app=True)(show_profile_card)
    mcp.tool(annotations=_READ_ONLY, name="show_validate_meshes_card", app=True)(show_validate_meshes_card)
    mcp.tool(annotations=_READ_ONLY, name="show_state_digest_card", app=True)(show_state_digest_card)
    mcp.tool(annotations=_READ_ONLY, name="show_read_node_card", app=True)(show_read_node_card)

