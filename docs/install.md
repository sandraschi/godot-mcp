# Godot MCP — Installation Guide

**Version**: 0.1.0

## Prerequisites

| Component | Minimum Version | Purpose |
|-----------|----------------|---------|
| **Python** | 3.12+ | MCP server (FastMCP 3.2 + FastAPI) |
| **Node.js** | 20+ | Vite + React webapp frontend |
| **Godot Engine** | 4.4+ | Game engine with TCP bridge addon |
| **uv** | Latest | Python package manager (fleet standard) |
| **just** | Latest | Command runner (fleet standard) |

### Check Your Versions

```powershell
python --version      # Should be 3.12 or 3.13
node --version        # Should be 20.x or 22.x
godot --version       # Godot 4.x
uv --version          # Any recent version
just --version        # Any recent version
```

## Quick Install

The `just bootstrap` command handles everything in one step:

```powershell
just bootstrap
```

This automatically:
1. Runs `just install-godot` to download Godot 4.4 if not already installed
2. Runs `uv sync --all-extras` to install all Python dependencies
3. Runs `npm install` in the `webapp/` directory for frontend dependencies

After bootstrap, verify with:

```powershell
just check
```

## Manual Install

### Step 1: Godot Engine

If `just install-godot` doesn't work for your environment, download manually:

1. Download Godot 4.4+ from https://godotengine.org/download/windows/
2. Extract `godot.exe` to a location in your PATH (e.g. `C:\Program Files\Godot\godot.exe`)
3. Verify: `godot --version`

Alternatively, set the `GODOT_PATH` environment variable:

```powershell
$env:GODOT_PATH = "C:\Program Files\Godot\godot.exe"
```

### Step 2: Python Dependencies

```powershell
uv sync --all-extras
```

This creates a `.venv` in the project directory and installs:

- `fastmcp>=3.2.0` — MCP server framework with SSE transport
- `fastapi>=0.104` — REST API framework
- `uvicorn[standard]>=0.23` — ASGI server
- `httpx>=0.27` — HTTP client
- `pydantic>=2.0` — Data validation
- `websockets>=12.0` — WebSocket client (future)

Development extras (`uv sync --all-extras`):

- `pytest>=8.0` — Test runner
- `pytest-asyncio>=0.24` — Async test support
- `ruff>=0.9` — Python linter and formatter

### Step 3: Webapp Dependencies

```powershell
Push-Location webapp
npm install
Pop-Location
```

Installs Vite, React, TypeScript, Tailwind CSS, and Biome (linter).

## Windows-Specific Notes

### PATH Configuration

Godot must be discoverable. The server checks these locations in order:
1. `GODOT_PATH` environment variable (absolute path)
2. `godot.exe` in system PATH (via `shutil.which`)
3. Common install paths: `C:\Program Files\Godot\`, `C:\Program Files (x86)\Godot\`, `~/Godot/`

### PowerShell Execution Policy

If scripts fail to run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Line Endings

All `.gd` files (GDScript bridge) and `.sh`/`.bat` files use LF line endings. If you edit these on Windows, configure your editor to preserve LF.

### Port Zombies

The `start.ps1` script automatically kills processes on ports 10992 and 10993 before starting. If you encounter port conflicts manually:

```powershell
Get-NetTCPConnection -LocalPort 10993 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
Get-NetTCPConnection -LocalPort 10992 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

## Verifying Installation

### Full Check (lint + tests)

```powershell
just check
```

Runs:
1. `just lint` — Ruff for Python, Biome for TypeScript/React
2. `just test` — Pytest suite (3 test files: bridge, server, tools)

### Individual Checks

```powershell
just lint          # Lint only (Python + TypeScript)
just fix           # Auto-fix lint issues
just test          # Run test suite
just health        # Ping live server (if running)
```

### Manual Verification

```powershell
# Check Python imports resolve
uv run python -c "from godot_mcp.server import app; print('Server module OK')"
uv run python -c "from godot_mcp.tools import register_all; print('Tools module OK')"
uv run python -c "from godot_mcp.services.godot_bridge import GodotBridge; print('Bridge module OK')"

# Check Godot availability
uv run python -c "from godot_mcp.services.godot_bridge import is_installed; print(f'Godot found: {is_installed()}')"

# Start server in stdio mode (quick smoke test)
uv run python -m godot_mcp.server --mode stdio
```

## Troubleshooting

### "godot.exe not found"

The server logs a warning but still starts. Set `GODOT_PATH` to the absolute path:

```powershell
$env:GODOT_PATH = "D:\Tools\Godot\godot.exe"
```

Or add Godot to your system PATH via Windows Settings > System > About > Advanced system settings > Environment Variables.

### "Connection refused at 127.0.0.1:9080"

The TCP bridge is not running. The MCP server still starts; this is a **warning**, not a fatal error.

**Fleet quick fix (this repo):**

```powershell
just godot-bridge
just bridge-test
```

**Manual:** Run the bridge project (`main_bridge.tscn` at repo root) or add `mcp_bridge.gd` as Autoload in your own Godot project and press F5.

### Sample demo: missing textures or animations

**Missing `.godot/imported/` (paddle.png, etc.):** First run needs import:

```powershell
just demo-import pong
just demo-run pong
```

`just demo-run` runs import automatically when `.godot/imported` is absent.

**Animation not found: idle / walk (platformer on Godot 4.4):** Official demos target 4.6 scene syntax. This repo patches the platformer for 4.4, or install 4.6: `just install-godot version="4.6"`. Use `just demo-run heart` for a native 4.0 project.

### "Module not found" errors

Ensure you ran `uv sync` from the project root. The `.venv` must be created. Verify:

```powershell
uv run python -c "import fastmcp; print(fastmcp.__version__)"
```

### Webapp won't start (npm errors)

```powershell
Push-Location webapp
Remove-Item -Recurse -Force node_modules, package-lock.json
npm install
Pop-Location
```

### Ruff/Biome version mismatches

Ruff and Biome versions are pinned in `pyproject.toml` and `webapp/package.json`. Run:

```powershell
just fix    # Auto-corrects all lint issues
```

### Port 10993 already in use

Another MCP server may be occupying the port. Check:

```powershell
Get-NetTCPConnection -LocalPort 10993 | Select-Object OwningProcess
```

Then stop the offending process or use a different port:

```powershell
$env:PORT = "10994"
uv run python -m godot_mcp.server --mode dual --port 10994
```
