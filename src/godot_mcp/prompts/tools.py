"""MCP tools for prompt template management."""

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from godot_mcp.prompts.templates import get_prompt, list_prompts
from godot_mcp.sampling.service import sample_text

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


async def prompt_list(ctx: Context = None) -> dict:
    """List available prompt templates.

    ## Return Format
    {"success": bool, "prompts": [...]}
    """
    prompts = list_prompts()
    return {"success": True, "prompts": [p.model_dump() for p in prompts]}


async def prompt_execute(
    prompt_id: Annotated[str, Field(description="Prompt template ID.")],
    params: Annotated[dict, Field(description="Parameter values for the template.", default={})] = {},
    ctx: Context = None,
) -> dict:
    """Execute a prompt template with given parameters and return the LLM response.

    Uses ctx.sample() for the LLM call.

    ## Return Format
    {"success": bool, "prompt": str, "response": str}
    """
    prompt = get_prompt(prompt_id)
    if not prompt:
        return {"success": False, "error": f"Unknown prompt: {prompt_id}"}

    user_message = prompt.user_prompt_template
    for k, v in params.items():
        user_message = user_message.replace("{" + k + "}", str(v))

    response = await sample_text(ctx, user_message, system=prompt.system_prompt, max_tokens=1024)
    return {"success": True, "prompt": prompt_id, "response": response}


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(prompt_list)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(prompt_execute)
