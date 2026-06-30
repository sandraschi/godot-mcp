"""Godot export helpers for sample / custom projects."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from godot_mcp.itch.config import REPO_ROOT, build_output_paths, resolve_sample_project


def _find_godot() -> Path:
    custom = __import__("os").getenv("GODOT_PATH", "").strip()
    if custom:
        path = Path(custom)
        if path.is_file():
            return path
    found = shutil.which("godot") or shutil.which("godot.exe")
    if found:
        return Path(found)
    candidates = [
        Path(r"C:\Program Files\Godot\godot.exe"),
        Path(r"C:\Program Files (x86)\Godot\godot.exe"),
        Path.home() / "Godot" / "godot.exe",
        Path.home() / ".local" / "bin" / "godot.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("godot executable not found — set GODOT_PATH or install Godot")


def ensure_export_presets(project: Path) -> bool:
    dest = project / "export_presets.cfg"
    template = REPO_ROOT / "templates" / "little-game-export_presets.cfg"
    if not template.is_file():
        raise RuntimeError(f"Missing export template: {template}")
    needs_copy = not dest.is_file()
    if dest.is_file():
        existing = dest.read_text(encoding="utf-8", errors="replace")
        if any(
            x in existing for x in ("variant/thread_support", "ensure_cross_origin_isolation_headers", "export_d3d12")
        ):
            needs_copy = True
    if needs_copy:
        shutil.copyfile(template, dest)
    return needs_copy


def ensure_imported(project: Path, godot: Path) -> None:
    if (project / ".godot" / "imported").is_dir():
        return
    subprocess.run(  # noqa: S603 — godot path validated by _find_godot()
        [str(godot), "--path", str(project), "--import"],
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    if not (project / ".godot" / "imported").is_dir():
        raise RuntimeError("Godot import failed — .godot/imported not created")


def export_release(
    *,
    target: str,
    game: str = "dodge",
    project_path: str | None = None,
    output_path: str | None = None,
) -> dict:
    target = target.lower()
    if target not in ("web", "windows"):
        raise ValueError("target must be web or windows")

    project = resolve_sample_project(game, project_path)
    godot = _find_godot()
    presets_applied = ensure_export_presets(project)
    ensure_imported(project, godot)

    out_file, upload_dir = build_output_paths(game, target, output_path)
    preset = "Web" if target == "web" else "Windows Desktop"

    proc = subprocess.run(  # noqa: S603 — godot path validated by _find_godot()
        [str(godot), "--headless", "--path", str(project), "--export-release", preset, str(out_file)],
        capture_output=True,
        text=True,
        check=False,
        timeout=900,
    )
    if not out_file.is_file():
        hint = (proc.stderr or proc.stdout or "export output missing").strip()
        raise RuntimeError(f"Export failed for {preset}. Run install-export-templates. {hint[:500]}")

    return {
        "target": target,
        "game": game,
        "project": str(project),
        "output_file": str(out_file),
        "upload_dir": str(upload_dir),
        "presets_applied": presets_applied,
        "godot": str(godot),
    }
