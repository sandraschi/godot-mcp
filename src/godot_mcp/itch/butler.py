"""Butler CLI wrapper."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

_SECRET_PATTERNS = (
    re.compile(r"(BUTLER_API_KEY=)(\S+)", re.I),
    re.compile(r"(Authorization:\s*)(\S+)", re.I),
    re.compile(r"(api[_-]?key[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", re.I),
)


@dataclass
class ButlerResult:
    success: bool
    command: list[str]
    stdout: str
    stderr: str
    returncode: int

    def as_dict(self) -> dict:
        return {
            "success": self.success,
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
        }


def redact_secrets(text: str) -> str:
    out = text
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub(r"\1***", out)
    return out


def find_butler() -> Path | None:
    custom = os.getenv("BUTLER_PATH", "").strip()
    if custom:
        path = Path(custom)
        if path.is_file():
            return path
    found = shutil.which("butler") or shutil.which("butler.exe")
    if found:
        return Path(found)
    appdata = os.getenv("APPDATA", "")
    if appdata:
        chosen = Path(appdata) / "itch" / "broth" / "butler" / ".chosen-version"
        if chosen.is_file():
            version = chosen.read_text(encoding="utf-8").strip()
            candidate = Path(appdata) / "itch" / "broth" / "butler" / "versions" / version / "butler.exe"
            if candidate.is_file():
                return candidate
    return None


def run_butler(args: list[str], *, cwd: Path | None = None, timeout: int = 900) -> ButlerResult:
    exe = find_butler()
    if not exe:
        return ButlerResult(
            success=False,
            command=["butler", *args],
            stdout="",
            stderr="butler not found — install from https://itchio.itch.io/butler or set BUTLER_PATH",
            returncode=127,
        )
    env = os.environ.copy()
    cmd = [str(exe), *args]
    proc = subprocess.run(  # noqa: S603 — butler exe resolved by find_butler()
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    stdout = redact_secrets(proc.stdout or "")
    stderr = redact_secrets(proc.stderr or "")
    ok = proc.returncode == 0
    return ButlerResult(success=ok, command=cmd, stdout=stdout, stderr=stderr, returncode=proc.returncode)


def butler_version() -> str | None:
    result = run_butler(["version"], timeout=30)
    if not result.success:
        return None
    line = (result.stdout or result.stderr).strip().splitlines()
    return line[0] if line else None
