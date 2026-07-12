"""Portmanteau registration tests — verify every operation maps to a real handler.

Prevents the "tool renamed, operation string didn't update" regression pattern.
"""

import inspect

import pytest

from godot_mcp.fleet.tools import fleet_ops
from godot_mcp.itch.tools import itch_ops
from godot_mcp.steam.tools import steam_ops

# Expected operations per portmanteau — update when adding new operations
EXPECTED_OPS = {
    "itch": {"status", "export", "preview", "push", "latest", "ship"},
    "steam": {"status", "checklist", "monetization", "stage", "prerelease", "release", "ship"},
    "fleet": {
        "exchange_status",
        "import",
        "worldlabs_get",
        "worldlabs_stage_mesh",
        "worldlabs_stage_splat",
        "worldlabs_import",
    },
}

# Allowed overlapping operation names (same meaning across domains)
ALLOWED_SHARED = {"status", "ship"}


def _get_code_operations(func) -> set[str]:
    """Extract all `case "op":` strings from a function's source code."""
    src = inspect.getsource(func)
    ops = set()
    for line in src.split("\n"):
        stripped = line.strip()
        if stripped.startswith('case "') and stripped.endswith(":"):
            op = stripped.removeprefix('case "').removesuffix('":')
            ops.add(op)
    return ops


def test_itch_ops_all_operations_have_handlers():
    code = _get_code_operations(itch_ops)
    assert EXPECTED_OPS["itch"] == code, (
        f"itch_ops: expected has {EXPECTED_OPS['itch'] - code}, code has {code - EXPECTED_OPS['itch']}"
    )


def test_steam_ops_all_operations_have_handlers():
    code = _get_code_operations(steam_ops)
    assert EXPECTED_OPS["steam"] == code, (
        f"steam_ops: expected has {EXPECTED_OPS['steam'] - code}, code has {code - EXPECTED_OPS['steam']}"
    )


def test_fleet_ops_all_operations_have_handlers():
    code = _get_code_operations(fleet_ops)
    assert EXPECTED_OPS["fleet"] == code, (
        f"fleet_ops: expected has {EXPECTED_OPS['fleet'] - code}, code has {code - EXPECTED_OPS['fleet']}"
    )


@pytest.mark.asyncio
async def test_itch_ops_invalid_operation_returns_error():
    result = await itch_ops(operation="nonexistent_operation_xyz")
    assert result["success"] is False
    assert "Unknown itch operation" in result["error"]


@pytest.mark.asyncio
async def test_steam_ops_invalid_operation_returns_error():
    result = await steam_ops(operation="nonexistent_operation_xyz")
    assert result["success"] is False
    assert "Unknown steam operation" in result["error"]


@pytest.mark.asyncio
async def test_fleet_ops_invalid_operation_returns_error():
    result = await fleet_ops(operation="nonexistent_operation_xyz")
    assert result["success"] is False
    assert "Unknown fleet operation" in result["error"]


def test_portmanteau_operations_are_consistent_across_domains():
    for name_a, name_b in [("itch", "steam"), ("steam", "fleet"), ("itch", "fleet")]:
        shared = EXPECTED_OPS[name_a] & EXPECTED_OPS[name_b]
        unexpected = shared - ALLOWED_SHARED
        assert not unexpected, f"{name_a}/{name_b} unexpected shared ops: {unexpected}"


def test_code_matches_expected_ops():
    """Ensure EXPECTED_OPS dict stays in sync with source code."""
    for name, func in [("itch", itch_ops), ("steam", steam_ops), ("fleet", fleet_ops)]:
        code = _get_code_operations(func)
        assert EXPECTED_OPS[name] == code, f"EXPECTED_OPS['{name}'] is stale. Update to: {sorted(code)}"
