"""MCP tools for itch.io / Butler publishing."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from godot_mcp.itch import service

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


async def itch_status(ctx: Context = None) -> dict:
    """Check Butler install, API key env, and default itch.io slug.

    ## Return Format
    {"success": bool, "butler": {...}, "auth": {...}, "defaults": {...}}

    ## Examples
    await itch_status()
    """
    return service.itch_status()


async def godot_export_release(
    target: Annotated[str, Field(description="Export target: web or windows.", default="web")] = "web",
    game: Annotated[str, Field(description="Sample key: dodge, heart, platformer, …", default="dodge")] = "dodge",
    project_path: Annotated[
        str | None, Field(description="Optional custom Godot project directory.", default=None)
    ] = None,
    output_path: Annotated[str | None, Field(description="Optional output file path.", default=None)] = None,
    ctx: Context = None,
) -> dict:
    """Export a Godot sample or custom project for itch.io (Web or Windows).

    ## Examples
    await godot_export_release(target="web", game="dodge")
    """
    return service.godot_export_release_tool(
        target=target,
        game=game,
        project_path=project_path,
        output_path=output_path,
    )


async def itch_push_preview(
    upload_dir: Annotated[str, Field(description="Directory to upload (export output folder).")],
    itch_target: Annotated[
        str | None, Field(description="Project slug user/game. Defaults to ITCH_TARGET env.", default=None)
    ] = None,
    channel: Annotated[str | None, Field(description="Butler channel name, e.g. html or win.", default=None)] = None,
    ctx: Context = None,
) -> dict:
    """Preview Butler push diff (NEW/MODIFIED/DELETED) before uploading.

    ## Examples
    await itch_push_preview(upload_dir="D:/Dev/repos/godot-mcp/build/little-game/dodge/web")
    """
    return service.itch_push_preview(upload_dir, itch_target=itch_target, channel=channel)


async def itch_push(
    upload_dir: Annotated[str, Field(description="Directory to upload.")],
    itch_target: Annotated[str | None, Field(description="Project slug user/game.", default=None)] = None,
    channel: Annotated[str | None, Field(description="Butler channel name.", default=None)] = None,
    hidden: Annotated[bool, Field(description="Hidden channel on first push.", default=False)] = False,
    ctx: Context = None,
) -> dict:
    """Upload a build directory to itch.io via Butler push.

    ## Examples
    await itch_push(upload_dir="...", itch_target="you/my-game", channel="html")
    """
    return service.itch_push(upload_dir, itch_target=itch_target, channel=channel, hidden=hidden)


async def itch_latest_version(
    itch_target: Annotated[str | None, Field(default=None)] = None,
    channel: Annotated[str | None, Field(default=None)] = None,
    ctx: Context = None,
) -> dict:
    """Query api.itch.io/wharf/latest for the newest build version on a channel."""
    return service.itch_latest_version(itch_target=itch_target, channel=channel)


async def ship_to_itch(
    target: Annotated[str, Field(description="web or windows", default="web")] = "web",
    game: Annotated[str, Field(default="dodge")] = "dodge",
    project_path: Annotated[str | None, Field(default=None)] = None,
    itch_target: Annotated[str | None, Field(default=None)] = None,
    channel: Annotated[str | None, Field(default=None)] = None,
    preview: Annotated[bool, Field(default=True)] = True,
    push: Annotated[bool, Field(default=True)] = True,
    hidden: Annotated[bool, Field(default=False)] = False,
    ctx: Context = None,
) -> dict:
    """Export Godot build, optionally preview and push to itch.io in one flow.

    ## Examples
    await ship_to_itch(target="web", game="dodge", itch_target="you/my-game", channel="html")
    """
    return service.ship_to_itch(
        target=target,
        game=game,
        project_path=project_path,
        itch_target=itch_target,
        channel=channel,
        preview=preview,
        push=push,
        hidden=hidden,
    )


async def itch_ops(
    operation: Annotated[
        Literal["status", "export", "preview", "push", "latest", "ship"],
        Field(
            description="itch.io operation: status (check Butler), export (export project), preview (Butler diff), push (upload), latest (check version), ship (export + preview + push)."
        ),
    ],
    target: Annotated[
        str | None, Field(default=None, description="Export target: web or windows. Used by: export, ship.")
    ] = None,
    game: Annotated[
        str | None, Field(default=None, description="Sample key: dodge, heart. Used by: export, ship.")
    ] = None,
    project_path: Annotated[
        str | None, Field(default=None, description="Custom project path. Used by: export, ship.")
    ] = None,
    upload_dir: Annotated[
        str | None, Field(default=None, description="Directory to upload. Used by: preview, push.")
    ] = None,
    itch_target: Annotated[
        str | None, Field(default=None, description="user/game slug. Used by: preview, push, ship.")
    ] = None,
    channel: Annotated[
        str | None, Field(default=None, description="Butler channel: html, win. Used by: preview, push, ship.")
    ] = None,
    hidden: Annotated[bool, Field(default=False, description="Hidden channel. Used by: push.")] = False,
    preview: Annotated[bool, Field(default=True, description="Preview before push. Used by: ship.")] = True,
    do_push: Annotated[bool, Field(default=True, description="Push after preview. Used by: ship.")] = True,
    output_path: Annotated[
        str | None, Field(default=None, description="Optional output path. Used by: export.")
    ] = None,
    ctx: Context = None,
) -> dict:
    """itch.io publishing — consolidated portmanteau for Butler operations.

    ## Return Format
    {"success": bool, ...}

    ## Examples
    await itch_ops(operation="status")
    await itch_ops(operation="export", target="web", game="dodge")
    await itch_ops(operation="push", upload_dir="build/dodge/web", itch_target="user/game")
    await itch_ops(operation="ship", target="web", game="dodge", itch_target="user/game")
    """
    from godot_mcp.itch import service as s

    match operation:
        case "status":
            return s.itch_status()
        case "export":
            return s.godot_export_release_tool(
                target=target or "web", game=game or "dodge", project_path=project_path, output_path=output_path
            )
        case "preview":
            return s.itch_push_preview(upload_dir or "", itch_target=itch_target, channel=channel)
        case "push":
            return s.itch_push(upload_dir or "", itch_target=itch_target, channel=channel, hidden=hidden)
        case "latest":
            return s.itch_latest_version(itch_target=itch_target, channel=channel)
        case "ship":
            return s.ship_to_itch(
                target=target or "web",
                game=game or "dodge",
                project_path=project_path,
                itch_target=itch_target,
                channel=channel,
                preview=preview,
                push=do_push,
                hidden=hidden,
            )
        case _:
            return {"success": False, "error": f"Unknown itch operation: {operation}"}


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.2.1")(itch_status)
    mcp.tool(annotations=_MUTATING, version="0.2.1")(godot_export_release)
    mcp.tool(annotations=_READ_ONLY, version="0.2.1")(itch_push_preview)
    mcp.tool(annotations=_MUTATING, version="0.2.1")(itch_push)
    mcp.tool(annotations=_READ_ONLY, version="0.2.1")(itch_latest_version)
    mcp.tool(annotations=_MUTATING, version="0.2.1")(ship_to_itch)
    mcp.tool(annotations=_READ_ONLY, version="0.4.0")(itch_ops)
