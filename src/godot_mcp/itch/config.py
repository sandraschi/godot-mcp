"""Environment configuration for itch.io / Butler integration."""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

ITCH_TARGET_RE = re.compile(r"^[a-z0-9_-]+/[a-z0-9_-]+$")
CHANNEL_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

GAME_SAMPLES: dict[str, str] = {
    "heart": "samples/Heart-Platformer-Godot-4",
    "platformer": "samples/godot-demo-projects/2d/platformer",
    "dodge": "samples/godot-demo-projects/2d/dodge_the_creeps",
    "pong": "samples/godot-demo-projects/2d/pong",
    "procedural": "samples/godot-4-procedural-generation",
    "skelerealms": "samples/skelerealms",
    "vibecode": "samples/vibecode-runner",
}


def default_game() -> str:
    return os.getenv("GODOT_EXPORT_GAME", "dodge").strip() or "dodge"


def default_itch_target() -> str:
    return os.getenv("ITCH_TARGET", "").strip()


def channel_for_target(target: str) -> str:
    target = target.lower()
    if target == "web":
        return os.getenv("ITCH_CHANNEL_WEB", "html").strip() or "html"
    if target == "windows":
        return os.getenv("ITCH_CHANNEL_WIN", "win").strip() or "win"
    raise ValueError(f"Invalid export target: {target}")


def validate_itch_target(value: str) -> str:
    slug = value.strip().lower()
    if not ITCH_TARGET_RE.match(slug):
        raise ValueError("itch_target must look like user/game (lowercase)")
    return slug


def validate_channel(value: str) -> str:
    ch = value.strip().lower()
    if not CHANNEL_RE.match(ch):
        raise ValueError("channel must be kebab-case alphanumeric")
    return ch


def resolve_sample_project(game: str, project_path: str | None = None) -> Path:
    if project_path:
        proj = Path(project_path).resolve()
        if not (proj / "project.godot").is_file():
            raise ValueError(f"No project.godot in {proj}")
        return proj
    key = (game or default_game()).strip().lower()
    rel = GAME_SAMPLES.get(key)
    if not rel:
        known = ", ".join(sorted(GAME_SAMPLES))
        raise ValueError(f"Unknown game '{key}'. Use: {known}")
    proj = (REPO_ROOT / rel).resolve()
    if not (proj / "project.godot").is_file():
        raise ValueError(f"Missing sample project: {proj}")
    return proj


def build_output_paths(game: str, target: str, output: str | None = None) -> tuple[Path, Path]:
    """Return (output_file, upload_directory)."""
    key = (game or default_game()).strip().lower()
    build_root = REPO_ROOT / "build" / "little-game" / key
    if target == "web":
        out_dir = build_root / "web"
        out_file = Path(output).resolve() if output else out_dir / "index.html"
    elif target == "windows":
        out_dir = build_root / "windows"
        out_file = Path(output).resolve() if output else out_dir / f"{key}.exe"
    else:
        raise ValueError("target must be web or windows")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    return out_file, out_dir


def validate_upload_dir(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_dir():
        raise ValueError(f"Upload directory missing: {resolved}")
    allowed_roots = [
        (REPO_ROOT / "build").resolve(),
        (REPO_ROOT / "samples").resolve(),
    ]
    if not any(resolved == root or root in resolved.parents for root in allowed_roots):
        raise ValueError("upload_dir must be under build/ or samples/")
    return resolved


def itch_page_url(itch_target: str) -> str:
    user, game = itch_target.split("/", 1)
    return f"https://{user}.itch.io/{game}"
