"""MCP tools that use FastMCP 3.2+ sampling (ctx.sample())."""

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from godot_mcp.sampling.service import SamplingUnavailableError, sample_text

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


async def ai_describe_artifact(
    name: Annotated[str, Field(description="Artifact name to describe.")],
    artifact_type: Annotated[str, Field(description="Type: scene, mesh, material, etc.")],
    features: Annotated[str, Field(description="Key features / details.", default="")] = "",
    ctx: Context = None,
) -> dict:
    """Generate an AI-powered description for an artifact using LLM sampling.

    Uses connected MCP client's LLM to write rich descriptions. Falls back
    gracefully if sampling is unavailable.

    ## Return Format
    {"success": bool, "description": str}

    ## Examples
    await ai_describe_artifact(name="River Rapids", artifact_type="scene", features="turbulent water, foam, rocks")
    """
    prompt = f"Write a concise description for a Godot {artifact_type} artifact named '{name}'."
    if features:
        prompt += f" Features: {features}"
    prompt += "\nDescription:"
    try:
        description = await sample_text(ctx, prompt, system="You are a game asset cataloger.", max_tokens=200)
    except SamplingUnavailableError as exc:
        return {"success": False, "error": str(exc), "artifact_name": name, "artifact_type": artifact_type}
    return {"success": True, "description": description, "artifact_name": name, "artifact_type": artifact_type}


async def ai_generate_gdscript(
    specification: Annotated[str, Field(description="What the GDScript should do.")],
    ctx: Context = None,
) -> dict:
    """Generate GDScript code for a Godot node/behavior using LLM sampling.

    Uses ctx.sample() to generate GDScript from a natural language spec.

    ## Return Format
    {"success": bool, "code": str, "language": "gdscript"}

    ## Examples
    await ai_generate_gdscript(specification="A player movement script with WASD and jump")
    """
    prompt = f"Write GDScript code for Godot 4 that: {specification}\n\n```gdscript"
    try:
        code = await sample_text(
            ctx,
            prompt,
            system="You are a Godot 4 GDScript expert. Output ONLY the code, no explanation.",
            max_tokens=1024,
        )
    except SamplingUnavailableError as exc:
        return {"success": False, "error": str(exc), "language": "gdscript", "specification": specification}
    return {"success": True, "code": code, "language": "gdscript", "specification": specification}


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(ai_describe_artifact)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(ai_generate_gdscript)
