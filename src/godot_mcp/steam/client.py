"""HTTP client for steam-mcp REST bridge."""

from __future__ import annotations

from typing import Any

import httpx

from godot_mcp.steam.config import steam_mcp_url


def call_steam_tool(tool_name: str, arguments: dict[str, Any] | None = None, timeout: int = 120) -> dict[str, Any]:
    url = f"{steam_mcp_url()}/api/tools/{tool_name}/call"
    try:
        resp = httpx.post(url, json={"arguments": arguments or {}}, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"steam-mcp HTTP {exc.response.status_code}: {exc.response.text}") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Cannot reach steam-mcp at {steam_mcp_url()}: {exc}") from exc

    if not payload.get("success"):
        raise RuntimeError(payload.get("message", "steam-mcp tool call failed"))

    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return {"success": True, "data": data}


def call_steam_publish(operation: str, **kwargs: Any) -> dict[str, Any]:
    return call_steam_tool("steam_publish", {"operation": operation, **kwargs})
