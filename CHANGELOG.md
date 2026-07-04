# Changelog

All notable changes to **godot-mcp** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (2026-07-04 fleet standardisation)
- **`.env.example`** — safe credential template; `native/tauri.conf.json` now references `.env.example` instead of `.env` (no API key leaks)
- **Session context injection** — `.claude-plugin/plugin.json`, `hooks/hooks.json`, `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md` for 49-tool agent awareness
- **`.pre-commit-config.yaml`** — ruff check + ruff-format on commit
- **`mcpb/manifest.json` + `.mcpbignore`** — ready for `mcpb pack` distribution
- **`Dockerfile` + `docker-compose.yml`** — containerized deployment

### Fixed
- **Tauri 2.0 NSIS config schema** — removed invalid `create_desktop_shortcut` / `create_start_menu_shortcut` keys (not valid in v2)

### Fixed (2026-07-01 correctness sweep)
- **justfile parse failure** — the broken `pack-mcpb` recipe (multiline PowerShell array) made every `just` invocation fail. Removed in favour of the fleet-standard root-level `just mcpb-pack`. Also fixed undefined `{{REPO}}` in the e2e recipes, removed the duplicate `cua-nsis-test` recipe (fleet.just provides it), and made `just tools` actually enumerate registered tools instead of printing a hardcoded "37+".
- **ws_gateway startup crash** — `_push_log_entries` imported a nonexistent `LOG_RING` from `server`; now polls `services/activity_log.query_logs()` and skips work when no clients are connected.
- **`modify-node` phantom bridge action** — the mobile gateway and command dispatcher sent an action the GDScript bridge never implemented. Added a real `modify_node` handler in `mcp_bridge.gd` (path-or-name node lookup, nested properties via `set_indexed`, returns previous/new values) and fixed all callers to snake_case.
- **Sampling now has real fallbacks** — `sample_text` tries `ctx.sample()` → OpenAI-compatible API (`GODOT_MCP_LLM_BASE_URL` / `_API_KEY` / `_MODEL`) → local Ollama (`GODOT_MCP_OLLAMA_URL` / `_MODEL`), and raises `SamplingUnavailableError` instead of returning a fake-success placeholder string. Game Builder works over REST/dashboard now, not only via sampling-capable MCP clients. Also fixed result-content extraction and system-prompt passing for `ctx.sample()`.
- **Latent ImportError in `export_and_ship`** — imported nonexistent `godot_export_release` from `itch.service` (real name: `godot_export_release_tool`); would have crashed on first use.
- **Godot bridge unified and hardened** — one module singleton (`get_bridge()`) shared by server, tools, gateway, and pipelines (previously two divergent instances with separate sockets and desynced state). `threading.Lock` around each request/response exchange; `request_id` correlation with stale-reply draining; `_recv_line` retains bytes after the first newline (previously discarded, losing pipelined messages); config is re-resolved on each connect (env → `~/.godot-mcp/settings.json` → defaults), so `PUT /api/v1/settings` actually takes effect (it now also drops the current connection).
- **Event-loop blocking eliminated** — all blocking bridge socket, subprocess, and HTTP-download calls in `core_tools`, `ws_gateway`, `mobile_command`, `game_builder/pipeline`, and the REST tool handlers are wrapped in `asyncio.to_thread`.
- **MCP-over-HTTP transport mounted** — `--mode http/dual` previously advertised an MCP endpoint that returned 404 (transport never mounted). The FastMCP HTTP app is now mounted at `/mcp` with its lifespan wired into the FastAPI lifespan.
- **MCPB packaging repaired** — removed the stale drifted flat server copy under `mcpb/src/` (plus its own manifest/pyproject/run_server). Root `manifest.json` written with `${__dirname}` (not `${PWD}`), version 0.3.0. `run_server.py` resolves `src/` relative to itself instead of the CWD. Packing is root-level via `just mcpb-pack`.
- **CHANGELOG corruption** — removed duplicated pre-header Unreleased blocks containing literal BEL/tab escape artifacts.
- **Versions unified at 0.3.0** — pyproject, justfile `VER`, web_sota `package.json`, Tauri conf, bridge `plugin.cfg`, MCPB manifest; the server reads its version from package metadata.

### Fixed (2026-06-14, salvaged from corrupted duplicate blocks)
- Tauri build: Rust crate conflict (brotli/alloc-no-stdlib), PyInstaller path mismatch (hyphen vs underscore in src dirs), TypeScript errors (unused imports, useRef arg, import.meta.env).
- Tauri CORS: explicit origins (`tauri://localhost`, `http://tauri.localhost`, `https://tauri.localhost`) instead of `["*"]`; `_TAURI` env toggle with allow_origin_regex.
- CUA-NSIS: `just cua-nsis-test` recipe + 11-phase smoke test (install, launch, WebView OCR, diagnostics, uninstall); build.ps1 copies the NSIS installer to dist/.

### Added
- `GET /api/capabilities` — fleet-standard runtime capability introspection (Godot engine/bridge, Butler, Steam/World Labs URLs, sampling providers, MCP HTTP, mobile gateway, logs).
- `godot_add_node` / `godot_remove_node` / `godot_modify_node` / `godot_save_scene` exposed through the REST tool-execution action map.
- `export_web` via bridge now uses a 300 s timeout instead of the 10 s default.
- Uploads/outputs directories overridable via `GODOT_MCP_UPLOADS_DIR` / `GODOT_MCP_OUTPUTS_DIR`.
- **Steam publishing** (`godot_mcp/steam/`) — 7 MCP tools bridging to steam-mcp: export Windows, stage to `_exchange/steam-builds/`, VDF + SteamPipe upload (dry_run default). REST `/api/v1/steam/*`, dashboard **`/ship-steam`**, workflows `ship_windows_steam_beta` / `ship_windows_steam_release`. Just: `steam-status`, `steam-stage`, `steam-ship-beta`, `steam-ship-release`. Docs: `docs/ship-to-steam.md`.
- **Fleet-standard logs** — `services/activity_log.py`, `/api/logs` (query, stats, export, clear), rewritten `/logs` page; tool calls logged as `kind: tool_call`.
- **Game Builder REST + UI** — `/api/v1/game-builder/*`, `/game-builder` dashboard; game_builder tools in `PYTHON_TOOLS`.
- **Scene materialization** — `materialize_scenes_from_plan`, `sync_project_from_plan`; updates `run/main_scene`.
- **Game Builder ↔ fleet wiring** — `generate_game_worlds` stages collider GLBs via `fleet_worldlabs_stage_mesh`; `compose_game_scene` accepts `worlds_result_json` with Marble ids; `build_game` copies meshes + writes scripts; `templates/game-template/` bootstrap project.
- **Game Builder pipeline** (`godot_mcp/game_builder/`) — AI-native game creation from natural language. 6 MCP tools:
  - `design_game` — LLM decomposes concept into GamePlan (worlds, scenes, scripts, controls, scoring, export)
  - `generate_game_worlds` — calls worldlabs-mcp via bridge for each world, polls until completion
  - `compose_game_scene` — imports Marble GLBs into Godot, sets up lighting/camera/node structure
  - `generate_game_logic` — AI writes all GDScript files via `ctx.sample()`
  - `export_and_ship` — HTML5 export + optional itch.io push
  - `build_game` — master tool: design → worlds → compose → logic → export
- **GamePlan schema** (`plan.py`) — Pydantic model for AI-generated game plans
- **System prompts** (`prompts.py`) — LLM prompts for game design + GDScript generation
- **Pipeline orchestration** (`pipeline.py`) — bridges worldlabs-mcp, godot-mcp, and LLM sampling
- **Spec document** (`docs/SPEC_GAME_BUILDER.md`)

### Changed
- **Tool count**: 43 → 56 MCP tools (added 6 game_builder + 7 steam tools) — actual enumerated total per `just tools` is **93** (incl. depot/prefab/prompt/workflow/bridge/sampling tools).
- `pyproject.toml`: `fastmcp>=3.4.2,<4`; removed unused `websockets` dependency; ruff consolidated into `[dependency-groups].dev` (the CI lint step now actually has ruff installed).
- `POST /api/v1/settings` responses note that the bridge reconnects with the new config on next use.

## [0.2.1] - 2026-05-22

### Added
- **itch.io / Butler shipping** (`godot_mcp/itch/`): export sample games, `push-preview`, `push`, and one-shot `ship_to_itch`. Six MCP tools; REST at `/api/v1/itch/*`; dashboard **`/ship`** page; `ship_web_itch` workflow. Env: `BUTLER_API_KEY`, `ITCH_TARGET`, `BUTLER_PATH`, `ITCH_CHANNEL_WEB`, `ITCH_CHANNEL_WIN`, `GODOT_EXPORT_GAME`. Just: `itch-status`, `itch-push-preview`, `itch-push`, `ship`.
- **Little-game export** (`scripts/little-game-export.ps1`, `templates/little-game-export_presets.cfg`): `just install-export-templates`, `just little-game-export`, `just little-game-pack`. Output under `build/little-game/<game>/`.
- **Tauri 2.0 native app** (`native/`): PyInstaller sidecar `godot-mcp-backend`, auto-starts MCP on 10993, bundles `web_sota` dashboard. Build: `just tauri-build`. Scripts: `native/build.ps1`, `build-sidecar.ps1`, `scripts/generate-tauri-icon.ps1`, `scripts/patch-platformer-godot44.ps1`.
- **Sample games workflow**: `samples/` with official `godot-demo-projects`, Heart Platformer, procedural generation, skelerealms; `just demo-list`, `just demo-run`, `just demo-import` (auto `--import` on first run).
- **Bridge diagnostics**: `just bridge-test`, `just bridge-status`, `just godot-bridge` (headless bridge project).
- **VibeCode Runner** sample (`samples/vibecode-runner/`) — vibecoding-themed side-scroller (AI-assisted scaffold example).
- **Fleet pipeline** (`godot_mcp/fleet/`): exchange listing, World Labs mesh download/import, splat staging, REST `/api/v1/fleet/*`, six MCP tools. Docs: `docs/fleet-game-pipeline.md`, `docs/FLEET_ASSESSMENT.md`. Just: `fleet-status`, `fleet-import`, `fleet-worldlabs-*`.
- **Product docs**: `docs/PRD.md`, `docs/ai-and-indie-games.md`; MCD fleet pages at `mcp-central-docs/projects/godot-mcp/`.

### Fixed
- **GDScript bridge**: Removed duplicate `_count_meshes` in `mcp_bridge.gd` (parse error blocked TCP listener on 9080).
- **Justfile 1.50**: Quoted recipe defaults (`mode="dual"`, `count="10"`), PowerShell-safe `doctor`/`freeze`, `depot-import`/`tool` args.
- **Platformer on Godot 4.4**: Patched `libraries/ = SubResource(...)` → `libraries = { "": SubResource(...) }` in six `.tscn` files (fixes missing `idle`/`walk` animations).

### Changed
- `GET /api/v1/status` includes `itch` block (Butler path, API key set, defaults, last ship) and **`fleet`** block (exchange root, asset count, splat/mesh flags).
- `POST /api/v1/control/tool` dispatches itch + workflow tools without Godot bridge.
- `samples/README.md` — demo catalog, import notes, 4.4 vs 4.6 guidance.
- `docs/install.md`, `docs/cli.md`, `docs/little-game-guide.md`, `STATUS.md` — export/ship recipes, Butler env, `/ship` UI.
- MCD: `projects/godot-mcp/`, `docs/gamedev/` — Butler via godot-mcp (not a separate butler-mcp repo).

---

## [0.2.0] - 2026-05-19

### Added
- **GLB/GLTF import** (`godot_import_glb`): Native Godot 4.0 GLTFDocument importer via GDScript bridge. Unlocks the blender-mcp → godot-mcp cross-fleet pipeline for glTF 2.0 binary (.glb) and text (.gltf) files.
- **OBJ import** (`godot_import_obj`): Wavefront OBJ import via Godot 4.0 ResourceLoader. Supports the freecad-mcp CFD streamline export → godot-mcp visualization pipeline.
- **Real HTML5 export**: `godot_export_web` now falls back to `godot --headless --export-release` subprocess when the GDScript bridge reports export templates unavailable. 300s timeout, auto-creates output directories.
- **Fleet exchange depot**: `_exchange/` convention documented at `D:\Dev\repos\_exchange\` (cad/, models/, cfd/, avatars/, robots/).

### Changed
- Tool count: 12 → 14 MCP tools (added `godot_import_glb`, `godot_import_obj`)

---

## [0.1.0] - 2026-05-01

### Added
- Initial alpha release.
- 12 MCP tools: status, STL import, velocity field loading, GPU particles, streamline animation, camera, lighting, PBR materials, web export, scene tree, config, headless verify.
- Godot 4.0 TCP bridge (port 9080, newline-delimited JSON) with 15 GDScript action handlers.
- Artifact depot (`~/.godot-mcp/depot/`), MCPB bundles, prefab catalog, workflow engine, prompt templates.
- MCP bridge federation (`MCP_BRIDGE_URLS`) for cross-server tool calling.
- Tauri 2.0 native wrapper scaffold.
