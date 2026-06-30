"""Tests for fleet exchange and World Labs asset parsing."""

from __future__ import annotations

import pytest

from godot_mcp.fleet import exchange, worldlabs


def test_exchange_root_default(monkeypatch):
    monkeypatch.delenv("FLEET_EXCHANGE_ROOT", raising=False)
    root = exchange.exchange_root()
    assert "exchange" in str(root).lower() or root.name == "_exchange"


def test_validate_import_rejects_outside_exchange(tmp_path, monkeypatch):
    monkeypatch.setenv("FLEET_EXCHANGE_ROOT", str(tmp_path))
    outside = tmp_path.parent / "outside.glb"
    outside.write_bytes(b"glb")
    with pytest.raises(ValueError, match="under fleet exchange"):
        exchange.validate_import_path(outside)


def test_validate_import_accepts_glb_in_exchange(tmp_path, monkeypatch):
    monkeypatch.setenv("FLEET_EXCHANGE_ROOT", str(tmp_path))
    glb = tmp_path / "models" / "test.glb"
    glb.parent.mkdir(parents=True)
    glb.write_bytes(b"fake-glb")
    resolved = exchange.validate_import_path(glb)
    assert resolved == glb.resolve()


def test_list_exchange_assets(tmp_path, monkeypatch):
    monkeypatch.setenv("FLEET_EXCHANGE_ROOT", str(tmp_path))
    (tmp_path / "a.glb").write_bytes(b"x" * 10)
    rows = exchange.list_exchange_assets()
    assert len(rows) == 1
    assert rows[0]["extension"] == ".glb"
    assert rows[0]["size_bytes"] == 10


def test_extract_assets_from_world_payload():
    payload = {
        "world": {
            "assets": {
                "mesh": {"collider_mesh_url": "https://example.com/mesh.glb"},
                "splats": {"spz_urls": {"500k": "https://example.com/splat.spz"}},
                "imagery": {"pano_url": "https://example.com/pano.jpg"},
                "thumbnail_url": "https://example.com/thumb.jpg",
                "caption": "test world",
            }
        }
    }
    assets = worldlabs.extract_assets(payload)
    assert assets["mesh"] == "https://example.com/mesh.glb"
    assert assets["splat_500k"] == "https://example.com/splat.spz"
    assert assets["caption"] == "test world"


def test_extract_assets_prefers_assets_block():
    payload = {
        "world": {
            "_assets": {
                "mesh": "https://cached/mesh.glb",
                "splat_full": "https://cached/full.spz",
            }
        }
    }
    assets = worldlabs.extract_assets(payload)
    assert assets["mesh"] == "https://cached/mesh.glb"
    assert assets["splat_full"] == "https://cached/full.spz"


def test_spark_viewer_url_builds_query():
    assets = {
        "splat_full": "https://cdn/full.spz",
        "splat_500k": "https://cdn/500k.spz",
    }
    url = worldlabs.spark_viewer_url(assets)
    assert url is not None
    assert "spark?" in url
    assert "splat_full=" in url


def test_validate_world_id_rejects_empty():
    with pytest.raises(ValueError):
        worldlabs.validate_world_id("  ")


def test_validate_world_id_accepts_marble_id():
    assert worldlabs.validate_world_id("abc123XYZ") == "abc123XYZ"
