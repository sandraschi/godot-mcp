"""Steam publishing orchestration via steam-mcp."""

from __future__ import annotations

from typing import Any

from godot_mcp.itch import export as itch_export
from godot_mcp.steam import client, config, staging

_LAST_SHIP: dict[str, Any] = {}


def get_last_ship() -> dict[str, Any]:
    return dict(_LAST_SHIP)


def _record_ship(payload: dict[str, Any]) -> None:
    global _LAST_SHIP
    _LAST_SHIP = payload


def steam_status() -> dict[str, Any]:
    try:
        pub = client.call_steam_publish("status")
    except Exception as exc:
        pub = {"error": str(exc)}
    try:
        cmd = client.call_steam_tool("steam_system", {"operation": "steamcmd_status"})
    except Exception as exc:
        cmd = {"error": str(exc)}

    return {
        "success": True,
        "steam_mcp_url": config.steam_mcp_url(),
        "app_id": config.steam_app_id(),
        "depot_id": config.steam_depot_id(),
        "content_root": str(config.steam_content_root()),
        "publish": pub,
        "steamcmd": cmd,
        "docs": "mcp-central-docs/docs/gamedev/STEAM_PUBLISHING.md",
        "last_ship": get_last_ship(),
    }


def steam_checklist(content_root: str = "") -> dict[str, Any]:
    try:
        return client.call_steam_publish(
            "checklist",
            content_root=content_root or str(config.steam_content_root()),
        )
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def steam_monetization_guide() -> dict[str, Any]:
    try:
        return client.call_steam_publish("monetization")
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def stage_windows_build(
    game: str | None = None,
    project_path: str | None = None,
    app_id: int | None = None,
) -> dict[str, Any]:
    try:
        exported = itch_export.export_release(
            target="windows",
            game=game or config.default_game(),
            project_path=project_path,
        )
        staged = staging.stage_export_to_steam_content(
            exported["upload_dir"],
            app_id=app_id,
            clean=True,
        )
        validation = client.call_steam_publish(
            "validate_build",
            content_root=staged["content_root"],
        )
        return {
            "success": True,
            "export": exported,
            "stage": staged,
            "validation": validation,
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def steam_upload_prerelease(
    content_root: str = "",
    dry_run: bool = True,
) -> dict[str, Any]:
    root = content_root or str(config.steam_content_root())
    try:
        result = client.call_steam_publish("upload_prerelease", content_root=root, dry_run=dry_run)
        _record_ship({"phase": "prerelease", "content_root": root, "dry_run": dry_run, "result": result})
        return {"success": result.get("success", False), "data": result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def steam_upload_release(
    content_root: str = "",
    dry_run: bool = True,
) -> dict[str, Any]:
    root = content_root or str(config.steam_content_root())
    try:
        result = client.call_steam_publish("upload_release", content_root=root, dry_run=dry_run)
        _record_ship({"phase": "release", "content_root": root, "dry_run": dry_run, "result": result})
        return {"success": result.get("success", False), "data": result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def ship_to_steam(
    *,
    game: str | None = None,
    project_path: str | None = None,
    phase: str = "prerelease",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Export Windows build, stage to exchange, generate VDF, upload via steam-mcp."""
    staged = stage_windows_build(game=game, project_path=project_path)
    if not staged.get("success"):
        return staged

    content_root = staged["stage"]["content_root"]
    if phase == "release":
        upload = steam_upload_release(content_root, dry_run=dry_run)
    else:
        upload = steam_upload_prerelease(content_root, dry_run=dry_run)

    payload = {
        "success": upload.get("success", False),
        "phase": phase,
        "export": staged.get("export"),
        "stage": staged.get("stage"),
        "validation": staged.get("validation"),
        "upload": upload,
    }
    _record_ship(payload)
    return payload
