"""MCPB — Godot MCP Bundle packaging format.

.mcpb is a tar.gz archive containing:
  manifest.json  - Metadata and tool sequence
  assets/        - Any referenced files (STL, CSV, scripts, textures)
  preview.png    - Optional thumbnail

Usage:
  from godot_mcp.mcpb.format import build_bundle, unpack_bundle
"""

import io
import json
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

MCPB_VERSION = "0.1.0"


def build_bundle(manifest: dict, assets: list[Path], output_path: Path) -> Path:
    """Build a .mcpb bundle from a manifest dict and asset files."""
    manifest["mcpb_version"] = MCPB_VERSION
    manifest["created_at"] = datetime.now().isoformat()

    with tarfile.open(output_path, "w:gz") as tar:
        manifest_bytes = json.dumps(manifest, indent=2, default=str).encode()
        manifest_io = io.BytesIO(manifest_bytes)
        tarinfo = tarfile.TarInfo(name="manifest.json")
        tarinfo.size = len(manifest_bytes)
        tar.addfile(tarinfo, manifest_io)

        for asset_path in assets:
            if asset_path.exists():
                arcname = f"assets/{asset_path.name}"
                tar.add(str(asset_path), arcname=arcname)

    return output_path


def unpack_bundle(bundle_path: Path, output_dir: Path) -> dict[str, Any]:
    """Unpack a .mcpb bundle into a directory. Returns the manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    def safe_extract(member: tarfile.TarInfo, dest: str) -> tarfile.TarInfo | None:
        if ".." in member.name or member.name.startswith("/"):
            return None
        return member

    with tarfile.open(bundle_path, "r:gz") as tar:
        tar.extractall(path=output_dir, filter=safe_extract if hasattr(tarfile, "TarInfo") else None)  # noqa: S202

    manifest_file = output_dir / "manifest.json"
    if not manifest_file.exists():
        raise ValueError("Invalid .mcpb: no manifest.json found")

    manifest = json.loads(manifest_file.read_text())
    return manifest


def create_scene_bundle(name: str, description: str, tool_sequence: list[dict], output_path: Path) -> Path:
    """Create a .mcpb bundle that reproduces a Godot scene via tool calls."""
    manifest = {
        "type": "scene",
        "name": name,
        "description": description,
        "tools": tool_sequence,
        "tags": [],
    }
    return build_bundle(manifest, [], output_path)
