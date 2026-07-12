# godot-mcp — TODO (from assessment 2026-07-11)

Source: `docs/ASSESSMENT_2026-07-11.md`. This file tracks active work items.
Mark items off as completed and update CHANGELOG.md.

---

## ✅ ALL COMPLETED (2026-07-11 session)

### Standards & Security
- [x] `build.ps1` bundle `.env.example` not `.env` (was leaking API keys)
- [x] Bun migration: npm -> bun, `bun.lock`, `package-lock.json` deleted
- [x] `prefab-ui>=0.14.0` core dependency
- [x] `BUILD_LOG.md` created
- [x] 15 stale `.bak` files deleted from `src/`
- [x] `tauri.conf.json` nsis snake_case -> camelCase
- [x] `main.rs` `CommandExt` import added

### Tauri / Rust
- [x] `backend.rs` `free_port()` upgraded (multi-layer kill + 240s TIME_WAIT poll + UAC)
- [x] `main.rs` deduplicated (calls `backend::spawn_backend()`)
- [x] Bridge unused-const cleanup (no dead_code warnings)
- [x] NSIS installer built and verified (Rust + PyInstaller + NSIS)
- [x] `build.ps1` uses project-venv pyinstaller, bunx

### MCPB
- [x] Root `manifest.json` fixed (was double-stringified JSON)
- [x] `.mcpbignore` excludes `samples/` — 242 MB -> 377 KB
- [x] MCPB bundle rebuilt and validated

### Prefab UI Cards
- [x] 5 status cards: godot, itch, steam, fleet, workflows
- [x] viewport capture card

### Dashboard
- [x] Onboarding welcome card + Godot hint + Launch Bridge button
- [x] `start_bridge` MCP tool + REST + auto-detect
- [x] `godot_status` improved error messages
- [x] Live viewport preview (`GET /api/v1/viewport/live`)
- [x] `/fleet` page (exchange assets, World Labs status, pipeline)
- [x] Game Builder pipeline visualization (PipelineViz DAG)
- [x] `/plugins` page (install community plugins from GitHub)
- [x] Playwright e2e from 2 to 8 tests

### Game Builder
- [x] `just gb-smoke` — 4/4 steps pass
- [x] `godot_capture_viewport` GDScript + MCP tool + REST + Prefab
- [x] Two-pass GDScript validation (gdlint + godot --check-only) + LLM repair
- [x] Multi-node scene hierarchy (SceneSpec.children with recursive compose)
- [x] `godot_simulate_input` — input injection for agent playtesting
- [x] `godot_scene` portmanteau (add/remove/modify/save nodes as MCP tool)
- [x] `install_community_plugin` tool + REST + web UI
- [x] `generate_game_tests` — GUT test generation + runner
- [x] Procedural visuals enforcement in prompts
- [x] Plugin-aware GamePlan (auto-install plugins from spec)
- [x] Narrative + NPC support in GamePlan
- [x] `just gb-preview` — serve HTML5 export + open browser

### Vibecoder Runner (sample game)
- [x] 10 enemy types: Hallucinator, PromptInjector, Tokenmaxxer, ContextOverflow, ClaudeDesktop, Techbro, LegacyCode, TheVC, TheMeeting, TheDatacenter
- [x] 11 GDScript files, 329 lines, all gdlint-clean
- [x] Procedural terminal visuals
- [x] Carbon meter, Ship It! ultimate, score multiplier systems
- [x] Full README documentation

### Plugin Ecosystem
- [x] `install_community_plugin` module-level function (importable)
- [x] Plugin registry with 7 plugins (Dialogic, Behavior Tree, GUT, Aseprite Wizard, Terrain3D, Voxel, XR Tools)
- [x] `gdtoolkit>=4.5,<5` dev dependency
- [x] `just gdscript-lint` / `just gdscript-format-check`
- [x] `docs/godot-ecosystem.md` with full catalog

---

## REMAINING — High Impact

### Portmanteau consolidation (8h)
Collapse itch (6), steam (7), fleet (6) tool groups into three portmanteaus with
`operation` enum. Reduces 95 -> ~60 tools. Use FastMCP Transforms to project
individual operations as atomic tools to the host.

### Game Builder E2E with worlds (4h)
`just gb-smoke` validates design->logic pipeline but skips world generation
(needs worldlabs-mcp) and scene composition (needs bridge). A full E2E test
with Marble world generation + scene compose + export would prove the entire
pipeline end-to-end.

### GDScript test runner (GUT) polish (2h)
`generate_game_tests` exists but needs: better test generation prompts, CI
integration, and automatic test running after `build_game()`. The GUT CLI
invocation is fragile (depends on exact godot path + addon path).

---

## REMAINING — Medium Impact

### Bridge disconnect-reconnect stability test (2h)
Kill Godot bridge mid-operation, verify graceful degradation + recovery.

### Game Builder tutorial (2h)
A "Build Your First Game" walkthrough document showing the full pipeline.

### Plugin install E2E test (1h)
Test that installs GUT into a temp Godot project, verifies addon exists.

### Procedural sprite generation tool (2h)
`godot_generate_procedural_texture` — create textures at runtime via bridge.

---

## REMAINING — Low Impact

### Dialogic timeline generation (3h)
Generate Dialogic `.dtl` timeline files from GamePlan narrative + NPCs.

### Splat import decision (0.5h)
Adopt a Godot 4 gaussian-splat GDExtension or close the R&D item.

### Ubuntu lint-only CI job (0.5h)

### Portmanteau registration test (1h)

### gb-demo script (2h)

---

## Effort Summary

| Category | Remaining | Est. |
|----------|-----------|------|
| Structural | Portmanteau consolidation | 8h |
| Testing | Game Builder E2E with worlds | 4h |
| Testing | Bridge disconnect-reconnect | 2h |
| Testing | GUT polish | 2h |
| Testing | Plugin install E2E | 1h |
| Testing | Portmanteau registration | 1h |
| Game Builder | Procedural sprite tool | 2h |
| Game Builder | Narrative -> Dialogic timelines | 3h |
| Docs | Tutorial | 2h |
| Docs | gb-demo script | 2h |
| Misc | Splat decision | 0.5h |
| Misc | Ubuntu CI | 0.5h |
| **Total** | | **~28h** |
