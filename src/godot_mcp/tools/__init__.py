"""Godot MCP tools — portmanteau registration for FastMCP 3.2.

[RATIONALE] Consolidates all tool modules into a single register_all()
entry point. Each module's register() function fires @mcp.tool decorators at
import time for server boot discovery.
"""


def register_all(mcp):
    from godot_mcp.artifacts.tools import register as reg_artifacts
    from godot_mcp.mcp_bridge.tools import register as reg_bridge
    from godot_mcp.mcpb.tools import register as reg_mcpb
    from godot_mcp.prefabs.tools import register as reg_prefabs
    from godot_mcp.prompts.tools import register as reg_prompts
    from godot_mcp.sampling.tools import register as reg_sampling
    from godot_mcp.tools.core_tools import register as reg_core
    from godot_mcp.workflows.tools import register as reg_workflows

    reg_core(mcp)
    reg_artifacts(mcp)
    reg_sampling(mcp)
    reg_workflows(mcp)
    reg_prefabs(mcp)
    reg_prompts(mcp)
    reg_bridge(mcp)
    reg_mcpb(mcp)
