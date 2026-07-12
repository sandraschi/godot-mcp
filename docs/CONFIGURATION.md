# Configuration

## Environment Variables

### Godot Engine

| Variable | Default | Description |
|----------|---------|-------------|
| `GODOT_PATH` | auto-detect | Path to godot.exe |
| `GODOT_HOST` | 127.0.0.1 | TCP bridge host |
| `GODOT_PORT` | 9080 | TCP bridge port |
| `GODOT_TAURI` | (unset) | Set to `1` when running inside Tauri (enables CORS) |

### LLM Sampling

| Variable | Default | Description |
|----------|---------|-------------|
| `GODOT_MCP_OLLAMA_URL` | http://localhost:11434 | Ollama server URL |
| `GODOT_MCP_OLLAMA_MODEL` | gemma4:12b | Ollama model name |
| `GODOT_MCP_LLM_BASE_URL` | (unset) | OpenAI-compatible API base URL (e.g. https://api.deepseek.com/v1) |
| `GODOT_MCP_LLM_API_KEY` | (unset) | Cloud API key |
| `GODOT_MCP_LLM_MODEL` | (unset) | Cloud model override |
| `GODOT_MCP_LLM_TIMEOUT` | 180 | LLM request timeout in seconds |

### Publishing

| Variable | Default | Description |
|----------|---------|-------------|
| `BUTLER_API_KEY` | (required) | itch.io Butler API key |
| `ITCH_TARGET` | (optional) | Default user/game slug |
| `BUTLER_PATH` | (optional) | Path to butler binary |
| `STEAM_MCP_URL` | http://127.0.0.1:11020 | steam-mcp server URL |
| `STEAM_APP_ID` | (required) | Steam App ID |
| `STEAM_DEPOT_ID` | (required) | Steam Depot ID |
| `STEAM_USERNAME` | (required) | Steamworks login |
| `STEAMCMD_PATH` | (required) | Path to steamcmd.exe |

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_PORT` | 10993 | HTTP server port |
| `MCP_HOST` | 127.0.0.1 | HTTP server host |
| `GODOT_MCP_UPLOADS_DIR` | ./uploads/ | File upload directory |
| `GODOT_MCP_OUTPUTS_DIR` | ./outputs/ | Export output directory |
| `GODOT_MCP_VIEWPORT_DIR` | ~/.godot-mcp/viewport/ | Viewport capture directory |
| `MCP_BRIDGE_URLS` | (optional) | Comma-separated peer MCP servers |

### Fleet

| Variable | Default | Description |
|----------|---------|-------------|
| `FLEET_EXCHANGE_ROOT` | D:\Dev\repos\_exchange | Fleet exchange directory |
| `WORLDLABS_BRIDGE_URL` | http://127.0.0.1:10865 | World Labs bridge URL |
| `WORLDLABS_WEB_URL` | https://apps.worldlabs.ai | World Labs web URL |

---

## Settings File

Persistent settings stored in `~/.godot-mcp/settings.json`:

```json
{
  "godot_path": "C:/Program Files/Godot/godot.exe",
  "godot_host": "127.0.0.1",
  "godot_ws_port": 9080
}
```

Edit via `PUT /api/v1/settings` or the `/settings` dashboard page.
