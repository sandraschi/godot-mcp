"""Fleet exchange depot helpers."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_EXCHANGE = Path("D:/Dev/repos/_exchange")

IMPORT_EXTENSIONS = {".glb", ".gltf", ".obj", ".stl"}


def exchange_root() -> Path:
    raw = os.getenv("FLEET_EXCHANGE_ROOT", str(DEFAULT_EXCHANGE)).strip()
    return Path(raw).resolve()


def worldlabs_dir() -> Path:
    path = exchange_root() / "models" / "worldlabs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def models_dir() -> Path:
    path = exchange_root() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_import_path(path: str | Path) -> Path:
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise ValueError(f"File not found: {resolved}")
    if resolved.suffix.lower() not in IMPORT_EXTENSIONS:
        raise ValueError(f"Unsupported import type: {resolved.suffix}. Use: {', '.join(sorted(IMPORT_EXTENSIONS))}")
    root = exchange_root()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"Import path must be under fleet exchange: {root}")
    return resolved


def list_exchange_assets(limit: int = 100) -> list[dict]:
    root = exchange_root()
    if not root.is_dir():
        return []
    rows: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in IMPORT_EXTENSIONS and ext not in {".csv", ".spz", ".ply"}:
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path.name
        rows.append(
            {
                "path": str(path),
                "relative": str(rel),
                "extension": ext,
                "size_bytes": path.stat().st_size,
            }
        )
        if len(rows) >= limit:
            break
    return sorted(rows, key=lambda r: r["relative"])
