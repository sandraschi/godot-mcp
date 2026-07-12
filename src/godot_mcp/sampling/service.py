"""LLM sampling for godot-mcp — ctx.sample() with real fallbacks.

Provider chain (first available wins):

1. **MCP client sampling** — ``ctx.sample()`` when an MCP client that
   supports sampling is connected (FastMCP 3.x).
2. **OpenAI-compatible HTTP API** — set ``GODOT_MCP_LLM_BASE_URL`` (e.g.
   ``https://api.deepseek.com/v1`` or ``https://openrouter.ai/api/v1``),
   ``GODOT_MCP_LLM_API_KEY``, and ``GODOT_MCP_LLM_MODEL``.
3. **Local Ollama** — ``GODOT_MCP_OLLAMA_URL`` (default
   ``http://127.0.0.1:11434``) with ``GODOT_MCP_OLLAMA_MODEL`` (default
   ``gemma4:12b`` — fast, fits on RTX 4090, multimodal).

If every provider fails, ``SamplingUnavailableError`` is raised — callers get
an honest exception instead of a fake-success placeholder string.
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("godot-mcp.sampling")

_HTTP_TIMEOUT = float(os.getenv("GODOT_MCP_LLM_TIMEOUT", "180"))


class SamplingUnavailableError(RuntimeError):
    """No sampling provider (MCP client, HTTP API, Ollama) could produce text."""


def sampling_capabilities() -> dict[str, Any]:
    """Report which fallback providers are configured (for /api/capabilities)."""
    return {
        "llm_api_configured": bool(os.getenv("GODOT_MCP_LLM_BASE_URL", "").strip()),
        "llm_api_model": os.getenv("GODOT_MCP_LLM_MODEL", "") or None,
        "ollama_url": os.getenv("GODOT_MCP_OLLAMA_URL", "http://127.0.0.1:11434"),
        "ollama_model": os.getenv("GODOT_MCP_OLLAMA_MODEL", "gemma4:12b"),
    }


def _extract_ctx_text(result: Any) -> str | None:
    """Pull text out of a FastMCP sampling result (content block or plain str)."""
    if result is None:
        return None
    if isinstance(result, str):
        return result
    text = getattr(result, "text", None)
    if isinstance(text, str) and text:
        return text
    content = getattr(result, "content", None)
    if isinstance(content, str) and content:
        return content
    if isinstance(content, list):
        parts = [getattr(block, "text", "") for block in content]
        joined = "".join(p for p in parts if isinstance(p, str))
        if joined:
            return joined
    return None


async def _sample_via_ctx(ctx: Any, prompt: str, system: str | None, max_tokens: int) -> str | None:
    if ctx is None or not hasattr(ctx, "sample"):
        return None
    try:
        result = await ctx.sample(prompt, system_prompt=system, max_tokens=max_tokens)
        text = _extract_ctx_text(result)
        if text:
            return text
        logger.warning("ctx.sample() returned no extractable text (%r)", type(result))
        return None
    except Exception as e:
        logger.warning("ctx.sample() failed, falling back: %s", e)
        return None


async def _sample_via_openai_api(prompt: str, system: str | None, max_tokens: int) -> str | None:
    base_url = os.getenv("GODOT_MCP_LLM_BASE_URL", "").strip().rstrip("/")
    if not base_url:
        return None
    api_key = os.getenv("GODOT_MCP_LLM_API_KEY", "").strip()
    model = os.getenv("GODOT_MCP_LLM_MODEL", "deepseek-chat").strip()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json={"model": model, "messages": messages, "max_tokens": max_tokens},
            )
            resp.raise_for_status()
            data = resp.json()
        text = data["choices"][0]["message"]["content"]
        if isinstance(text, str) and text.strip():
            logger.info("Sampled via HTTP API (%s, %s)", base_url, model)
            return text
        return None
    except Exception as e:
        logger.warning("HTTP API sampling failed (%s), falling back: %s", base_url, e)
        return None


async def _sample_via_ollama(prompt: str, system: str | None, max_tokens: int) -> str | None:
    base_url = os.getenv("GODOT_MCP_OLLAMA_URL", "http://127.0.0.1:11434").strip().rstrip("/")
    model = os.getenv("GODOT_MCP_OLLAMA_MODEL", "gemma4:12b").strip()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
            )
            resp.raise_for_status()
            data = resp.json()
        text = (data.get("message") or {}).get("content", "")
        if isinstance(text, str) and text.strip():
            logger.info("Sampled via Ollama (%s)", model)
            return text
        return None
    except Exception as e:
        logger.warning("Ollama sampling failed (%s @ %s): %s", model, base_url, e)
        return None


async def sample_text(ctx, prompt: str, system: str | None = None, max_tokens: int = 512) -> str:
    """Generate text: ctx.sample() -> OpenAI-compatible API -> Ollama.

    Raises:
        SamplingUnavailableError: if no provider produced text.
    """
    text = await _sample_via_ctx(ctx, prompt, system, max_tokens)
    if text:
        return text

    text = await _sample_via_openai_api(prompt, system, max_tokens)
    if text:
        return text

    text = await _sample_via_ollama(prompt, system, max_tokens)
    if text:
        return text

    raise SamplingUnavailableError(
        "No LLM provider available: no sampling-capable MCP client connected, "
        "GODOT_MCP_LLM_BASE_URL not set (or unreachable), and Ollama not reachable at "
        + os.getenv("GODOT_MCP_OLLAMA_URL", "http://127.0.0.1:11434")
    )
