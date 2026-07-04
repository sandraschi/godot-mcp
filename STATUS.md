# Status — godot-mcp

**Status**: v0.3.0 — 15 Godot bridge tools + 6 itch ship tools + **7 steam ship tools** + 6 fleet pipeline tools + **6 game_builder tools**; TCP bridge verified; World Labs GLB import wired; AI game-from-prompt pipeline; Steam publishing via steam-mcp; MCP-over-HTTP mounted at `/mcp`; sampling falls back to HTTP API/Ollama.

**Repo**: `D:\Dev\repos\godot-mcp`  
**Ports**: Backend 10993, Frontend 10992, Bridge 9080, World Labs 10864/10865, steam-mcp 11020  
**Updated**: 2026-07-01

## Runtime (two processes)

| Process | Command | Port |
|---------|---------|------|
| MCP gateway | `just serve` or `start.ps1` | 10993 / 10992 |
| Godot bridge | `just godot-bridge` | 9080 |

Verify: `just bridge-test` → `Bridge OK - Godot 4.4.x @ … FPS`

Startup log warning `Connection refused at 127.0.0.1:9080` is expected until the bridge runs.

## Architecture

Godot 4 engine → TCP bridge (`mcp_bridge.gd` in `main_bridge.tscn`) → Python MCP → REST/SSE + webapp.

See `docs/architecture.md`, `docs/PRD.md`, `docs/ship-to-itch.md`, `docs/ship-to-steam.md`.

## MCP tools

### Godot bridge (15)

| Tool | Status |
|------|--------|
| `godot_status` | Verified live |
| `godot_import_stl` | Implemented |
| `godot_import_glb` | Implemented |
| `godot_import_obj` | Implemented |
| `godot_play_animation` | Implemented |
| `godot_load_velocity_field` | Implemented |
| `godot_spawn_particles` | Implemented |
| `godot_animate_streamlines` | Implemented |
| `godot_create_camera` | Implemented |
| `godot_add_light` | Implemented |
| `godot_set_material` | Implemented |
| `godot_export_web` | Implemented (+ CLI fallback) |
| `godot_read_scene_tree` | Implemented |
| `godot_set_config` | Implemented |
| `godot_headless_verify` | Implemented |

Bridge-only actions (REST action map + gateway, not MCP tools): `add_node`, `remove_node`, `modify_node`, `save_scene`.

### itch.io / Butler (6)

| Tool | Status |
|------|--------|
| `itch_status` | Implemented |
| `godot_export_release` | Implemented (headless export, no bridge) |
| `itch_push_preview` | Implemented |
| `itch_push` | Implemented |
| `itch_latest_version` | Implemented |
| `ship_to_itch` | Implemented |

Workflow: `ship_web_itch` (export → preview → push).

### Steam / steam-mcp (7)

| Tool | Status |
|------|--------|
| `steam_status` | Implemented (HTTP → steam-mcp) |
| `steam_checklist` | Implemented |
| `steam_monetization_guide` | Implemented |
| `steam_stage_build` | Implemented (Windows export → exchange) |
| `ship_to_steam_prerelease` | Implemented (beta branch; dry_run default) |
| `ship_to_steam_release` | Implemented (default branch; dry_run default) |
| `ship_to_steam` | Implemented (full pipeline) |

Workflows: `ship_windows_steam_beta`, `ship_windows_steam_release`. Env: `STEAM_MCP_URL`, `STEAM_APP_ID`, `STEAM_DEPOT_ID`, `STEAM_USERNAME`, `STEAMCMD_PATH`.

### Fleet maker pipeline (6)

| Tool | Status |
|------|--------|
| `fleet_exchange_status` | Implemented |
| `fleet_import_from_exchange` | Implemented (GLB/OBJ/STL via bridge) |
| `fleet_worldlabs_get_world` | Implemented (HTTP → worldlabs bridge) |
| `fleet_worldlabs_stage_mesh` | Implemented (collider GLB → `_exchange`) |
| `fleet_worldlabs_stage_splat` | Implemented (SPZ to exchange; **not** Godot import) |
| `fleet_worldlabs_import_mesh` | Implemented (stage + `godot_import_glb`) |

REST: `/api/v1/fleet/*`. Assessment: `docs/FLEET_ASSESSMENT.md`. Just: `fleet-status`, `fleet-import`, `fleet-worldlabs-*`.

**Splat gap:** Gaussian splats (SPZ/RAD) are not rendered in Godot via godot-mcp yet — use Spark viewer URL or Unity handoff; GLB collision mesh works today.

**Game Builder gap:** REST + UI + scene/script sync done. Live E2E still manual.

**Logs:** Fleet-standard `/api/logs` + `/logs` page (tail, pagination, filters, export, clear).

### Game Builder (6)

| Tool | Status |
|------|--------|
| `design_game` | Implemented (LLM sampling → GamePlan JSON) |
| `generate_game_worlds` | Implemented (bridge → worldlabs-mcp) |
| `compose_game_scene` | Implemented (GLB import + scene setup) |
| `generate_game_logic` | Implemented (ctx.sample() GDScript gen) |
| `export_and_ship` | Implemented (HTML5 export + itch push) |
| `build_game` | Implemented (full pipeline in one call) |

Pipeline: `prompt → design → worlds → compose → logic → export`. Spec: `docs/SPEC_GAME_BUILDER.md`.

## Web dashboard

| Route | Purpose |
|-------|---------|
| `/logs` | Fleet activity log — tail, filters, export |
| `/game-builder` | AI game pipeline steps + full build |
| `/ship` | Export, Butler preview/push, env status |
| `/ship-steam` | Export Windows, stage depot, Steam upload (dry_run) |
| `/workflows` | Includes `ship_web_itch`, `ship_windows_steam_*` |
| `/settings` | itch env hints (read-only) |

## Sample games & export

| Recipe | Demo |
|--------|------|
| `just demo-run` | Heart Platformer (4.0) |
| `just demo-run platformer` | Official 2D platformer (4.4-patched) |
| `just demo-run pong` | Pong |
| `just demo-list` | All aliases |
| `just little-game-export web dodge` | HTML5 → `build/little-game/dodge/web/` |
| `just ship web dodge` | Export + Butler push (needs env) |
| `just steam-ship-beta dodge` | Export + stage + Steam beta upload (dry_run) |

## Tauri native app (v0.3.0)

| Artifact | Path |
|----------|------|
| NSIS installer | `native/target/release/bundle/nsis/Godot MCP_0.3.0_x64-setup.exe` |
| MSI installer | `native/target/release/bundle/msi/Godot MCP_0.3.0_x64_en-US.msi` |
| Dev binary | `native/target/release/godot-mcp-native.exe` |

Build (requires Rust, Node 20+, uv, ~10 min first run):

```powershell
just tauri-build
```

Sidecar only: `just tauri-sidecar`. Dev shell: `just tauri-dev` (expects `web_sota` on 10992).

## Done recently (2026-07-01 correctness sweep)

- justfile parse blocker removed (broken `pack-mcpb` recipe); `{{REPO}}` e2e fix; honest `tools` enumeration; VER 0.3.0
- ws_gateway `LOG_RING` crash fixed (activity_log polling); `modify-node` → real `modify_node` GDScript handler
- Sampling fallback chain: `ctx.sample()` → OpenAI-compatible API → Ollama; `SamplingUnavailableError` instead of fake-success string; Game Builder works over REST now
- Bridge unified (module singleton), send lock + request_id correlation + recv buffer retention; settings.json wired into connect
- All blocking bridge/subprocess/download calls wrapped in `asyncio.to_thread`
- MCP HTTP transport mounted at `/mcp` (dual/http modes real now)
- MCPB repaired: stale `mcpb/src/` drift copy deleted, root `manifest.json` with `${__dirname}`, path-robust `run_server.py`
- Latent ImportError in `export_and_ship` fixed (`godot_export_release_tool`)
- `GET /api/capabilities` added; versions unified at 0.3.0; CHANGELOG head corruption repaired

## Done earlier (2026-05-25)

- **Game Builder pipeline** (`godot_mcp/game_builder/`) — 6 MCP tools for prompt-to-game, GamePlan schema, LLM prompts, bridge orchestration
- **Fleet pipeline module** (`godot_mcp/fleet/`) — exchange listing, World Labs mesh download/import, splat staging, REST + MCP tools
- itch/Butler module + REST `/api/v1/itch/*` + `/ship` UI
- Little-game export scripts + Just recipes
- Bridge parse fix; port 9080 listens
- Justfile parses under just 1.50
- Tauri 2.0 + PyInstaller sidecar
- MCD gamedev + project pages updated
- VibeCode Runner sample + `docs/ai-and-indie-games.md`
- `docs/fleet-game-pipeline.md` + `docs/FLEET_ASSESSMENT.md`

## Fleet standards compliance

| Standard | Status | Notes |
|----------|--------|-------|
| `glama.json` | ✅ | Root |
| `llms.txt` + `llms-full.txt` | ✅ | Root |
| Tool annotations | ✅ | READ_ONLY/MUTATING per module |
| `justfile` | ✅ | Comprehensive (520 lines) |
| `start.ps1` + `start.bat` | ✅ | |
| Tauri NSIS build pipeline | ✅ | `just tauri-build` |
| NSIS hooks | ✅ | Kill both processes |
| CUA smoke test | ✅ | `scripts/cua-smoke.py` |
| `backend.rs` free_port() | ✅ | Multi-layer kill |
| Web zoom (Ctrl+Scroll) | ✅ | |
| Web dashboard | ✅ | 20 pages |
| Skills page | ✅ | `src/godot_mcp/skills/` |
| `data-testid` attributes | ✅ | |
| Dark theme | ✅ | |
| `@tauri-apps/api` | ✅ | |
| Biome JS/TS linting | ✅ | `web_sota/biome.json` |
| `.env.example` | ✅ | New — `.env` no longer bundled |
| Session context injection | ✅ | New — 5 files |
| `.pre-commit-config.yaml` | ✅ | New |
| `mcpb/manifest.json` | ✅ | New |
| Docker support | ✅ | New — `Dockerfile` + `docker-compose.yml` |
| Tauri v2 config schema | ✅ | Fixed — removed invalid keys |

## Next steps

1. Live E2E test: `build_game` with worldlabs + bridge + sampling (or `GODOT_MCP_LLM_BASE_URL`)
2. Prefab UI cards + `fastmcp dev apps` preview (fleet GenerativeUI standard)
3. Bun migration for `web_sota` (bun.lock, Biome)
4. R&D: `godot_import_splat` bridge action (SPZ in-engine)
5. Optional: `/fleet` dashboard page; multi-node scene hierarchy from GamePlan
