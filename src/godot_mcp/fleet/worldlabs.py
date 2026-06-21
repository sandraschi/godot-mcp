"""World Labs bridge HTTP client (no worldlabs-mcp package dependency)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import httpx

WORLD_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{6,}$")


def bridge_base_url() -> str:
    return os.getenv("WORLDLABS_BRIDGE_URL", "http://127.0.0.1:10865").rstrip("/")


def web_base_url() -> str:
    return os.getenv("WORLDLABS_WEB_URL", "http://127.0.0.1:10864").rstrip("/")


def validate_world_id(world_id: str) -> str:
    wid = world_id.strip()
    if not WORLD_ID_RE.match(wid):
        raise ValueError("world_id must be alphanumeric (Marble world id)")
    return wid


def _http_json(url: str, timeout: int = 60) -> dict[str, Any]:
    try:
        resp = httpx.get(url, headers={"Accept": "application/json"}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"HTTP {exc.response.status_code} from {url}: {exc.response.text}") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Cannot reach World Labs bridge at {bridge_base_url()}: {exc}") from exc


def extract_assets(world_payload: dict[str, Any]) -> dict[str, str | None]:
    """Mirror worldlabs-mcp _extract_assets shape."""
    world = world_payload.get("world", world_payload)
    assets = world.get("assets", {})
    if world.get("_assets"):
        return dict(world["_assets"])
    spz = assets.get("splats", {}).get("spz_urls", {})
    return {
        "splat_100k": spz.get("100k"),
        "splat_500k": spz.get("500k"),
        "splat_full": spz.get("full_res"),
        "mesh": assets.get("mesh", {}).get("collider_mesh_url"),
        "panorama": assets.get("imagery", {}).get("pano_url"),
        "thumbnail": assets.get("thumbnail_url"),
        "caption": assets.get("caption"),
    }


def fetch_world(world_id: str) -> dict[str, Any]:
    wid = validate_world_id(world_id)
    data = _http_json(f"{bridge_base_url()}/api/worlds/{wid}")
    assets = extract_assets(data)
    world = data.get("world", data)
    return {
        "success": True,
        "world_id": wid,
        "world": world,
        "assets": assets,
        "spark_viewer_url": spark_viewer_url(assets),
    }


def spark_viewer_url(assets: dict[str, str | None]) -> str | None:
    full = assets.get("splat_full") or assets.get("splat_500k") or assets.get("splat_100k")
    if not full:
        return None

    params = {}
    if assets.get("splat_full"):
        params["splat_full"] = assets["splat_full"]
    if assets.get("splat_500k"):
        params["splat_500k"] = assets["splat_500k"]
    if assets.get("splat_100k"):
        params["splat_100k"] = assets["splat_100k"]
    import urllib.parse
    query = urllib.parse.urlencode(params)
    return f"{web_base_url()}/spark?{query}"


def download_url(url: str, dest_path: str | Path, timeout: int = 180) -> Path:
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, headers={"User-Agent": "godot-mcp-fleet/0.2.1"}, follow_redirects=True)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Download failed: {exc}") from exc
    if dest.stat().st_size == 0:
        raise RuntimeError(f"Downloaded empty file: {dest}")
    return dest.resolve()
