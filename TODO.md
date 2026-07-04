# godot-mcp — TODO (from assessment 2026-07-01)

Source: `docs/ASSESSMENT_2026-07-01.md`. Estimates are AI-assisted dev time. Check items off and mark this file OBSOLETE when superseded.

**2026-07-02: P0 + P1 + quick P2 wins DONE (correctness sweep, see CHANGELOG). Verified: `just --list`, ruff check + format, 52/52 pytest, live boot on :10999 with working `/api/v1/status`, `/api/capabilities`, and a successful MCP initialize handshake at `/mcp`. `just tools` enumerates 93 tools. Remaining open items below.**

## P0 — Broken right now — ✅ ALL DONE 2026-07-02

- [x] **justfile parse fix** — `pack-mcpb` deleted; `just --list` verified.
- [x] **justfile `{{REPO}}` undefined** — replaced with `{{justfile_directory()}}`. (`npx` → `bunx` deliberately deferred to the Bun migration item.)
- [x] **ws_gateway LOG_RING ImportError** — rewritten against `activity_log.query_logs(after_id=...)`.
- [x] **`modify-node` phantom bridge action** — `modify_node` implemented in mcp_bridge.gd (`set_indexed`, path-or-name lookup); all callers fixed (ws_gateway + mobile_command + mobile_help docs).
- [x] **Sampling dead over REST/dashboard** — fallback chain implemented: `ctx.sample()` → OpenAI-compatible API (`GODOT_MCP_LLM_BASE_URL/_API_KEY/_MODEL`) → Ollama (`GODOT_MCP_OLLAMA_URL/_MODEL`, default qwen3.5:27b); raises `SamplingUnavailableError` instead of fake-success string.
- [x] **sample_text result handling** — `.text` / content-block extraction; `system_prompt=` param.
- [x] **MCPB bundle rebuild** — stale `mcpb/src/` deleted (incl. .pyc); root `manifest.json` with `${__dirname}`; path-robust root `run_server.py`; packing root-level via `just mcpb-pack`. Still to do at next release: `bunx @anthropic-ai/mcpb validate` + actual pack.

## P1 — Correctness / architecture — ✅ ALL DONE 2026-07-02

- [x] **Unify GodotBridge singleton** — `get_bridge()` everywhere; `/api/v1/status` reports live `bridge_connected` (+ legacy `ws_connected` key).
- [x] **Stop blocking the event loop** — `asyncio.to_thread` in core_tools (28 call sites), ws_gateway, mobile_command, game_builder pipeline, REST tool handlers (itch/steam/fleet).
- [x] **Bridge concurrency safety** — `threading.Lock`, request_id correlation with stale-reply draining, `_recv_line` buffer retention.
- [x] **Dual mode: actually serve MCP over HTTP** — `mcp.http_app()` mounted at `/mcp`, lifespan wired; initialize handshake verified live.
- [x] **CI dev-deps** — ruff in `[dependency-groups].dev`; duplicate optional-dependencies removed.
- [x] **ci.yml** — stray `.bak` deleted; `*.bak` already gitignored. Tag-only trigger change left uncommitted for Sandra to commit/revert. Ubuntu lint-only PR job: still open (optional).
- [x] **Version single-sourcing** — 0.3.0 everywhere; runtime via `importlib.metadata`.
- [x] **CHANGELOG.md repair** — corrupted duplicate blocks removed, content merged.
- [x] **Honest tool counts** — server.py comment lists the 15 tools; STATUS says 15; `just tools` enumerates (93 total, incl. depot/prefab/prompt/workflow tools).
- [x] **Small bugs** — environment-dup fixed, `fastmcp<4`, `websockets` dropped (grep-confirmed unused), uploads/outputs env-configurable (`GODOT_MCP_UPLOADS_DIR`/`_OUTPUTS_DIR`), settings wired into bridge connect (env → settings.json → defaults; PUT drops connection), TCP naming in docstrings.

## P2 — Fleet standards (partially done)

- [ ] **Prefab UI cards** — add `prefab-ui` dep; Prefab surfaces for `godot_status`, `fleet_exchange_status`, `itch_status`, `steam_status`, `workflow_list`, `artifact_list` (mandatory list/status/stats per SOTA_REQUIREMENTS §2.2). (0.5-1 d)
- [x] **`GET /api/capabilities`** — backend endpoint done (godot/bridge/butler/steam/worldlabs/sampling/mcp_http/gateway/logs). Still open: web_sota consumes it for feature gating. (1-2 h)
- [ ] **Bun migration (BUN_STANDARDS)** — web_sota: `bun install`, commit `bun.lock`, delete `package-lock.json`; add `@biomejs/biome` + playwright scripts to package.json; justfile: `npm/npx` → `bun/bunx`. (2-3 h)
- [x] **STATUS.md refresh** — done 2026-07-01.
- [x] **Justfile dedup** — local `cua-nsis-test` removed.

## Extensions (post-fix, highest value first)

- [ ] **`godot_capture_viewport`** — new bridge action rendering the viewport to PNG (path or base64) + MCP tool + REST. Enables agent verify-loops on generated scenes, README screenshots, mobile previews. The single biggest capability gap for an AI game-dev server. (0.5-1 d)
- [ ] **GDScript validation loop** — after `generate_game_logic`, run `godot --headless --check-only` per script; on errors, one LLM repair round with the error text. (0.5 d)
- [ ] **`just gb-smoke`** — E2E smoke of design→logic via Ollama fallback (worlds skipped), asserting a parseable GamePlan and syntactically valid scripts. Closes STATUS "Live E2E" gap. (2 h)
- [ ] **`godot_scene` portmanteau** — expose existing bridge actions `add_node` / `remove_node` / `save_scene` / `modify_node` as one MCP tool with `operation` enum. (Bridge actions are already in the REST action map since 2026-07-02.) (2-3 h)
- [ ] **Input injection bridge action** — `simulate_input` (key/mouse via `Input.parse_input_event`) for agent playtesting. (0.5 d)
- [ ] **Portmanteau consolidation** — collapse itch (6), steam (7), fleet (6) tool groups into three portmanteaus; 93 → much smaller tool surface. Keep the 15 engine tools flat. (0.5-1 d)
- [ ] **Multi-node scene hierarchy from GamePlan** — nested node trees + script attachment instead of flat top-level nodes (existing roadmap item). (1 d)
- [ ] **Splat decision** — either adopt a Godot 4.x gaussian-splat GDExtension for in-engine SPZ/PLY, or formally document the Spark-viewer handoff as the design and close the R&D item. (research 0.5 d)
- [ ] **Residual sync-in-async** — itch/steam/fleet `tools.py` MCP tool wrappers still call sync service functions directly (FastMCP runs them on the loop); low traffic, but wrap in `to_thread` for consistency. (1 h)
- [ ] **Optional ubuntu lint-only PR job** in CI (tag-only Windows job stays). (30 min)
