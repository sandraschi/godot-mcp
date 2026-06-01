"""Tests for Steam publishing integration."""

from __future__ import annotations

from pathlib import Path

import pytest

from godot_mcp.steam import config, staging


def test_steam_content_root_default(monkeypatch, tmp_path):
    monkeypatch.setenv("FLEET_EXCHANGE_ROOT", str(tmp_path))
    monkeypatch.setenv("STEAM_APP_ID", "1234560")
    root = config.steam_content_root()
    assert root == tmp_path / "steam-builds" / "1234560" / "content"


def test_stage_export_to_steam_content(tmp_path, monkeypatch):
    monkeypatch.setenv("FLEET_EXCHANGE_ROOT", str(tmp_path))
    monkeypatch.setenv("STEAM_APP_ID", "480")

    src = tmp_path / "export"
    src.mkdir()
    (src / "MyGame.exe").write_bytes(b"fake-exe")
    (src / "data.pck").write_bytes(b"pck")

    result = staging.stage_export_to_steam_content(src, clean=True)
    assert result["success"] is True
    assert result["has_windows_exe"] is True
    assert (Path(result["content_root"]) / "MyGame.exe").is_file()


def test_steam_status_without_server(monkeypatch):
    monkeypatch.setenv("STEAM_MCP_URL", "http://127.0.0.1:59999")
    from godot_mcp.steam import service

    status = service.steam_status()
    assert status["success"] is True
    assert "error" in status["publish"] or "error" in status["steamcmd"]
