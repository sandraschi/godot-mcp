# Changelog

All notable changes to **godot-mcp** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
- **Tool count**: 43 → 56 MCP tools (added 6 game_builder + 7 steam tools)

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
- Godot 4.0 WebSocket bridge (port 9080) with 15 GDScript action handlers.
- Artifact depot (`~/.godot-mcp/depot/`), MCPB bundles, prefab catalog, workflow engine, prompt templates.
- MCP bridge federation (`MCP_BRIDGE_URLS`) for cross-server tool calling.
- Tauri 2.0 native wrapper scaffold.
