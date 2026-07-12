# LLM Onboarding — GPU Detection & Model Selection

**Problem:** Fleet repos assume an RTX 4090 with 24 GB VRAM running Gemma 4 12B
via Ollama. Most users have weaker GPUs (or none). Without onboarding, they hit
OOM crashes, silent fallbacks, or accidentally configure expensive cloud models.

**Scope:** Cross-cutting — affects every fleet MCP server that uses LLM sampling
for game generation, chat, or agentic tools.

---

## 1. GPU Detection

Auto-detect on server start — pure Python, no sudo, no NVML license issues.

### Detection mechanism

```python
def detect_gpu() -> dict:
    """Return GPU info without external deps."""
    import subprocess, re
    try:
        # nvidia-smi is bundled with the driver — always available
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if out.returncode != 0: return {"available": False}
        parts = out.stdout.strip().split(", ")
        vram_mb = int(parts[1])
        return {
            "available": True,
            "name": parts[0],
            "vram_mb": vram_mb,
            "vram_gb": round(vram_mb / 1024, 1),
            "driver": parts[2],
        }
    except Exception:
        return {"available": False}
```

### VRAM tier → model recommendation

| VRAM | Tier | Recommended model | Also fits | Ollama command |
|------|------|-------------------|-----------|----------------|
| >= 32 GB | 5 — Monster | `qwen2.5-coder:32b` (Q4) | DeepSeek-R1 32B, Gemma 4 26B | `ollama pull qwen2.5-coder:32b-instruct-q4_K_M` |
| >= 20 GB | 4 — High-end | `gemma4:12b` | Qwen 2.5 Coder 14B, Llama 3.1 8B | `ollama pull gemma4:12b` |
| >= 14 GB | 3 — Mid | `qwen2.5-coder:7b` | Llama 3.2 3B, Mistral 7B | `ollama pull qwen2.5-coder:7b` |
| >= 10 GB | 2 — Entry | `llama3.2:3b` | Qwen 2.5 Coder 1.5B | `ollama pull llama3.2:3b` |
| >= 6 GB | 1 — Minimal | `llama3.2:1b` | TinyLlama, Gemma 3 1B | `ollama pull llama3.2:1b` |
| < 6 GB / no GPU | 0 — Cloud | External API | DeepSeek, OpenAI, Anthropic | N/A |

### When no NVIDIA GPU is detected

- Check for **Ollama** running on localhost (it might have CPU-only models)
- Check for **LM Studio** on port 1234
- If neither: **Cloud LLM required** — show the settings page on first launch

---

## 2. Cloud LLM Configuration

### Provider registry

| Provider | API format | Cost (2026) | Quality | Fleet recommendation |
|----------|-----------|-------------|---------|---------------------|
| DeepSeek V4 Flash | OpenAI-compatible | ~$0.15/M tok | Good | **Default** — cheap, fast, good-enough |
| DeepSeek V4 Pro | OpenAI-compatible | ~$0.50/M tok | Excellent | For complex game design |
| OpenAI GPT-4o | Native | ~$2.50/M tok | Excellent | Expensive — not recommended |
| Anthropic Claude | Native | ~$3.00/M tok | Excellent | Expensive — not recommended |
| Groq | OpenAI-compatible | Free tier | OK | Good for testing |
| OpenRouter | OpenAI-compatible | Varies | Varies | Access to many models |

### Forbidden defaults

**Never set a paid cloud provider as the default.** The server should:
1. Try Ollama first (local, free, private)
2. If Ollama unavailable AND a cloud API key is configured, use it
3. If neither: show a setup wizard, not a silent failure or expensive auto-billing

### Settings schema

```jsonc
{
  "llm": {
    "mode": "auto",                  // "auto" | "local" | "cloud"
    "local": {
      "provider": "ollama",          // "ollama" | "lmstudio" | "custom"
      "url": "http://localhost:11434",
      "model": "auto",               // "auto" = detected from VRAM table, or explicit
    },
    "cloud": {
      "provider": "deepseek",        // "deepseek" | "openai" | "anthropic" | "openrouter" | "custom"
      "api_key": "",                 // never stored in repo, only in settings.json
      "model": "deepseek-v4-flash",  // per-provider default
      "base_url": "",                // for custom OpenAI-compatible endpoints
    }
  }
}
```

---

## 3. Settings UI (Webapp)

New section in `/settings` page:

### GPU Detection Card

Shows on first visit and when `/api/v1/llm/detect` returns a different GPU:

```
┌─────────────────────────────────────────────┐
│  🖥️  GPU Detected: NVIDIA RTX 4090 (24 GB) │
│                                              │
│  Recommended model: gemma4:12b               │
│  Status: ✅ Installed (Ollama)               │
│                                              │
│  [Change model] [Run benchmark]              │
└─────────────────────────────────────────────┘
```

### LLM Provider Toggle

```
┌─────────────────────────────────────────────┐
│  LLM Mode: [Auto] [Local only] [Cloud only]  │
│                                              │
│  ── Local (Ollama) ──                        │
│  Model: gemma4:12b  ▼                        │
│  Status: ● Running (2.3s avg)                │
│                                              │
│  ── Cloud Fallback ──                        │
│  Provider: DeepSeek  ▼                       │
│  API Key:  ••••••••••••••••••  [Set]         │
│  Model: deepseek-v4-flash                    │
│  Status: ○ Not configured                    │
└─────────────────────────────────────────────┘
```

### LLM Benchmark

A "Run Benchmark" button that:
1. Sends a test prompt ("Write hello world in GDScript")
2. Measures time-to-first-token + total time
3. Shows result: `gemma4:12b — 2.3s first token, 8.1s total`
4. Stores result so the user can compare providers

---

## 4. Implementation Plan

### Phase 1: GPU detection (godot-mcp canary)

| Item | File | Effort |
|------|------|--------|
| `detect_gpu()` function | `src/godot_mcp/services/llm_detect.py` | 1h |
| `GET /api/v1/llm/detect` endpoint | `src/godot_mcp/server.py` | 30m |
| Model tier table + recommendation | `src/godot_mcp/services/llm_detect.py` | 1h |
| Ollama presence check | `src/godot_mcp/services/llm_detect.py` | 30m |

### Phase 2: Settings page

| Item | File | Effort |
|------|------|--------|
| LLM section in `/settings` | `webapp/src/pages/SettingsPage.tsx` | 2h |
| GPU detection card | same file | 1h |
| Provider toggle + API key input | same file | 1h |
| Benchmark button + results | same file + new endpoint | 2h |

### Phase 3: Sampling integration

| Item | File | Effort |
|------|------|--------|
| `sample_text` reads from settings.json (not just env) | `sampling/service.py` | 2h |
| Auto-detect VRAM -> pick model on first run | `server.py` lifespan | 1h |
| Cloud provider routing (DeepSeek default) | `sampling/service.py` | 2h |

### Phase 4: Fleet rollout

| Item | Effort |
|------|--------|
| Port detect logic to `mcp-central-docs/templates/llm-detect/` | 1h |
| Add to fleet-agent-mcp for fleet-wide monitoring | 2h |
| Update all fleet repos with GPU detection | 8h (mechanical) |

### Total effort: ~17h

---

## 5. Guardrails

### Cost protection

- **No credit card required for local-only mode.** Many users never need a cloud API key.
- **Cloud mode defaults to DeepSeek V4 Flash** ($0.15/M tok — ~$0.001 per game generation).
- **Every cloud request shows estimated cost** in the dashboard logs.
- **Monthly spending cap** (default $5, configurable).
- **Warn before first paid request:** "This will cost ~$0.001. Proceed?"

### Stored credentials

- API keys stored in `~/.godot-mcp/settings.json` (NOT `.env`, NOT the repo)
- Settings file is `600` (user-read-only) on Linux/macOS
- Keys are never logged, never in error messages, never in the webapp HTML
- "Clear API key" button in settings

### No vendor lock-in

- All cloud providers use OpenAI-compatible API format for chat completion
- Switching from DeepSeek to OpenAI to Groq is a one-field change (base URL + key)
- Benchmark results per provider help users choose informed

---

## 6. Default Selection Logic (governing algorithm)

```python
def select_default_model(detect: dict, ollama_models: list[str]) -> str:
    """Pick the best available model."""
    if not detect["available"]:
        return None  # cloud-only

    vram = detect["vram_gb"]
    installed = set(ollama_models)

    # Walk tiers from best to worst, pick first installed match
    tiers = [
        (32, ["qwen2.5-coder:32b-instruct-q4_K_M", "deepseek-r1:32b"]),
        (20, ["gemma4:12b", "qwen2.5-coder:14b"]),
        (14, ["qwen2.5-coder:7b", "mistral:7b"]),
        (10, ["llama3.2:3b", "qwen2.5-coder:1.5b"]),
        (6,  ["llama3.2:1b", "tinyllama:latest"]),
    ]

    for min_vram, candidates in tiers:
        if vram >= min_vram:
            for c in candidates:
                if c in installed:
                    return c
            # Tier matches but nothing installed — recommend first candidate
            return candidates[0] if vram >= min_vram else None

    return None
```
