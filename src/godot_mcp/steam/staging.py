"""Stage Godot exports into fleet exchange for Steam depots."""

from __future__ import annotations

import shutil
from pathlib import Path

from godot_mcp.steam.config import steam_app_id, steam_content_root


def stage_export_to_steam_content(
    upload_dir: str | Path,
    *,
    app_id: int | None = None,
    clean: bool = True,
) -> dict:
    """Copy Godot Windows export folder into STEAM content root."""
    src = Path(upload_dir).resolve()
    if not src.is_dir():
        raise ValueError(f"Upload dir not found: {src}")

    aid = app_id or steam_app_id()
    dest = steam_content_root(aid)
    if clean and dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    copied = 0
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
        copied += 1

    exe_files = list(dest.rglob("*.exe"))
    return {
        "success": True,
        "source": str(src),
        "content_root": str(dest),
        "app_id": aid,
        "items_copied": copied,
        "exe_files": [str(p) for p in exe_files],
        "has_windows_exe": len(exe_files) > 0,
    }
