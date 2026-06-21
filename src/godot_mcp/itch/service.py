"""itch.io publish orchestration."""

from __future__ import annotations

import os
from typing import Any

import httpx

from godot_mcp.itch import butler, export
from godot_mcp.itch.config import (
    channel_for_target,
    default_game,
    default_itch_target,
    itch_page_url,
    validate_channel,
    validate_itch_target,
    validate_upload_dir,
)

_LAST_SHIP: dict[str, Any] = {}


def get_last_ship() -> dict[str, Any]:
    return dict(_LAST_SHIP)


def _record_ship(payload: dict[str, Any]) -> None:
    global _LAST_SHIP
    _LAST_SHIP = payload


def itch_status() -> dict:
    exe = butler.find_butler()
    api_key_set = bool(os.getenv("BUTLER_API_KEY", "").strip())
    target = default_itch_target()
    return {
        "success": True,
        "butler": {
            "found": exe is not None,
            "path": str(exe) if exe else "",
            "version": butler.butler_version() if exe else None,
        },
        "auth": {
            "api_key_set": api_key_set,
            "hint": "Set BUTLER_API_KEY from itch.io → Account → API keys (never commit it).",
        },
        "defaults": {
            "game": default_game(),
            "itch_target": target,
            "channel_web": channel_for_target("web"),
            "channel_windows": channel_for_target("windows"),
        },
        "last_ship": get_last_ship(),
        "docs": "mcp-central-docs/docs/gamedev/ITCH_IO_PLATFORM.md",
    }


def godot_export_release_tool(
    target: str = "web",
    game: str | None = None,
    project_path: str | None = None,
    output_path: str | None = None,
) -> dict:
    try:
        data = export.export_release(
            target=target,
            game=game or default_game(),
            project_path=project_path,
            output_path=output_path,
        )
        return {"success": True, "data": data}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def itch_push_preview(
    upload_dir: str,
    itch_target: str | None = None,
    channel: str | None = None,
) -> dict:
    try:
        target_slug = validate_itch_target(itch_target or default_itch_target())
        if not target_slug:
            raise ValueError("itch_target required — set ITCH_TARGET or pass itch_target")
        ch = validate_channel(channel or "html")
        directory = validate_upload_dir(__import__("pathlib").Path(upload_dir))
        ref = f"{target_slug}:{ch}"
        result = butler.run_butler(["push-preview", str(directory), ref])
        return {
            "success": result.success,
            "data": {
                "upload_dir": str(directory),
                "itch_ref": ref,
                "page_url": itch_page_url(target_slug),
                **result.as_dict(),
            },
            "error": None if result.success else result.stderr or "push-preview failed",
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def itch_push(
    upload_dir: str,
    itch_target: str | None = None,
    channel: str | None = None,
    hidden: bool = False,
) -> dict:
    try:
        target_slug = validate_itch_target(itch_target or default_itch_target())
        if not target_slug:
            raise ValueError("itch_target required — set ITCH_TARGET or pass itch_target")
        ch = validate_channel(channel or "html")
        directory = validate_upload_dir(__import__("pathlib").Path(upload_dir))
        ref = f"{target_slug}:{ch}"
        args = ["push"] + (["--hidden"] if hidden else []) + [str(directory), ref]
        result = butler.run_butler(args)
        payload = {
            "upload_dir": str(directory),
            "itch_ref": ref,
            "page_url": itch_page_url(target_slug),
            **result.as_dict(),
        }
        if result.success:
            _record_ship({"itch_ref": ref, "upload_dir": str(directory), "page_url": itch_page_url(target_slug)})
        return {
            "success": result.success,
            "data": payload,
            "error": None if result.success else result.stderr or "push failed",
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def itch_latest_version(itch_target: str | None = None, channel: str | None = None) -> dict:
    try:
        target_slug = validate_itch_target(itch_target or default_itch_target())
        if not target_slug:
            raise ValueError("itch_target required")
        ch = validate_channel(channel or channel_for_target("web"))
        import urllib.parse
        query = urllib.parse.urlencode({"target": target_slug, "channel_name": ch})
        url = f"https://api.itch.io/wharf/latest?{query}"
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        return {"success": True, "data": {"url": url, "raw": resp.text}}
    except httpx.HTTPStatusError as exc:
        return {"success": False, "error": f"HTTP {exc.response.status_code}: {exc.response.text}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def ship_to_itch(
    target: str = "web",
    game: str | None = None,
    project_path: str | None = None,
    itch_target: str | None = None,
    channel: str | None = None,
    preview: bool = True,
    push: bool = True,
    hidden: bool = False,
) -> dict:
    export_result = godot_export_release_tool(
        target=target,
        game=game,
        project_path=project_path,
    )
    if not export_result.get("success"):
        return export_result

    upload_dir = export_result["data"]["upload_dir"]
    ch = channel or channel_for_target(target)
    out: dict[str, Any] = {"success": True, "export": export_result["data"], "preview": None, "push": None}

    if preview:
        out["preview"] = itch_push_preview(upload_dir, itch_target=itch_target, channel=ch)
        if not out["preview"].get("success"):
            out["success"] = False
            out["error"] = out["preview"].get("error")
            return out

    if push:
        out["push"] = itch_push(upload_dir, itch_target=itch_target, channel=ch, hidden=hidden)
        if not out["push"].get("success"):
            out["success"] = False
            out["error"] = out["push"].get("error")
            return out

    slug = validate_itch_target(itch_target or default_itch_target())
    if slug:
        out["page_url"] = itch_page_url(slug)
    _record_ship(
        {
            "target": target,
            "game": game or default_game(),
            "upload_dir": upload_dir,
            "itch_target": slug,
            "channel": ch,
            "page_url": out.get("page_url"),
        }
    )
    return out
