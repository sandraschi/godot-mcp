"""FastMCP 3.2+ sampling integration for godot-mcp.

Enables tools to make LLM calls via ctx.sample() for autonomous
reasoning, content generation, and intelligent orchestration.
"""

import logging

logger = logging.getLogger("godot-mcp.sampling")


async def sample_text(ctx, prompt: str, system: str | None = None, max_tokens: int = 512) -> str:
    """Use ctx.sample() to generate text via the connected MCP client's LLM.

    Falls back gracefully if sampling is not available.
    """
    if ctx is None or not hasattr(ctx, "sample"):
        logger.warning("ctx.sample() not available — no MCP client connected")
        return "[Sampling unavailable]"
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        result = await ctx.sample(
            messages=messages,
            max_tokens=max_tokens,
        )
        if result and hasattr(result, "content"):
            return result.content
        return str(result) if result else "[No response]"
    except Exception as e:
        logger.warning("ctx.sample() failed: %s", e)
        return f"[Sampling error: {e}]"
