"""HTTP client for steam-mcp REST bridge."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from godot_mcp.steam.config import steam_mcp_url


def call_steam_tool(tool_name: str, arguments: dict[str, Any] | None = None, timeout: int = 120) -> dict[str, Any]:
    url = f"{steam_mcp_url()}/api/tools/{tool_name}/call"
    body = json.dumps({"arguments": arguments or {}}).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"steam-mcp HTTP {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Cannot reach steam-mcp at {steam_mcp_url()}: {exc.reason}") from exc

    if not payload.get("success"):
        raise RuntimeError(payload.get("message", "steam-mcp tool call failed"))

    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return {"success": True, "data": data}


def call_steam_publish(operation: str, **kwargs: Any) -> dict[str, Any]:
    return call_steam_tool("steam_publish", {"operation": operation, **kwargs})
