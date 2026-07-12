# LLM Onboarding — Fleet Rollout Strategy

**Question:** How do we retrofit GPU detection + model recommendation across
all fleet repos without creating a maintenance nightmare?

---

## Option Analysis

### A. Canonical template in mcd (`templates/llm-detect/`)

A Python module + README in `mcp-central-docs/templates/` that each repo copies.

| Pro | Con |
|-----|-----|
| Zero new services to deploy | Every copy drifts over time |
| Works offline, no HTTP dep | Batch mutation = 35+ repos to update |
| Simple — just `uv add ./templates/llm-detect` | No central upgrade path |
| Any language can use it | Bug fix requires 35+ PRs |

### B. Feature in local-llm-mcp (recommended)

local-llm-mcp already manages LLM providers. It already has
`GET /api/llm/discover`. Extend it with GPU detection + model recommendation.

| Pro | Con |
|-----|-----|
| Single canonical implementation | Creates HTTP dependency |
| One place to fix bugs | local-llm-mcp must be running |
| Already a dep of chat-capable repos | Doesn't help stdio-only servers |
| Natural fit — it *is* the LLM gateway |  |
| Zero code changes in consumer repos (just call `/api/llm/recommend`) |  |

### C. "llm-fitter" in meta-mcp

A new capability in meta-mcp that detects GPU + recommends models across the fleet.

| Pro | Con |
|-----|-----|
| Meta-mcp already knows fleet topology | Meta-mcp is for *introspection*, not config |
| Sounds cool ("the fleet knows your GPU") | Mixing concerns — meta gets bloated |
| Central view of fleet LLM health | Now every repo needs meta-mcp running |
| | Feature-creep: it'll grow into option B anyway |

### D. New standalone MCP server (`llm-detect-mcp`)

Clean microservice just for this.

| Pro | Con |
|-----|-----|
| Zero coupling | Yet another MCP server to run |
| Owns its domain cleanly | Deployment fatigue |

### E. Agent-chained copy from mcd template

AGENTS.md instructs agents to add the mcd template to any repo that needs it.

| Pro | Con |
|-----|-----|
| No code changes needed | Only works when an agent session touches the repo |
| Leverages existing agent infrastructure | Inconsistent — repos that aren't touched stay stale |
| | Can't enforce compliance |

---

## Recommendation: B (local-llm-mcp) + A (mcd template) as fallback

**Primary: local-llm-mcp** gets two new endpoints:

```python
GET /api/llm/detect
# Returns: {"gpu": {...}, "ollama_installed": bool, "ollama_models": [...]}

GET /api/llm/recommend
# Returns: {"mode": "local"|"cloud", "model": "gemma4:12b",
#           "tier": 4, "vram_gb": 24,
#           "fallback": {"provider": "deepseek", "model": "deepseek-v4-flash"}}
```

Any repo that needs LLM sampling calls these. No code duplication, one
canonical implementation. Repos that already have local-llm-mcp as a dep
(arxiv-mcp, godot-mcp, multi-backup-mcp, etc.) get this for free.

**Secondary: mcd template** (`templates/llm-detect/detect.py`) — a self-contained
Python module repos can vendor for:
- **stdio-only MCP servers** that can't make HTTP calls to local-llm-mcp
- **Offline/air-gapped** environments
- **Repos that don't want an HTTP dependency**

The template has a version constant. Our fleet agent checks version drift
during maintenance passes (same pattern as `cua-smoke.py`).

### What meta-mcp should actually do

Meta-mcp gets a lighter task: `fleet_ops(operation="llm_pulse")` that probes
each repo's `GET /api/llm/detect` (or falls back to local-llm-mcp's endpoint)
and reports fleet-wide GPU inventory. This is introspection — meta-mcp's
actual job — not configuration.

---

## Rollout Plan

| Phase | What | Who |
|-------|------|-----|
| 1 | Add `detect_gpu()` to local-llm-mcp | local-llm-mcp maintainer |
| 2 | Add `GET /api/llm/detect` + `/recommend` | same |
| 3 | Create `mcd/templates/llm-detect/detect.py` | mcd maintainer |
| 4 | Wire `GET /api/v1/llm/detect` in godot-mcp (canary) | this session |
| 5 | GPU card in settings page (godot-mcp) | frontend pass |
| 6 | Add `fleet_llm_pulse` to meta-mcp | meta-mcp maintainer |
| 7 | Fleet sweep: add /api/llm/detect to all repos | agent batch (5-repo limit) |
| 8 | Update all sampling/service.py to use detect result | per-repo |

**Phase 4-5 are doable right now in godot-mcp as the canary.**
