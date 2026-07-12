# Status — godot-mcp

**Status**: v0.3.0 — 15 Godot bridge tools + 6 itch ship tools + **7 steam ship tools** + 6 fleet pipeline tools + **6 game_builder tools** + **5 Prefab card tools**; TCP bridge verified; World Labs GLB import wired; AI game-from-prompt pipeline; Steam publishing via steam-mcp; MCP-over-HTTP mounted at `/mcp`; sampling falls back to HTTP API/Ollama. Bun migration complete. Prefab UI cards deployed.

**Repo**: `D:\Dev\repos\godot-mcp`  
**Ports**: Backend 10993, Frontend 10992, Bridge 9080, World Labs 10864/10865, steam-mcp 11020  
**Updated**: 2026-07-11

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

**Splat gap:** Gaussian splats (SPZ/RAD) are not rendered in Godot 4 via godot-mcp — use Spark viewer URL or Unity handoff. Multiple Godot 4 gaussian-splat GDExtensions exist (e.g. `Zylann/godot-gaussian-splat`) but none are stable enough for the pipeline. Decision: **document Spark viewer as the official handoff** and revisit when a GDExtension reaches 1.0. GLB collision mesh import works today.

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
| `just demo-run vibecode` | Vibecoder Runner (original, AI-themed) |
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

Sidecar only: `just tauri-sidecar`. Dev shell: `just tauri-dev` (expects `webapp` on 10992).

## Sample game: Vibecoder Runner

Original game in `samples/vibecode-runner/`: 2D side-scrolling runner against 10 AI-themed
enemy types (Hallucinator, PromptInjector, Tokenmaxxer, ContextOverflow, ClaudeDesktop,
Techbro, LegacyCode, TheVC, TheMeeting, TheDatacenter). Procedural terminal visuals, all
11 GDScript files pass `gdlint` clean. Created via the Game Builder pipeline.

```
just demo-run vibecode
```

Full catalog: `samples/vibecode-runner/README.md`.

## Done recently (2026-07-11 standards sweep)

- **5 Prefab UI card tools** — `show_godot_status_card`, `show_itch_status_card`, `show_steam_status_card`, `show_fleet_status_card`, `show_workflows_card`. Each returns `ToolResult(content=plain, structured_content=PrefabApp(...))`. Fleet Prefab standard compliance.
- **`prefab-ui>=0.14.0`** — core dependency added.
- **Bun migration** — `webapp` migrated from npm to Bun. All justfile, build scripts, and `tauri.conf.json` use `bun`/`bunx`. Fleet Bun standard compliance.
- **`@biomejs/biome` in devDependencies** — explicit install, no `npx` fallback.
- **`BUILD_LOG.md`** — created.
- **`build.ps1` security fix** — bundles `.env.example` instead of `.env` (no API key leaks).
- **`.bak` file purge** — 15 stale backup files deleted from `src/`.
- **`main.rs`/`backend.rs` dedup** — `main.rs` now calls `backend::spawn_backend()` instead of maintaining inline copy. Reduced from 95 to 49 lines.
- **`free_port()` upgraded** — multi-layer kill + 240s TIME_WAIT poll + UAC escalation fallback.
- **`tauri.conf.json` NSIS schema fix** — camelCase for Tauri 2.0 compatibility.
- **`manifest.json` fixed** — was double-stringified; proper JSON now. MCPB pack passes.
- **`.mcpbignore` excludes `samples/`** — MCPB dropped from 242 MB to 377 KB.
- **Playwright e2e expanded** — from 2 to 8 tests (KPIs, navigation, console errors, 422 validation).

## Done earlier (2026-07-01 correctness sweep)

- justfile parse blocker removed; `{{REPO}}` fix; `just tools` enumerates tools live
- ws_gateway `LOG_RING` crash fixed; `modify-node` → real `modify_node` GDScript handler
- Sampling fallback chain: `ctx.sample()` → OpenAI-compatible API → Ollama
- Bridge unified singleton, send lock + request_id correlation + recv buffer retention
- All blocking calls wrapped in `asyncio.to_thread`
- MCP HTTP transport mounted at `/mcp`
- MCPB repaired; root manifest.json fixed; path-robust `run_server.py`
- `export_and_ship` ImportError fixed
- `GET /api/capabilities` added; versions unified at 0.3.0

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
| `justfile` | ✅ | Comprehensive (550 lines) |
| `start.ps1` + `start.bat` | ✅ | |
| Tauri NSIS build pipeline | ✅ | `just tauri-build` |
| NSIS hooks | ✅ | Kill both processes |
| CUA smoke test | ✅ | `scripts/cua-smoke.py` |
| `backend.rs` free_port() | ✅ | Multi-layer kill + 240s TIME_WAIT poll |
| Web zoom (Ctrl+Scroll) | ✅ | |
| Web dashboard | ✅ | 20 pages |
| Skills page | ✅ | `src/godot_mcp/skills/` |
| `data-testid` attributes | ✅ | |
| Dark theme | ✅ | |
| `@tauri-apps/api` | ✅ | |
| Biome JS/TS linting | ✅ | `@biomejs/biome` in devDeps |
| `.env.example` | ✅ | `.env` no longer bundled in installer |
| Session context injection | ✅ | 5 files |
| `.pre-commit-config.yaml` | ✅ | |
| `mcpb/manifest.json` | ✅ | |
| Docker support | ✅ | `Dockerfile` + `docker-compose.yml` |
| Tauri v2 config schema | ✅ | camelCase NSIS — fixed |
| **`prefab-ui` core dep** | ✅ **NEW** | `prefab-ui>=0.14.0` |
| **Prefab card tools** | ✅ **NEW** | 5 `@mcp.tool(app=True)` tools |
| **Bun (fleet JS)** | ✅ **NEW** | `bun.lock`, `bun install`, `bunx` everywhere |
| **`BUILD_LOG.md`** | ✅ **NEW** | NSIS build gate record |

## Done this session (2026-07-11 features)

- **`godot_generate_procedural_texture`** — creates gradient/noise/checker/solid textures at runtime via bridge.
- **`generate_dialogue`** — generates DialogueManager.gd + Dialogic .dtl files from GamePlan NPCs.
- **GUT test integration** — `generate_game_tests` runs after `build_game()` with improved prompt + examples.
- **Portmanteau consolidation** — `itch_ops`, `steam_ops`, `fleet_ops` added (19 tools -> 3).
- **`just gb-demo`** — one-command demo (design -> GDScript -> validate).
- **`docs/game-builder-tutorial.md`** — 7-step tutorial from concept to HTML5.
- **`docs/godot-ecosystem.md`** — full plugin catalog with 7 curated plugins.
- **Vibecoder Runner** — sample game with 10 enemy types in `samples/vibecode-runner/`.

## Integrated tools

| Tool | Role | Status |
|------|------|--------|
| **gdlint** (gdtoolkit) | GDScript linter — 28 rules (naming, style, complexity) | Integrated in `generate_game_logic` validation pass |
| **gdformat** (gdtoolkit) | GDScript formatter (Black-style) | Available as `just gdscript-format-check` |
| **gdparse** (gdtoolkit) | GDScript AST parser | Available for static analysis |
| **godot --check-only** | Godot headless compile check | Integrated in validation + repair loop |
| **godot --export-release** | Headless HTML5/Windows export | `godot_export_release` tool |

See `docs/godot-ecosystem.md` for the full ecosystem catalog.
See `docs/ASSESSMENT_2026-07-11.md` for the full improvement roadmap.

## Next steps

1. Live E2E test: `build_game` with worldlabs + bridge + sampling (needs worldlabs-mcp running) — ~4h
2. All other items from the 54h assessment are **done** — see `docs/ASSESSMENT_2026-07-11.md`

## Tools registered

20 core engine tools in `core_tools.py`:
- 15 original (godot_status through godot_headless_verify)
- 4 additions (godot_capture_viewport, godot_simulate_input, godot_scene, godot_generate_procedural_texture)
- 1 utility (start_bridge)

Plus 70+ tools across all modules (itch, steam, fleet, artifacts, game builder, mcpb, prefabs, prompts, sampling, workflows, card tools).
