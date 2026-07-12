# Changelog

All notable changes to **godot-mcp** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (2026-07-11 web_sota/ -> webapp/ rename)
- **WEBAPP_DIRECTORY_STANDARD.md** — fleet standard: frontend dir MUST be `webapp/`, not `web_sota/`. The SOTA naming was redundant — every repo we build is SOTA.
- **godot-mcp migrated** — `web_sota/` renamed to `webapp/`. 14 files updated (justfile, tauri.conf.json, build.ps1, start.ps1, .mcpbignore, docs, Dockerfile, scripts). TypeScript, tests, ruff all clean.

### Added (2026-07-11 Release tiers standard)
- **`RELEASE_TIERS.md`** — fleet standard codifying T1 (MCPB only), T2 (webapp), T3 (NSIS). NSIS is explicitly the last step, not the first. MCPB is the default artifact. Tier assignment table for all fleet repos.
- **`RELEASE_TIER.md`** — per-repo tier markers for godot-mcp (T3), fleet-agent-mcp (T2).
- **README badge** — `tier:T3-desktop` badge added.

### Added (2026-07-11 LLM detect + recommend endpoints)
- **GPU detection** — `GET /api/v1/llm/detect` probes GPU via nvidia-smi (name, VRAM, driver), checks Ollama presence + installed models. Pure Python, no external deps.
- **Model recommendation** — `GET /api/v1/llm/recommend` returns tier (1-5), recommended model, install status, cloud fallback (DeepSeek V4 Flash). Algorithm walks VRAM tiers from best to worst, picks first installed model.
- **Settings page GPU card** — shows detected GPU, VRAM, recommended model, install status, guidance message. Falls back to cloud config hint when no local LLM available.
- **Fleet template** — `mcp-central-docs/templates/llm-detect/detect.py` mirrored for repo reuse with version constant.

### Added (2026-07-11 Portmanteau consolidation + Gemma 4 model)
- **S1: Portmanteau consolidation** — `itch_ops`, `steam_ops`, `fleet_ops` portmanteau tools added (19 -> 6, 20 -> 7, 6 -> 1). Each with `operation: Literal[...]` enum. Individual tools kept alongside for backward compatibility.
- **Default Ollama model** — changed from `qwen3.5:27b` (nonexistent) to `gemma4:12b` (installed, fast, multimodal, fits RTX 4090). Updated in `sampling/service.py` and all docs.

### Added (2026-07-11 Vibecoder Runner — expanded enemy roster)
- **6 new enemy types** (10 total GDScript files, 329 lines, all gdlint-clean):
  - **ClaudeDesktop** — immobile desk. Bump into it for "I apologize..." stun (3s). Chain-of-thought beam pulses. Fixed at lower screen position.
  - **Techbro** — fast chaser. Drops "synergy!" / "pivot!" jargon mines. On first death, splits into Techbro 2.0 (Now With AI, pink). On second death, spams "We're hiring!".
  - **LegacyCode** — scrolling floor hazard (COBOL). Slows player. GOTO teleport on contact (random reposition). Visual: brown COBOL strip.
  - **TheVC** — appears when score > 100. Asks "VALUATION?" then takes 50% equity (halves score). 15s cooldown between visits. Yellow suit.
  - **TheMeeting** — calendar invite swarm that chases. Catches you = "45-min status update" (4s stun). Message: "could have been an email."
  - **TheDatacenter** — background hazard (built into main scene). Carbon meter rises from cooling + fans. Fan blast pushes player. Water pipe burst obstacles. Carbon hit 100% = EPA fines, game over.

### Added (2026-07-11 Vibecoder Runner game demo)
- **Vibecoder Runner** — playable Godot 4 game in `samples/vibecode-runner/`. 2D side-scrolling runner featuring:
  - **5 AI-themed enemies**: Hallucinator (teleporting glitch), PromptInjector (control hacker), Tokenmaxxer Bankruptor (score drain), Context Window Overflow (shrinking walls), Merge Conflict (splitting clone)
  - Procedural terminal visuals (green-on-black, ASCII/tech aesthetic)
  - Score as LOC (Lines of Code), energy drink multiplier, "Ship It!" ultimate
  - All GDScript passes `gdlint` clean
  - Game generated via the Game Builder pipeline: `design_game` -> GamePlan -> procedural visual enforcement -> gdlint validation

### Added (2026-07-11 Narrative + NPC support)
- **G5: Narrative & NPCs in GamePlan** — new `NarrativeArc` (premise, acts, tone) and `NPCSpec` (name, role, dialogues, position) schema types. `build_game()` auto-adds `dialogic` to plugins when narrative/NPCs are present. Summary shows story tone and NPC count. Design prompt includes narrative/npc rules.

### Added (2026-07-11 Scene portmanteau + pipeline viz)
- **S2: `godot_scene` portmanteau MCP tool** — consolidates 4 bridge-only REST actions (`add_node`, `remove_node`, `modify_node`, `save_scene`) into a single MCP tool with `operation: Literal[...]`. Now accessible from MCP clients, not just REST.
- **W3: Game Builder pipeline visualization** — `PipelineViz` DAG component showing Design → Worlds → Compose → Logic → Export → Ship with live status (idle/running/done/failed). Step cards highlight green on completion. "Build Full Game" button runs the entire pipeline and updates all steps.

### Added (2026-07-11 Procedural visuals + plugin-aware GamePlan)
- **G3: Procedural visual enforcement** — `GDScript_SPEC_PROMPT` now includes concrete procedural visual examples (ColorRect, Polygon2D, GradientTexture2D, draw_circle, star polygon vertices, health bar pattern). GamePlan schema gains `procedural_visuals` field with palette + style.
- **E2: Plugin-aware GamePlan** — `GamePlan.plugins: list[str]` field. `build_game()` auto-installs plugins via `install_community_plugin` during the pipeline. Design prompt includes plugin rule.
- **`SceneSpec` recursive typing** — fixed with `model_rebuild()` for Pydantic v2 forward reference.

### Added (2026-07-11 Input injection + preview)
- **G1: `godot_simulate_input` MCP tool** — sends keyboard events via `Input.parse_input_event()` in the Godot bridge. Accepts `actions: [{"key": "Space", "pressed": true, "hold_ms": 100}]`. Chains with `godot_capture_viewport` for agent playtesting loops. GDScript handler + Python tool + REST `POST /api/v1/viewport/simulate`.
- **G4: `just gb-preview`** — serves the latest HTML5 export via Python http.server and opens browser. Finds export under `build/little-game/`. Configurable port (default 10994). Auto-cleans stale port.

### Added (2026-07-11 GUT test runner)
- **P2: `generate_game_tests` MCP tool** — generates GUT test scripts for generated game logic. Auto-installs GUT plugin via `install_community_plugin`, creates `test/unit/test_*.gd` from `GDSCRIPT_TEST_PROMPT`, runs tests via `godot --headless -s addons/gut/gut_cmdln.gd`, parses PASS/FAIL counts. Returns test results + run output.
- **`GDSCRIPT_TEST_PROMPT`** — new prompt template for GUT test generation. Instructs LLM to write `extends GutTest` scripts with `assert_eq()`, `assert_true()`, `watch_signals()`, and test coverage of core mechanics.
- **`install_community_plugin` refactored** — extracted to module-level async function for programmatic use from other modules (not just as MCP tool).

### Added (2026-07-11 Multi-node scene hierarchy)
- **P1: Multi-node scene hierarchy** — `SceneSpec` now supports `children: list[SceneSpec]` for nested node trees. `compose_game_scene` recursively walks the tree and creates nodes with proper parenting via the bridge `add_node` action. GamePlan can now describe `Player -> Camera`, `World -> Terrain -> Collision`, `UI -> HUD -> Healthbar` hierarchies.
- **`KNOW_NODE_TYPES`** — expanded node type set (60+ Godot 4 node types) used by the recursive scene composer.
- **Design prompt** — updated `GAME_DESIGNER_SYSTEM_PROMPT` example to show nested scene `children` in the JSON schema.

### Added (2026-07-11 Dashboard depth + fleet page)
- **W1: Live viewport preview** — `GET /api/v1/viewport/live` returns the latest Godot viewport capture as PNG (or SVG placeholder when bridge is down). Dashboard shows auto-refreshing `<img>` with Refresh button when bridge is connected. Viewport directory served via StaticFiles at `/viewport/`.
- **W2: `/fleet` page** — Fleet Exchange dashboard: asset count KPI, World Labs bridge status, mesh/splat import availability, exchange asset grid, pipeline diagram. Sidebar entry under Fleet group.
- **`VIEWPORT_DIR`** config — `~/.godot-mcp/viewport/`, configurable via `GODOT_MCP_VIEWPORT_DIR` env.

### Added (2026-07-11 Godot ecosystem + plugin registry)
- **`install_community_plugin` MCP tool** — downloads and installs Godot community plugins from GitHub (latest release or main branch). Registry includes: Dialogic, Godot Behavior Tree, GUT, Aseprite Wizard, Terrain3D, Godot Voxel, Godot XR Tools. Extends `addon_tools.py`.
- **`PLUGIN_REGISTRY`** — extensible dict in `addon_tools.py`. Adding a new plugin is a one-line entry.
- **`docs/godot-ecosystem.md`** — comprehensive catalog: gdtoolkit rules table, plugin power ranking (4 tiers), GitHub repo refs for every plugin, install-community-plugin usage, Godot CLI flags, fleet pipeline diagram, extending guidelines.
- **`just gdscript-lint`** / **`just gdscript-format-check`** — run gdlint and gdformat on all `.gd` files.
- **`gdtoolkit>=4.5,<5`** — added to dev dependencies.

### Added (2026-07-11 Phase A: Game Builder depth)
- **`godot_capture_viewport` MCP tool** — captures the Godot viewport as PNG. Enables agent verify-loops ("did the scene load?"), README screenshots, and in-dashboard scene preview. Bridge action + Python tool + REST `POST /api/v1/viewport/capture`.
- **GDScript validation + auto-repair** — after `generate_game_logic`, each script is validated via `godot --headless --check-only`. If compilation fails, the error text is fed back to the LLM for up to 2 repair attempts. Catches silent game-breakers before export.
- **`show_viewport_card` Prefab tool** — in-chat viewport capture card via `@mcp.tool(app=True)`.
- **`just gb-smoke`** — Game Builder E2E smoke test
- **`just gb-smoke`** — Game Builder E2E smoke test: `design_game` -> GamePlan validation -> GDScript generation -> GDScript syntax check. Uses Ollama. 4/4 steps pass. Verifies the entire prompt-to-code pipeline works.
- **`scripts/gb-smoke.py`** — standalone smoke test script. Skips gracefully if no LLM is available.
- **`GamePlan.from_json` resilient parsing** — strips null values from LLM JSON output so pydantic defaults apply; handles `Literal` field variations (e.g. `"web|windows"` -> `"web"`).
- **`start_bridge` MCP tool** — locates Godot and launches it headless with the bridge addon. No more manual `just godot-bridge` for users who prefer the UI.
- **`POST /api/v1/bridge/start` REST endpoint** — programmatic bridge launch from the dashboard or scripts.
- **`GET /api/v1/godot/find` REST endpoint** — check if Godot is installed and where.
- **Dashboard onboarding** — welcome card with 3-step quickstart, Godot installation guidance, and "Launch Godot Bridge" button when bridge is down. Dismissible.
- **`godot_status` error messages** — now detect if Godot is installed but bridge is down, and guide the user to `start_bridge()` or `just godot-bridge` accordingly.
- **Prefab UI card tools** — 5 new `@mcp.tool(app=True)` cards: `show_godot_status_card`, `show_itch_status_card`, `show_steam_status_card`, `show_fleet_status_card`, `show_workflows_card`. Returns `ToolResult` with `PrefabApp` in capable hosts; plain text fallback. Fleet Prefab standard compliance (SOTA_REQUIREMENTS §2.2).
- **`prefab-ui>=0.14.0`** — core dependency added. Fleet mandatory for list/status/stats Prefab surfaces.
- **Bun migration** — `webapp` migrated from npm to Bun (`bun.lock` replaces `package-lock.json`). All justfile recipes, `build.ps1`, `tauri.conf.json` pre-commands, and start scripts use `bun`/`bunx`. Fleet BUN_STANDARDS compliance.
- **`@biomejs/biome` in devDependencies** — explicit, no longer fetched via `npx`.
- **`BUILD_LOG.md`** — build gate record for NSIS installer auditing.

### Fixed (2026-07-11)
- **`build.ps1` bundled `.env` instead of `.env.example`** — SECURITY: dev `.env` contains personal API keys (OpenAI, Steam, Discord). Changed to bundle `.env.example` only.
- **PyInstaller `console=True`** — showed cmd window on launch. Changed to `console=False`.
- **15 stale `.bak` files** in `src/` — deleted.
- **`main.rs` duplicated `backend.rs` spawn logic** — now calls `backend::spawn_backend()` instead of maintaining inline copy. `main.rs` reduced from 95 to 49 lines.
- **`backend.rs` `free_port()` upgraded** — multi-layer kill (Stop-Process + taskkill + port kill + UAC escalation) with 240s TIME_WAIT polling. Prevents orphan backend zombies.
- **`tauri.conf.json` NSIS config** — fixed snake_case to camelCase (`install_mode` → `installMode`, `installer_hooks` → `installerHooks`) for Tauri 2.0 schema compliance.
- **`main.rs` missing `CommandExt` import** — added `use std::os::windows::process::CommandExt`.
- **Root `manifest.json`** — was double-stringified JSON string; replaced with proper JSON object. MCPB pack now passes validation.
- **CUA smoke script header** — said "pywinauto-mcp canary", fixed to "godot-mcp".
- **`.mcpbignore` excludes `samples/`** — slashed MCPB package size from 242 MB to 377 KB.

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
- **Versions unified at 0.3.0** — pyproject, justfile `VER`, webapp `package.json`, Tauri conf, bridge `plugin.cfg`, MCPB manifest; the server reads its version from package metadata.

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
- **Tauri 2.0 native app** (`native/`): PyInstaller sidecar `godot-mcp-backend`, auto-starts MCP on 10993, bundles `webapp` dashboard. Build: `just tauri-build`. Scripts: `native/build.ps1`, `build-sidecar.ps1`, `scripts/generate-tauri-icon.ps1`, `scripts/patch-platformer-godot44.ps1`.
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
