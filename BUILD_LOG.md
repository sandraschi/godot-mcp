# BUILD_LOG.md — godot-mcp

## 2026-07-11 — Full standards sweep

### Build results

| Gate | Result |
|------|--------|
| `ruff check src/ tests/` | All checks passed |
| `tsc --noEmit` (webapp) | Clean |
| `uv run pytest` | 52/52 passed |
| `bunx playwright test` | 8 tests (improved from 2) |
| PyInstaller backend | 27.4 MB onefile |
| `bunx tauri build --bundles nsis` | **Godot MCP_0.3.0_x64-setup.exe** built |
| `bunx mcpb pack` | **godot-mcp-v0.3.0.mcpb** built |

### Issues found and fixed

| # | Issue | Severity | Fix |
|---|-------|----------|-----|
| 1 | `build.ps1` bundles `.env` not `.env.example` — leaks API keys | **SECURITY** | Changed to bundle `.env.example` only |
| 2 | 15 stale `.bak` files in `src/` | Cleanliness | Deleted all |
| 3 | PyInstaller `console=True` — shows cmd window on launch | UX | Changed to `console=False` |
| 4 | `prefab-ui>=0.14.0` missing from core deps | Standards | Added |
| 5 | Package manager is npm, not Bun (fleet standard) | Standards | Migrated: `bun install`, `bun.lock`, deleted `package-lock.json` |
| 6 | `justfile` uses `cmd /c npm` / `npx` everywhere | Standards | Updated all to `bun`/`bunx` |
| 7 | `build.ps1` uses `npx` + global pyinstaller | Standards | Fixed: `bunx`, project-venv pyinstaller |
| 8 | `backend.rs` `free_port()` has no polling/re-kill | Robustness | Upgraded to fleet standard with 240s TIME_WAIT poll + UAC escalation |
| 9 | `tauri.conf.json` uses `npm` pre-commands | Standards | Changed to `bun --cwd` |
| 10 | `webapp` missing `@biomejs/biome` in devDeps | Standards | Added |
| 11 | `tauri.conf.json` nsis uses snake_case (Tauri 1.x) | Build | Fixed to camelCase (`installMode`, `installerHooks`) |
| 12 | `main.rs` missing `CommandExt` import | Build | Added `use std::os::windows::process::CommandExt` |
| 13 | `root` `manifest.json` was double-stringified JSON string | Build | Replaced with proper JSON object |
| 14 | CUA smoke script header says "pywinauto-mcp canary" | Cleanliness | Fixed to "godot-mcp" |
| 15 | No `BUILD_LOG.md` | Docs | Created |
| 16 | E2e tests only 2 (basic smoke) | Quality | Expanded to 8 tests (KPIs, navigation, console errors, 422) |

### Known gaps (deferred)

- Prefab UI card tools for list/status/stats (requires new `@mcp.tool(app=True)` implementations)
- `.mcpbignore` could exclude `samples/godot-demo-projects/` (31+ MB of demo data)
- `backend.rs` constants are unused (main.rs has its own spawn logic) — pre-existing architectural duplication
