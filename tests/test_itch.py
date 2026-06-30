"""Tests for itch.io / Butler integration."""

import pytest

from godot_mcp.itch import butler, config


def test_validate_itch_target_ok():
    assert config.validate_itch_target("myuser/my-game") == "myuser/my-game"


def test_validate_itch_target_rejects_bad_slug():
    with pytest.raises(ValueError, match="user/game"):
        config.validate_itch_target("Bad Slug")


def test_validate_channel_ok():
    assert config.validate_channel("html") == "html"
    assert config.validate_channel("win64-beta") == "win64-beta"


def test_validate_channel_rejects_invalid():
    with pytest.raises(ValueError, match="kebab-case"):
        config.validate_channel("Bad Channel")


def test_redact_secrets():
    raw = "BUTLER_API_KEY=supersecret123 and Authorization: tok123"
    redacted = butler.redact_secrets(raw)
    assert "supersecret123" not in redacted
    assert "tok123" not in redacted
    assert "BUTLER_API_KEY=***" in redacted


def test_validate_upload_dir_must_be_under_build(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    build = repo / "build" / "little-game" / "dodge" / "web"
    build.mkdir(parents=True)
    (build / "index.html").write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(config, "REPO_ROOT", repo)

    resolved = config.validate_upload_dir(build)
    assert resolved == build.resolve()


def test_validate_upload_dir_rejects_outside_roots(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    monkeypatch.setattr(config, "REPO_ROOT", repo)

    with pytest.raises(ValueError, match="under build/"):
        config.validate_upload_dir(outside)


def test_itch_page_url():
    assert config.itch_page_url("alice/cool-game") == "https://alice.itch.io/cool-game"


def test_channel_for_target_defaults(monkeypatch):
    monkeypatch.delenv("ITCH_CHANNEL_WEB", raising=False)
    monkeypatch.delenv("ITCH_CHANNEL_WIN", raising=False)
    assert config.channel_for_target("web") == "html"
    assert config.channel_for_target("windows") == "win"

    monkeypatch.setenv("ITCH_CHANNEL_WEB", "browser")
    assert config.channel_for_target("web") == "browser"
