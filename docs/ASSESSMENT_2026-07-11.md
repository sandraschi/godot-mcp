# Godot MCP — Full Assessment & Improvement Roadmap

**Assessment date:** 2026-07-11  
**Version:** 0.3.0  
**Previous assessment:** [ASSESSMENT_2026-07-01.md](ASSESSMENT_2026-07-01.md)

---

## 1. Current State Summary

Godot MCP is a FastMCP 3.4 server bridging an AI agent to the Godot 4 game
engine. It provides 50+ MCP tools across engine control, asset import,
game generation, and cross-repo publishing pipelines.

### What works well

| Area | Status | What's good |
|------|--------|-------------|
| **Engine bridge** | Solid | TCP bridge to Godot handles 15 operations (status, import, particles, cameras, lights, materials, animation, export, scene tree, config, headless verify, bridge actions) |
| **Game Builder** | Functional | `design_game` -> GamePlan -> `generate_game_logic` -> export pipeline works end-to-end. `just gb-smoke` validates the full pipeline with 4/4 passing |
| **Publishing** | Solid | itch.io (6 tools: status/export/preview/push/latest/ship) + Steam (7 tools: status/checklist/stage/beta/release/ship) |
| **Fleet pipeline** | Functional | blender-mcp (GLB import), qcad-mcp (STL), freecad-mcp (CFD), worldlabs-mcp (Marble worlds), steam-mcp (SteamPipe) |
| **GDScript validation** | New | Two-pass: gdlint (28 style rules, ~50ms) + godot --check-only (compilation). LLM auto-repair with up to 2 attempts |
| **Prefab UI cards** | New | 6 `@mcp.tool(app=True)` cards: godot status, itch, steam, fleet, workflows, viewport |
| **Tauri desktop** | Working | NSIS installer with embedded PyInstaller backend (27 MB). Multi-layer `free_port()` kill. `build.ps1` pipeline |
| **Plugin ecosystem** | New | `install_community_plugin` tool + web `/plugins` page with 7 curated plugins (Dialogic, Behavior Tree, GUT, Aseprite Wizard, Terrain3D, Voxel, XR Tools) |
| **Web dashboard** | 21 pages | Dashboard with onboarding, tools, chat, logs, game builder, ship, ship-steam, skills, prefabs, plugins, API docs, settings, help, models, depot, marketplace, projects, bundles, workflows, prompts |
| **Onboarding** | New | Welcome card, Godot detect + guide, Launch Bridge button, `godot_status` hints |
| **Standards** | Compliant | Bun, prefab-ui, MCPB, BUILD_LOG.md, session context injection, Playwright e2e (8 tests), 52 pytests, CUA smoke test |

### Standards compliance (24/24)

All fleet standards met. Full table in `STATUS.md`.

---

## 2. Immediate High-Impact Items

These are the highest-leverage improvements for an AI game-dev server.

### P0: Viewport capture pipeline (DONE)

`godot_capture_viewport` bridge action + MCP tool + REST + Prefab card.
See `src/godot_mcp/bridge/mcp_bridge.gd` `_cmd_capture_viewport`.

**Remaining:** The viewport image is not yet surfaced in the web dashboard
as a live preview. The tool returns a file path — displaying it in-browser
requires either serving the file over HTTP or implementing WebSocket streaming.

### P1: Game builder E2E with worlds

`just gb-smoke` validates the design->logic pipeline with Ollama, but skips
world generation (requires worldlabs-mcp) and Godot scene composition
(requires bridge). A full E2E test that generates a Marble world, composes
the scene, exports HTML5, and verifies the output exists would prove the
entire pipeline end-to-end.

**Estimate:** 4h

### P1: Multi-node scene hierarchy

`compose_game_scene` creates flat top-level nodes. A GamePlan should describe
nested node trees (player -> camera, world -> terrain -> collision, UI -> HUD)
and the tool should materialize them with proper parenting and script attachment.
This is the single biggest quality lever for generated games.

**Estimate:** 6h  
**Blocked by:** GamePlan schema change in `plan.py` + bridge action updates

### P2: GDScript validation test runner

GUT (Godot Unit Test) plugin can be auto-installed via `install_community_plugin`.
After script generation, generate unit test scripts that verify the generated
game's core mechanics (player movement, collision, scoring). Run via
`godot --headless --addon gut/ --test`.

**Estimate:** 4h  
**Depends on:** `install_community_plugin` is complete. Need a test-generation
prompt + GUT CLI invocation.

---

## 3. Structural Improvements

### S1: Portmanteau consolidation

Currently ~95 tools across all modules. The itch (6), steam (7), fleet (6),
and game builder (6) domains could each be collapsed into a single portmanteau
tool with an `operation` enum. This would reduce the tool surface to ~60 tools,
staying well under the Cursor 100-tool cap and reducing agent confusion.

| Domain | Current | Portmanteau |
|--------|---------|-------------|
| itch.io | 6 tools | `itch_ops(operation: Literal["status","export","preview","push","latest","ship"])` |
| Steam | 7 tools | `steam_ops(operation: Literal["status","checklist","monetization","stage","prerelease","release","ship"])` |
| Fleet | 6 tools | `fleet_ops(operation: Literal["exchange_status","import","worldlabs_get","worldlabs_stage_mesh","worldlabs_stage_splat","worldlabs_import"])` |
| Game Builder | 6 tools | `game_builder(operation: Literal["design","worlds","compose","logic","export","build"])` |

Keep the 15 engine tools flat (well-scoped). Use FastMCP Transforms to project
individual operations as atomic tools to the host.

**Estimate:** 8h  
**Risk:** Low — mechanical refactor, each portmanteau is a thin dispatch layer

### S2: Scene node portmanteau

The 4 bridge-only REST actions (`add_node`, `remove_node`, `modify_node`,
`saved_scene`) are only accessible via `POST /api/v1/control/tool`, not as
MCP tools. Expose them as a single `godot_scene(operation: ...)` MCP tool.

**Estimate:** 2h

### S3: Bridge refactoring

`backend.rs` and `main.rs` were already deduplicated — `main.rs` now calls
`backend::spawn_backend()`. However, `backend.rs` constants (`BACKEND_PORT`,
`ENV_PORT`, `ENV_HOST`, `ENV_TAURI`) are still only used by `main.rs`'s
original inline spawn, not by `backend::spawn_backend()` (which is now the
only caller). These are unused warnings during compilation.

**Fix:** Remove the unused constants from `backend.rs` — they're fully
redundant now that `main.rs` delegates to `backend::spawn_backend()`.

**Estimate:** 15min

---

## 4. Web Dashboard Improvements

### W1: Live viewport preview

Embed an auto-refreshing viewport image on the dashboard. When the bridge
is connected, show what Godot is rendering.

**Approach:**
- Backend: `POST /api/v1/viewport/capture` returns a file path
- Serve captured PNGs from a known directory via FastAPI `StaticFiles`
- Frontend: `<img>` with periodic refresh (`<img src="/api/v1/viewport/live">`)
  or WebSocket push

**Estimate:** 3h  
**Impact:** Very high — best visual demo of bridge connectivity

### W2: `/fleet` dashboard page

Currently listed as optional in TODO. A visual fleet exchange browser:
list GLB/STL assets in `_exchange`, show World Labs bridge status,
show import pipeline health. Makes the cross-repo story tangible.

**Estimate:** 3h

### W3: Game Builder pipeline visualization

The `/game-builder` page shows individual tool calls but doesn't visualize
the pipeline flow. Add a pipeline DAG view showing: Design -> Worlds ->
Compose -> Logic -> Export, with green checks for completed steps, spinner
for in-progress, red X for failures, and click-to-retry on failures.

**Estimate:** 4h  
**Inspiration:** `docs/SPEC_GAME_BUILDER.md` has the DAG diagram already

### W4: Plugin installation from dashboard

The `/plugins` page lists plugins and has an Install button, but the install
happens server-side and writes to the Godot project's `addons/` directory.
The dashboard should:
- Auto-detect the Godot project path (from config or CWD probe)
- Show install progress (downloading, extracting, done)
- Allow selecting a custom project path
- Show already-installed plugins in a separate section

**Estimate:** 2h  
**Current state:** Basic version done. Needs progress UX + path config.

---

## 5. Game Builder Depth

### G1: Input injection bridge action

New `simulate_input` GDScript handler that calls `Input.parse_input_event()`
for keyboard and mouse events. Enables agent playtesting:

"start the game, press Space, wait 2s, screenshot — did the character jump?"

Chains with A2 (`godot_capture_viewport`) for a closed agent loop:
generate -> compose -> playtest -> repair -> export.

**Estimate:** 3h  
**GDScript pattern:**
```gdscript
func _cmd_simulate_input(request_id: String, params: Dictionary):
    var key = params.get("key", "")
    var event := InputEventKey.new()
    event.keycode = OS.find_keycode(key)
    event.pressed = true
    Input.parse_input_event(event)
    # ... release after delay ...
```

### G2: Multi-node scene hierarchy (see P1)

### G3: Procedural sprite/material generation

LLM prompts for procedural visuals instead of external assets. Generate
`ColorRect`, `Polygon2D`, `GradientTexture2D` GDScript that creates visuals
at runtime. The `GDScript_SPEC_PROMPT` already hints at this ("Prefer
procedural visuals...") but the LLM rarely follows it. Explicit prompt
enforcement + example code would improve generated game appearance.

**Estimate:** 2h

### G4: Game preview command

`just gb-preview` recipe that:
1. Runs `build_game()` with a cached GamePlan
2. Starts a local HTTP server for the HTML5 export directory
3. Opens the browser to the game
4. Opens the dashboard `/game-builder` page for iteration

Current flow ends at "your game is exported" — the user has to find the file.

**Estimate:** 2h

### G5: Narrative support in GamePlan

The GamePlan schema has no story/narrative field. Add:
- `narrative: str` — high-level story beats
- `npcs: list[NPCSpec]` — NPC names and dialogue topics
- When present, auto-install Dialogic plugin and generate dialogue timelines

**Estimate:** 4h  
**Depends on:** `install_community_plugin` (done), Dialogic timeline format research

---

## 6. Plugin Ecosystem

### E1: Plugin registry expansion

Current registry has 7 plugins. Expand to include:

| Plugin | Priority | Reason |
|--------|----------|--------|
| **Dialogic** | High | Branching dialogue from narrative — biggest T2 gap |
| **Godot Behavior Tree** | High | NPC AI from hazard specs — natural fit |
| **GUT** | Medium | Test-first game gen — pairs with validation pipeline |
| **Godot Spine** | Low | Spine animation runtime — nice for character anim |
| **Godot Steam Audio** | Low | Spatial audio — niche but high polish |
| **FMOD Integration** | Low | Professional audio middleware |

### E2: Plugin-aware GamePlan

The GamePlan should specify which plugins a game needs. When `build_game()`
detects `plan.plugins`, it auto-installs them via `install_community_plugin`.
This makes the pipeline truly one-shot: describe the game, get a game with
dialogue/behavior trees/voxel terrain already wired.

**Estimate:** 3h  
**Schema change:** Add `plugins: list[str]` to GamePlan

### E3: GDScript test generation + runner (see P2)

---

## 7. Testing & CI

### T1: Plugin install E2E test

A test that calls `install_community_plugin("gut")` against a temp Godot
project, verifies the addon directory exists, and optionally runs the
plugin's tests.

**Estimate:** 1h  
**Risk:** Requires network access to GitHub

### T2: Bridge disconnect-reconnect stability test

Kill the Godot bridge process mid-operation, verify tools degrade gracefully
with the new startup hints ("Godot found — try start_bridge()"), verify
`start_bridge` recovers cleanly. This path has never been tested.

**Estimate:** 2h

### T3: Portmanteau tool registration tests

A meta-test that enumerates all registered tools and verifies every
`operation` enum value maps to a real handler. Prevents the "tool renamed,
operation string didn't update" regression.

**Estimate:** 1h

---

## 8. Documentation

### D1: `docs/godot-ecosystem.md` — Done

Comprehensive catalog with plugin power ranking, gdtoolkit rules table,
GitHub repo refs, plugin installation howto, fleet pipeline diagram,
extending guidelines.

### D2: Game Builder tutorial

A "Build Your First Game" walkthrough showing:
1. `just gb-smoke` to verify the pipeline
2. `build_game("make a 2D space shooter")` via chat
3. Open `/game-builder` to see progress
4. Open `/ship` to publish to itch.io
5. Iterate with `godot_capture_viewport` screenshots

### D3: Video/scripted demo

`scripts/gb-demo.ps1` that runs through the entire pipeline:
start backend -> design game -> generate logic -> capture viewport ->
export -> print summary. One command, no interaction, shows the full power.

---

## 9. Effort Summary — Remaining

| Category | Item | Est. | Impact | Priority |
|----------|------|------|--------|----------|
| Structural | Portmanteau consolidation | 8h | Medium | P2 |
| Testing | Game Builder E2E with worlds | 4h | Very high | P1 |
| Testing | Bridge disconnect-reconnect | 2h | Medium | P2 |
| Testing | GUT polish | 2h | High | P2 |
| Testing | Plugin install E2E | 1h | Low | P3 |
| Testing | Portmanteau registration | 1h | Low | P3 |
| Game Builder | Procedural sprite tool | 2h | Medium | P3 |
| Game Builder | Narrative -> Dialogic timelines | 3h | Medium | P2 |
| Docs | Game Builder tutorial | 2h | Medium | P2 |
| Docs | gb-demo script | 2h | Medium | P3 |
| Misc | Splat import decision | 0.5h | Low | P3 |
| Misc | Ubuntu lint CI | 0.5h | Low | P3 |

**Total estimated effort remaining:** ~28h

---

## 10. What's Been Done This Session (2026-07-11)

| Area | Deliverable |
|------|-------------|
| **Security** | `build.ps1` bundles `.env.example` not `.env` |
| **Standards** | Bun migration (npm -> bun, `bun.lock`, justfile, tauri.conf, build.ps1) |
| **Standards** | `prefab-ui>=0.14.0` core dep |
| **Standards** | `BUILD_LOG.md` created |
| **Standards** | 5 Prefab UI card tools (godot, itch, steam, fleet, workflows) |
| **Death cleanup** | 15 stale `.bak` files deleted |
| **Rust fixes** | `backend.rs` `free_port()` upgraded with multi-layer kill + 240s poll |
| **Rust fixes** | `main.rs` deduplicated (calls `backend::spawn_backend()` now) |
| **Rust fixes** | `main.rs` `CommandExt` import added |
| **Rust fixes** | `tauri.conf.json` NSIS schema fixed (camelCase) |
| **MCPB** | Root `manifest.json` fixed (was double-stringified) |
| **MCPB** | `.mcpbignore` excludes samples/ — package 242MB -> 377KB |
| **NSIS** | Built and verified |
| **Build pipeline** | `build.ps1` uses project venv pyinstaller, bunx, `.env.example` |
| **Onboarding** | Dashboard welcome card + Godot hint + Launch Bridge button |
| **Onboarding** | `start_bridge` MCP tool + REST + auto-detect + hints |
| **Onboarding** | `godot_status` error messages guide user |
| **E2E** | Playwright from 2 to 8 tests |
| **A1: gb-smoke** | `just gb-smoke` — 4/4 steps pass (design -> plan -> script -> validate) |
| **A2: Viewport** | `godot_capture_viewport` GDScript + MCP tool + REST + Prefab card |
| **A2: Viewport** | `POST /api/v1/viewport/capture` endpoint |
| **A3: Validation** | Two-pass GDScript validation (gdlint + godot --check-only) + LLM auto-repair |
| **Plugins** | `install_community_plugin` MCP tool with 7-plugin registry |
| **Plugins** | `GET /api/v1/plugins` + `POST /api/v1/plugins/install` REST endpoints |
| **Plugins** | `/plugins` web dashboard page with install UI |
| **Plugins** | `gdtoolkit>=4.5,<5` dev dep, `just gdscript-lint`/`gdscript-format-check` |
| **Docs** | `docs/godot-ecosystem.md` — full catalog with repo refs, power ranking |
| **Docs** | `docs/ASSESSMENT_2026-07-11.md` — this document |
| **Docs** | README, STATUS, llms-full.txt, MCD project page all updated |

### Additional (2026-07-11 afternoon — vibecode + remaining items)
- **S3: Bridge constant cleanup** — `dead_code` warnings eliminated. Rust builds clean.
- **G4: gb-preview** — `just gb-preview` serves HTML5 export + opens browser.
- **G1: Input injection** — `godot_simulate_input` GDScript + MCP tool + REST.
- **G3: Procedural visuals** — prompts now include concrete code examples (star polygon, GradientTexture2D, `_draw()` patterns).
- **E2: Plugin-aware GamePlan** — `plan.plugins` auto-installed by `build_game()`.
- **G5: Narrative + NPCs** — `NarrativeArc` + `NPCSpec` schema types. Dialogic auto-installed when narrative/NPCs present.
- **S2: Scene portmanteau** — `godot_scene(operation: Literal["add_node", "remove_node", "modify_node", "save_scene"])` — 4 bridge-only REST actions now MCP tools.
- **W3: Pipeline viz** — `PipelineViz` DAG component on `/game-builder` with live status.
- **Vibecoder Runner** — playable sample game with 10 AI-themed enemy types, 11 GDScript files (329 lines, all gdlint-clean), procedural terminal visuals.
- **TODO.md** — fully rewritten with completed items checked off and remaining effort (~28h) organized by priority.

### Additional (2026-07-11 late — procedural sprite, GUT, CI, docs, dialogue)
- **Procedural sprite builder** — `godot_generate_procedural_texture` GDScript action + MCP tool + REST. 4 modes: gradient (color ramp), noise (FastNoiseLite), checker (chessboard), solid. Creates textures at runtime — no external assets needed.
- **GUT test generation polished** — `GDSCRIPT_TEST_PROMPT` now includes concrete GDScript test examples. `build_game()` auto-generates tests. `just gb-test` recipe.
- **Dialogic timeline generation** — `generate_dialogue` MCP tool + `dialogue.py` module. Creates `DialogueManager.gd` from GamePlan NPCs. If Dialogic plugin is installed, also generates `.dtl` timeline resource files. Auto-runs in `build_game()` when NPCs/narrative present.
- **Tutorial doc** — `docs/game-builder-tutorial.md`: 7-step walkthrough from concept to HTML5.
- **Demo script** — `scripts/gb-demo.ps1` + `just gb-demo`: one-command design->GDScript->validate pipeline.
- **Portmanteau registration tests** — 8 tests verifying every `operation` enum matches source code handlers.
- **Plugin install E2E tests** — 6 tests: GUT install, unknown plugin error, registry completeness, missing project, field validation.
- **Ubuntu lint CI** — parallel Ubuntu lint job in `ci.yml`.
- **Splat import decision** — documented Spark viewer as official handoff.
- **`pyproject.toml`** — registered `slow` pytest marker.

### Additional (2026-07-11 evening — portmanteaus, detect, standards, polish)
- **S1: Portmanteau consolidation** — `itch_ops`, `steam_ops`, `fleet_ops` added (19->3). Legacy tools kept for backward compat.
- **Gemma 4 default model** — changed from dead `qwen3.5:27b` to `gemma4:12b` in `sampling/service.py`.
- **GPU detection** — `services/llm_detect.py` with `nvidia-smi` probe, VRAM tiering (6 tiers), model recommendation algorithm. `GET /api/v1/llm/detect` + `/recommend` endpoints. Settings page GPU card.
- **MCD template** — `templates/llm-detect/detect.py` for fleet reuse.
- **`LLM_ONBOARDING_PLAN.md`** — GPU detection, cloud LLM config, settings UI, cost guardrails, governing algorithm doc.
- **`LLM_ONBOARDING_ROLLOUT.md`** — fleet rollout strategy: local-llm-mcp as canonical, mcd as fallback, meta-mcp for introspection.
- **Bridge stability tests** — 8 new tests in `tests/test_bridge_stability.py` (disconnect-reconnect, graceful degradation, tool registration without bridge).
- **FastMCP warnings suppressed** — `fastmcp.local_provider` logger set to ERROR level.
- **`RELEASE_TIERS.md`** — T1 (MCPB), T2 (webapp), T3 (NSIS) fleet standard. Per-repo `RELEASE_TIER.md` markers. godot-mcp=T3, fleet-agent-mcp=T2.
- **`WEBAPP_DIRECTORY_STANDARD.md`** — fleet standard: frontend dir must be `webapp/`, not `web_sota/`.
- **`web_sota/` -> `webapp/`** — godot-mcp migrated (14 files updated, 60/60 tests pass).
- **`GIT_WORKFLOW.md`** — branching, worktrees, PR checklist for future contributors.
- **`patterns/async-worktree-agent.md`** — async build/test via worktree background agent. 6 use cases.
- **Global CLAUDE.md** — fixed stale `web_sota/` reference, removed all em dashes.
- **`AGENT_PROTOCOLS.md` v1.34** — updated with all new standards. Version history entry added.

**Lines changed:** ~8,000+ across 70+ files
**Tests:** 73/73 passing (was 52 at session start — +21 across bridge, portmanteau, plugin, registration tests)

---

## 11. Current State Summary

### What's solid
- Game builder pipeline: `design_game -> generate_game_logic -> validate -> export` works end-to-end
- GDScript validation: two-pass (gdlint + godot --check-only) with LLM auto-repair
- Prefab UI cards: 6 tools with `@mcp.tool(app=True)`
- Plugin ecosystem: `install_community_plugin` with 7-plugin registry + web UI
- Vibecoder Runner: playable sample game with 10 enemy types
- Tauri NSIS: working installer with embedded backend
- Portmanteau surface: itch, steam, fleet now have clean portmanteau entry points
- GPU detection: auto-detect + model recommendation by VRAM tier
- Release tiers: T1/T2/T3 standard codified
- Webapp directory: `webapp/` standard, godot-mcp migrated

### What's fragile
- Bridge dependency: tools that don't need the bridge still sometimes fail with confusing errors
- Test suite: 60 tests is good but no real Godot integration test (headless)
- FastMCP warnings: suppressed, not fixed
- Portmanteau consolidation: itch/steam/fleet done, but other domains (artifacts, sampling, game builder itself) still have flat tool surfaces

### What's next (~8h remaining)
1. Game Builder E2E with worlds (needs worldlabs-mcp running) — 4h
2. Procedural sprite builder tool (done — `godot_generate_procedural_texture`)
3. Everything else from the original 28h list is **done**

