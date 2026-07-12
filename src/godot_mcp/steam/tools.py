"""MCP tools for Steam publishing via steam-mcp."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from godot_mcp.steam import service

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


async def steam_status(ctx: Context = None) -> dict:
    """Check steam-mcp connectivity, Steam App/Depot IDs, and steamcmd readiness."""
    return service.steam_status()


async def steam_checklist(
    content_root: Annotated[str, Field(description="Depot content folder to validate.", default="")] = "",
    ctx: Context = None,
) -> dict:
    """Return Steam Direct / release checklist from steam-mcp."""
    return service.steam_checklist(content_root)


async def steam_monetization_guide(ctx: Context = None) -> dict:
    """Pricing and revenue guidance (manual Steamworks steps)."""
    return service.steam_monetization_guide()


async def steam_stage_build(
    game: Annotated[str, Field(description="Sample key: dodge, heart, …", default="dodge")] = "dodge",
    project_path: Annotated[str | None, Field(default=None)] = None,
    app_id: Annotated[int | None, Field(default=None)] = None,
    ctx: Context = None,
) -> dict:
    """Export Windows build and stage files to fleet exchange for Steam depot upload."""
    return service.stage_windows_build(game=game, project_path=project_path, app_id=app_id)


async def ship_to_steam_prerelease(
    content_root: Annotated[str, Field(default="")] = "",
    dry_run: Annotated[bool, Field(description="If true, only generate VDF + command.", default=True)] = True,
    ctx: Context = None,
) -> dict:
    """Upload staged build to Steam beta branch via steam-mcp (dry_run default true)."""
    return service.steam_upload_prerelease(content_root, dry_run=dry_run)


async def ship_to_steam_release(
    content_root: Annotated[str, Field(default="")] = "",
    dry_run: Annotated[bool, Field(default=True)] = True,
    ctx: Context = None,
) -> dict:
    """Upload staged build to Steam default (live) branch via steam-mcp."""
    return service.steam_upload_release(content_root, dry_run=dry_run)


async def ship_to_steam(
    game: Annotated[str, Field(default="dodge")] = "dodge",
    project_path: Annotated[str | None, Field(default=None)] = None,
    phase: Annotated[
        str, Field(description="prerelease (beta) or release (default).", default="prerelease")
    ] = "prerelease",
    dry_run: Annotated[bool, Field(default=True)] = True,
    ctx: Context = None,
) -> dict:
    """Export Windows build, stage to exchange, generate VDF, upload via steam-mcp."""
    return service.ship_to_steam(
        game=game,
        project_path=project_path,
        phase=phase,
        dry_run=dry_run,
    )


async def steam_ops(
    operation: Annotated[
        Literal["status", "checklist", "monetization", "stage", "prerelease", "release", "ship"],
        Field(
            description="Steam operation: status (SteamPipe readiness), checklist (release checklist), monetization (pricing guide), stage (export Windows build), prerelease (upload beta branch), release (upload live branch), ship (full pipeline)."
        ),
    ],
    game: Annotated[str | None, Field(default=None, description="Sample key. Used by: stage, ship.")] = None,
    project_path: Annotated[
        str | None, Field(default=None, description="Custom project path. Used by: stage, ship.")
    ] = None,
    app_id: Annotated[int | None, Field(default=None, description="Steam App ID. Used by: stage.")] = None,
    content_root: Annotated[
        str, Field(default="", description="Depot content root. Used by: checklist, prerelease, release.")
    ] = "",
    dry_run: Annotated[
        bool, Field(default=True, description="Dry run (generate VDF only). Used by: prerelease, release, ship.")
    ] = True,
    phase: Annotated[
        str, Field(default="prerelease", description="prerelease or release. Used by: ship.")
    ] = "prerelease",
    ctx: Context = None,
) -> dict:
    """Steam publishing via steam-mcp — consolidated portmanteau.

    ## Return Format
    {"success": bool, ...}

    ## Examples
    await steam_ops(operation="status")
    await steam_ops(operation="stage", game="dodge")
    await steam_ops(operation="prerelease", dry_run=True)
    await steam_ops(operation="ship", game="dodge", phase="release", dry_run=True)
    """
    from godot_mcp.steam import service as s

    match operation:
        case "status":
            return s.steam_status()
        case "checklist":
            return s.steam_checklist(content_root)
        case "monetization":
            return s.steam_monetization_guide()
        case "stage":
            return s.stage_windows_build(game=game or "dodge", project_path=project_path, app_id=app_id)
        case "prerelease":
            return s.steam_upload_prerelease(content_root, dry_run=dry_run)
        case "release":
            return s.steam_upload_release(content_root, dry_run=dry_run)
        case "ship":
            return s.ship_to_steam(game=game or "dodge", project_path=project_path, phase=phase, dry_run=dry_run)
        case _:
            return {"success": False, "error": f"Unknown steam operation: {operation}"}


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.3.0")(steam_status)
    mcp.tool(annotations=_READ_ONLY, version="0.3.0")(steam_checklist)
    mcp.tool(annotations=_READ_ONLY, version="0.3.0")(steam_monetization_guide)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(steam_stage_build)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(ship_to_steam_prerelease)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(ship_to_steam_release)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(ship_to_steam)
    mcp.tool(annotations=_READ_ONLY, version="0.4.0")(steam_ops)
