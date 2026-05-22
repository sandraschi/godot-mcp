# Godot MCP — CLI Reference

**Version**: 0.2.1

---

## 1. Justfile Recipes

The project uses `just` as its command runner (fleet standard). All recipes are defined in `justfile` at the project root.

### Workflow Commands

#### `just bootstrap`

Full project initialization in one step. Runs:
1. `just install-godot` — downloads Godot 4.6+ if not already installed
2. `uv sync --all-extras` — installs Python dependencies (FastMCP, FastAPI, uvicorn, httpx, pydantic)
3. `npm install` — installs webapp dependencies (Vite, React, TypeScript, Tailwind, Biome)

```powershell
just bootstrap
```

#### `just install-godot`

Download and extract Godot 4.6+ for Windows. Downloads from `https://godotengine.org/download/windows/`. Extracts to `C:\Program Files\Godot\godot.exe`. Skips if already installed.

```powershell
just install-godot
```

#### `just serve`

Start the full stack: Python backend + React webapp frontend. Runs both processes concurrently. Backend on port 10993, frontend on port 10992.

```powershell
just serve
```

#### `just stdio`

Start the MCP server in stdio mode only. No HTTP, no webapp. Useful for direct MCP client integration (Claude Desktop, Cursor, Continue).

```powershell
just stdio
```

#### `just web`

Start only the React webapp frontend (port 10992). Requires the backend to already be running via `just serve` or manually.

```powershell
just web
```

#### `just dev`

Start the backend in development mode with hot reload (uvicorn `--reload`). Automatically restarts on Python file changes.

```powershell
just dev
```

### Quality Commands

#### `just lint`

Run all linters:
- `ruff check src/` — Python linting
- `biome check webapp/src/` — TypeScript/JSX linting

```powershell
just lint
```

#### `just fix`

Auto-fix all auto-fixable lint issues:
- `ruff check --fix src/`
- `biome check --write webapp/src/`

```powershell
just fix
```

#### `just test`

Run the pytest suite:
- `tests/test_bridge.py` — GodotBridge class unit tests
- `tests/test_server.py` — Server module tests
- `tests/test_tools.py` — MCP tool function tests

```powershell
just test
```

#### `just check`

Full quality gate: runs lint first, then tests. Fails on any lint error.

```powershell
just check
```

### Utility Commands

#### `just godot-bridge`

Start Godot headless with the repo bridge project (`main_bridge.tscn`). Listens on TCP **9080**. Run in a separate terminal from `just serve`.

```powershell
just godot-bridge
```

#### `just bridge-test`

POST `godot_status` to the REST API. Requires **both** `just serve` and `just godot-bridge`.

```powershell
just bridge-test
```

#### `just demo-list` / `just demo-run` / `just demo-import`

Run cloned sample games under `samples/`. First run imports assets via `godot --import`.

```powershell
just demo-list
just demo-run              # default: heart
just demo-run platformer
just demo-import pong
```

#### `just health`

Ping the live server's `/api/v1/status` endpoint. Requires the server to be running.

```powershell
just health
```

**Expected output**:
```json
{"ok": true, "service": "godot-mcp", "version": "0.2.1", "godot": {"ws_connected": true, ...}}
```

#### `just clean`

Clean up generated files and caches:
- `Remove-Item -Recurse -Force .venv/` — Python virtual environment
- `Remove-Item -Recurse -Force webapp/node_modules/` — Node.js dependencies
- `Remove-Item -Recurse -Force __pycache__/` — Python bytecode cache

```powershell
just clean
```

#### `just setup`

Standalone setup for CI/CD environments. Runs `uv sync` and `npm install` without Godot download.

```powershell
just setup
```

---

## 2. Server CLI

The Python server is invoked via `python -m godot_mcp.server`.

```powershell
uv run python -m godot_mcp.server [OPTIONS]
```

### Options

#### `--mode {stdio|http|dual}`

Transport mode for the MCP server.

| Mode | Transport | Description |
|------|-----------|-------------|
| `stdio` | stdin/stdout | JSON-RPC over standard I/O. For MCP clients that spawn the process directly (Claude Desktop, Cursor, Continue). No HTTP server started. |
| `http` | HTTP + SSE | FastAPI server on port 10993 with REST endpoints and SSE transport. No stdin/stdout MCP. |
| `dual` | Both | **Default**. Runs both stdio and HTTP transports simultaneously. Requires both transports to be ready before accepting requests. |

```powershell
# Stdio mode (for MCP clients)
uv run python -m godot_mcp.server --mode stdio

# HTTP-only mode
uv run python -m godot_mcp.server --mode http

# Dual mode (default)
uv run python -m godot_mcp.server --mode dual
```

#### `--host HOST`

The host address for the HTTP server (used in `http` and `dual` modes).

| Default | Description |
|---------|-------------|
| `0.0.0.0` | Bind on all interfaces |

```powershell
uv run python -m godot_mcp.server --host 127.0.0.1
```

#### `--port PORT`

The TCP port for the HTTP server.

| Default | Description |
|---------|-------------|
| `10993` | Fleet standard port for godot-mcp backend |

```powershell
uv run python -m godot_mcp.server --port 10994
```

#### `--agentic`

Enable CodeMode (BM25 discovery) for agentic workflows. Applies the experimental `CodeMode` transform during CLI orchestration only.

```powershell
uv run python -m godot_mcp.server --mode dual --agentic
```

When enabled, the server activates fastmcp's experimental CodeMode transform, which uses BM25 (Best Match 25) ranking to discover relevant tools for the current agentic context.

### Full Example

```powershell
uv run python -m godot_mcp.server `
    --mode dual `
    --host 127.0.0.1 `
    --port 10993 `
    --agentic
```

---

## 3. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GODOT_HOST` | `127.0.0.1` | Hostname for the Godot TCP bridge |
| `GODOT_PORT` | `9080` | Port for the Godot TCP bridge |
| `GODOT_PATH` | auto-detect | Absolute path to `godot.exe`. Overrides PATH-based discovery |
| `MCP_BRIDGE_URLS` | `""` | Comma-separated list of SSE URLs for cross-repo MCP bridge proxies |
| `PORT` | `10993` | HTTP server port (alternative to `--port`) |
| `WEB_PORT` | `10992` | Webapp Vite dev server port |
| `LOG_LEVEL` | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

### `GODOT_PATH`

Used when Godot is installed in a non-standard location or when `godot.exe` is not in PATH.

```powershell
# PowerShell
$env:GODOT_PATH = "D:\Tools\Godot\godot.exe"

# Or set permanently
[Environment]::SetEnvironmentVariable("GODOT_PATH", "D:\Tools\Godot\godot.exe", "User")
```

### `GODOT_HOST` and `GODOT_PORT`

Override the default bridge connection parameters. Useful when running Godot on a remote machine or in a container.

```powershell
$env:GODOT_HOST = "192.168.1.100"
$env:GODOT_PORT = "9080"
```

### `MCP_BRIDGE_URLS`

Cross-repo MCP proxy. The server creates bridge proxies to other fleet MCP servers, making their tools available through the godot-mcp server.

```powershell
$env:MCP_BRIDGE_URLS = "http://localhost:10966/sse,http://localhost:10944/sse"
```

This proxies tools from:
- `qcad-mcp` (port 10966) — CAD tools for geometry creation
- `freecad-mcp` (port 10944) — BIM tools for model preparation

### `PORT`

Alternative to `--port` for setting the HTTP server port. Used by `start.ps1`.

```powershell
$env:PORT = "10994"
```

### `WEB_PORT`

Port for the Vite dev server (frontend). Must match the port in `vite.config.ts`.

```powershell
$env:WEB_PORT = "10992"
```

### `LOG_LEVEL`

Controls Python logging verbosity.

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Development, debugging bridge protocol |
| `INFO` | Default. Startup/shutdown, tool calls, errors |
| `WARNING` | Production. Only warnings and errors |
| `ERROR` | Silent. Only critical failures |

---

## 4. Start Scripts

### `start.ps1`

Fleet-standard PowerShell launcher. Clears zombie processes on ports 10992 and 10993, then starts both backend and frontend.

```powershell
.\start.ps1
```

**Behavior**:
1. Kills any process on port 10992 (`Get-NetTCPConnection -LocalPort 10992 | Stop-Process`)
2. Kills any process on port 10993
3. Starts the Python backend: `uv run python -m godot_mcp.server --mode dual`
4. Starts the webapp frontend: `npm run dev` in `webapp/`
5. Opens the webapp in the default browser via `Start-Process http://localhost:10992`

**Browser auto-open**: The script polls `http://localhost:10993/api/v1/status` until the backend is reachable, then opens the frontend URL in the default browser.

### `start.bat`

CMD wrapper that delegates to `start.ps1`. Required for users who double-click in File Explorer or run from Command Prompt.

```bat
@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1"
```

### Manual Startup (Backend Only)

```powershell
# Start just the backend
uv run python -m godot_mcp.server --mode dual
```

### Manual Startup (Webapp Only)

```powershell
# Start just the frontend (requires backend already running)
Push-Location webapp
npm run dev
Pop-Location
```
