"""Godot MCP tools — portmanteau registration for FastMCP 3.2.

[RATIONALE] Consolidates 12 Godot engine tools into a single register_all()
entry point. Each module's register() function fires @mcp.tool decorators at
import time for server boot discovery.
"""


def register_all(mcp):
    from godot_mcp.tools.core_tools import register as reg_core

    reg_core(mcp)
