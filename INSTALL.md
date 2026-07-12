# Installing Godot MCP

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| **Godot 4.4+** | Engine + bridge addon | `just install-godot` or [godotengine.org](https://godotengine.org) |
| **Python + uv** | Run the server | `winget install astral-sh.uv` |
| **Bun** | JS runtime | `winget install oven-sh.bun` |
| **Ollama** (optional) | Local LLM for game builder | `winget install Ollama.Ollama` — then `ollama pull gemma4:12b` |

---

## Option A — Quick Start (recommended)

```powershell
git clone https://github.com/sandraschi/godot-mcp
cd godot-mcp
just bootstrap       # uv sync + bun install + Godot
just serve           # MCP + REST (10993)
just godot-bridge    # headless bridge (9080)
just web             # dashboard (10992)
just bridge-test     # verify
```

Or `.\start.ps1` for backend + webapp.

---

## Option B — MCPB (Claude Desktop)

1. Download `godot-mcp-v0.4.0-beta.1.mcpb` from [Releases](https://github.com/sandraschi/godot-mcp/releases)
2. Open Claude Desktop -> drag the file onto the window
3. Or add to `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "godot-mcp": {
         "command": "uv",
         "args": ["run", "--directory", "C:/path/to/godot-mcp", "run_server.py"]
       }
     }
   }
   ```

---

## Option C — Dev Setup

```powershell
git clone https://github.com/sandraschi/godot-mcp
cd godot-mcp
uv sync
just gb-smoke     # verify pipeline works (needs Ollama)
just serve        
```

---

## Option D — Naked PC (Steve-class)

```powershell
# 1. Install prerequisites
winget install astral-sh.uv
winget install oven-sh.bun
winget install Git.Git

# 2. Clone and run
git clone https://github.com/sandraschi/godot-mcp
cd godot-mcp
uv sync
bun --cwd webapp install
.\start.ps1
```

---

## LLM Setup

The default model is `gemma4:12b` via local Ollama. The server auto-detects
your GPU and recommends the best model for your VRAM. See `/settings` page.

| VRAM | Recommended | Command |
|------|-------------|---------|
| 20 GB+ | gemma4:12b (default) | `ollama pull gemma4:12b` |
| 14 GB+ | qwen2.5-coder:7b | `ollama pull qwen2.5-coder:7b` |
| 10 GB+ | llama3.2:3b | `ollama pull llama3.2:3b` |
| No GPU | DeepSeek V4 Flash (cloud) | Set API key in `/settings` |

Override via env: `GODOT_MCP_OLLAMA_MODEL=llama3.2:3b`

---

## Quick Verify

```powershell
just bridge-test     # godot_status via REST
just gb-smoke        # game builder pipeline (4/4 steps)
just demo-run vibecode  # play sample game
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Connection refused at 127.0.0.1:9080` | Run `just godot-bridge` first |
| `No LLM provider available` | Install Ollama or set cloud API key in `/settings` |
| GameBuilder design fails | Check Ollama running: `ollama list` |
| Godot not found | `just install-godot` or set `GODOT_PATH` |

See `docs/TROUBLESHOOTING.md` for full diagnostics.
