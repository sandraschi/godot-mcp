"""Plugin install E2E test — install a community plugin into a temp Godot project.

Requires network access to GitHub. Marked @pytest.mark.slow.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from godot_mcp.tools.addon_tools import PLUGIN_REGISTRY, install_community_plugin


@pytest.fixture
def temp_godot_project():
    """Create a temporary Godot project with a minimal project.godot."""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "project.godot").write_text('[application]\nconfig/name="test"\n', encoding="utf-8")
    (tmp / "scripts").mkdir()
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_install_gut_plugin(temp_godot_project):
    """Install GUT plugin from GitHub into a temp project."""
    result = await install_community_plugin("gut", str(temp_godot_project))
    assert result["success"], f"GUT install failed: {result.get('error')}"
    gut_dir = temp_godot_project / "addons" / "gut"
    assert gut_dir.is_dir(), "GUT addon directory was not created"
    assert any(gut_dir.iterdir()), "GUT addon directory is empty"
    assert result["plugin"] == "gut"
    assert result["addon_path"] == str(gut_dir)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_install_unknown_plugin_fails(temp_godot_project):
    """Installing a non-existent plugin returns a helpful error."""
    result = await install_community_plugin("this-plugin-definitely-does-not-exist-12345", str(temp_godot_project))
    assert result["success"] is False
    assert "Unknown plugin" in result["error"]


@pytest.mark.slow
@pytest.mark.asyncio
async def test_plugin_registry_has_required_entries():
    """The plugin registry must have at minimum: gut, dialogic, aseprite-wizard."""
    required = {"gut", "dialogic", "aseprite-wizard"}
    assert required.issubset(PLUGIN_REGISTRY.keys()), (
        f"Missing required plugins: {required - set(PLUGIN_REGISTRY.keys())}"
    )


@pytest.mark.asyncio
async def test_install_missing_project_fails():
    """Installing into a nonexistent project returns a helpful error."""
    result = await install_community_plugin("gut", "/nonexistent/path")
    assert result["success"] is False
    assert "project.godot" in result["error"]


@pytest.mark.asyncio
async def test_plugin_registry_entries_have_required_fields():
    """Every plugin registry entry must have repo and path_in_zip."""
    for name, entry in PLUGIN_REGISTRY.items():
        assert "repo" in entry, f"{name} missing 'repo'"
        assert "path_in_zip" in entry, f"{name} missing 'path_in_zip'"
        assert "/" in entry["repo"], f"{name} repo should be 'user/repo' format"
