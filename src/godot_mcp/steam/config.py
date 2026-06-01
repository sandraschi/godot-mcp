"""Steam publishing configuration."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EXCHANGE = Path("D:/Dev/repos/_exchange")


def steam_mcp_url() -> str:
    return os.getenv("STEAM_MCP_URL", "http://127.0.0.1:11020").rstrip("/")


def steam_app_id() -> int:
    raw = os.getenv("STEAM_APP_ID", "").strip()
    return int(raw) if raw else 0


def steam_depot_id() -> int:
    raw = os.getenv("STEAM_DEPOT_ID", "").strip()
    return int(raw) if raw else 0


def exchange_root() -> Path:
    return Path(os.getenv("FLEET_EXCHANGE_ROOT", str(DEFAULT_EXCHANGE))).resolve()


def steam_content_root(app_id: int | None = None) -> Path:
    override = os.getenv("STEAM_CONTENT_ROOT", "").strip()
    if override:
        return Path(override).resolve()
    aid = app_id or steam_app_id()
    if not aid:
        return exchange_root() / "steam-builds" / "content"
    return exchange_root() / "steam-builds" / str(aid) / "content"


def default_game() -> str:
    return os.getenv("GODOT_EXPORT_GAME", "dodge").strip() or "dodge"
