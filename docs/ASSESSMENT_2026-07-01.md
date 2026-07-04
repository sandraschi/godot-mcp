# godot-mcp — Assessment 2026-07-01

Scope: full repo review of `D:\Dev\repos\godot-mcp` (v0.2.x/0.3.0, FastMCP 3.4.2, 56 MCP tools, TCP bridge, web_sota dashboard, Tauri native, MCPB bundle, mobile WS gateway). Findings below are code-verified; items marked **[verified live]** were confirmed by running commands on Goliath during the review.

**Verdict:** Ambitious, well-documented, architecturally coherent repo with a genuinely novel pipeline (prompt → GamePlan → Marble worlds → Godot scene → GDScript → itch/Steam). But right now the **justfile does not parse at all**, the **MCPB bundle cannot start**, the **flagship game-builder pipeline cannot work via REST/dashboard** (sampling is structurally unavailable there), and a **background task crashes at every server start**. The gap between STATUS.md's "Implemented" claims and what actually runs is wider than fleet honesty standards allow. Roughly 2-3 AI-assisted days close all P0/P1 items.

---

## 1. P0 — Broken right now

### 1.1 justfile fails to parse — every recipe is dead **[verified live]**

`just --list` errors: `Recipe line has extra leading whitespace — justfile:427`. The `pack-mcpb` recipe uses a multi-line PowerShell array without just line continuations:

```
pack-mcpb:
    Set-Location '...'
    $files = @(
        'manifest.json', 'pyproject.toml', ...   <- just sees this as bad indentation
```

Every recipe (`serve`, `test`, `bridge-test`, `demo-run`, `tauri-build`, …) is unusable until this is fixed. STATUS.md's "Justfile parses under just 1.50" is stale.

Second parse blocker behind it: recipes `e2e-install` / `e2e` (lines 528/533) reference `{{REPO}}`, which is defined nowhere (fleet.just defines `REPO_DIR`). Fix both: rewrite `pack-mcpb` with `\` continuations or a single line (or better, delete it — see 1.3), and replace `{{REPO}}` with `{{justfile_directory()}}`.

### 1.2 ws_gateway `_push_log_entries` crashes at startup **[verified live]**

`ws_gateway.py:452` does `from godot_mcp.server import LOG_RING`. `LOG_RING` does not exist anywhere in the codebase (grep confirms the only 5 references are inside ws_gateway itself) — it was replaced by `services/activity_log.py` and this task was never migrated. `start_background_tasks()` creates the task in lifespan, it raises `ImportError` on first tick, and the mobile `logs` channel is silently dead. Rewrite against `activity_log.query_logs(after_id=...)` (the SSE endpoint already shows the correct pattern).

### 1.3 MCPB bundle is non-functional (three independent ways)

1. **Stale drifted server copy.** `mcpb/src/server.py` is an old full copy of the main server that `import`s the entire `godot_mcp` package (`godot_mcp.artifacts.routes`, `fastapi`, `uvicorn`, …). The bundle ships only `src/__init__.py` + `src/server.py` — every import fails. It has also drifted (missing game_builder REST wiring, older CORS block, indentation damage).
2. **Wrong archive format.** `pack-mcpb` builds a `.mcpb` with `tar -czf`. MCPB bundles are ZIP archives produced by the Anthropic mcpb CLI (`bunx @anthropic-ai/mcpb pack`). Claude Desktop will reject the tarball. Note `fleet.just` already provides the correct `mcpb-pack` recipe via `scripts/mcpb-pack.ps1` — the local `pack-mcpb` is a broken duplicate.
3. **Invalid manifest.** `mcpb/manifest.json` uses `${PWD}` (not an MCPB manifest variable — use `${__dirname}`) and requires `uv` on the end user's machine, violating the portability intent of MCPB.

Recommendation: delete `mcpb/src/server.py` entirely, make the bundle a thin `run_server.py` that imports the real installed package (or vendor the package via mcpb-pack.ps1 staging), and pack exclusively via `just mcpb-pack`. Also: `mcpb/src/*.pyc` files are lying around (untracked, but clutter).

### 1.4 Game Builder is structurally dead over REST and the dashboard

Every REST/service entry point passes `ctx=None`:

- `service_design_game` → `pipeline.design_game(game_concept, ctx=None)`
- `service_generate_logic` → `generate_game_logic(plan, ctx=None)`
- `service_build_game` → `build_game(..., ctx=None)`
- `_handle_generation_intent` (mobile) → `sample_text(None, ...)`

`sampling/service.sample_text` with `ctx=None` returns the literal string `"[Sampling unavailable]"`, which `GamePlan.from_json` then fails to parse. So `/game-builder`, `/api/v1/game-builder/*`, `POST /api/v1/control/tool {tool: build_game}`, and the Pocket Architect environment intent can **never** succeed — not "E2E untested" (STATUS.md) but impossible by construction. Only an MCP client that supports sampling can drive it.

Two additional bugs inside `sample_text` even when a sampling client exists:

- It reads `result.content`; FastMCP sampling returns content blocks exposing `.text`, so the code falls through to `str(result)` and returns a repr.
- It stuffs a `{"role": "system"}` message into `messages`; FastMCP's `ctx.sample` expects a `system_prompt` parameter — system-in-messages is liable to be rejected by the client.

**This is the highest-value fix in the repo:** give `sample_text` a fallback provider chain (env-configured): `ctx.sample()` → direct API (DeepSeek/OpenRouter/Anthropic key) → local Ollama (`qwen3.5:27b` on Goliath). ~1 day, and it turns the flagship feature from demo-ware into something that actually runs from the dashboard.

### 1.5 `modify-node` bridge action does not exist **[verified live]**

`ws_gateway._handle_intervention_intent` (State Surveiller `set_param`) sends action `"modify-node"`. The GDScript bridge's action switch (grep of `mcp_bridge.gd`) has 18 snake_case actions — `status, import_stl, import_glb, import_obj, load_velocity_field, spawn_particles, animate_streamlines, create_camera, add_light, set_material, export_web, read_scene_tree, set_config, headless_verify, add_node, remove_node, save_scene, play_animation` — and no `modify-node`/`modify_node` at all. The intent always fails. Either implement `modify_node` in the bridge or remove the intent path (Implementation Honesty standard: no fake-success surface).

---

## 2. P1 — Correctness and architecture

### 2.1 Two divergent GodotBridge instances

`server.py` creates its own `_bridge = GodotBridge()` while `services/godot_bridge.py` holds a module singleton used by core_tools, fleet pipeline, game_builder, and ws_gateway. Result: two TCP connections to the GDScript bridge, divergent connection state, and `/api/v1/status.godot.ws_connected` reflects only the server.py instance (set once at startup and never updated). Fix: `server.py` should use `get_bridge()`; report `get_bridge().connected` live in `/api/v1/status`.

### 2.2 Blocking I/O on the asyncio event loop

`GodotBridge.connect/send` are blocking socket calls (default 10s timeout, 300s for exports) invoked directly from `async def` endpoints and tools. Likewise itch Butler subprocess runs, Steam staging, and worldlabs GLB downloads are sync calls inside async paths. One slow export freezes the entire server: SSE log stream, mobile WS, all REST. Fix: wrap bridge/subprocess/download calls in `asyncio.to_thread(...)` (cheap), or move the bridge to an asyncio streams client (cleaner, more work).

### 2.3 GodotBridge has no concurrency protection

`send()` writes a request and reads "the next line" with no lock and no `request_id` correlation on the read side. The ws_gateway status pusher calls `bridge.send("status")` every 2s on the shared singleton; a concurrent tool call can consume the status reply (or vice versa) and return mismatched data. Also `_recv_json` discards any buffered bytes after the first newline, so pipelined messages are lost. Fix: a `threading.Lock` around send+recv, keep leftover buffer between reads, and verify `response["request_id"]` matches, draining mismatches.

### 2.4 "dual"/"http" mode does not actually serve MCP over HTTP

`main()` runs `uvicorn.run(app)` — the plain FastAPI app. `FastMCP.from_fastapi(app)` derives MCP tools *from* the app, but the MCP HTTP/SSE transport is never mounted into it. `just info`'s advertised `http://localhost:10993/sse` is a 404; "dual" mode is REST-only. Fix: mount the FastMCP HTTP app (`mcp.http_app()` mounted into the FastAPI app, sharing the lifespan) or stop advertising dual/SSE.

### 2.5 CI is broken and half-committed **[verified live]**

- `uv sync --group dev` installs `[dependency-groups].dev` = pytest + pytest-asyncio only. **Ruff is not installed** (it lives in the legacy `[project.optional-dependencies].dev`), so the lint and format steps fail on the runner. Consolidate dev deps into `[dependency-groups].dev` (add ruff) and delete the optional-extra duplicate, or sync `--all-extras`.
- `ci.yml` has an **uncommitted** working-tree change switching triggers from push/PR to tags-only, plus a stray `ci.yml.20260701_030123.bak` sidecar inside `.github/workflows/`. If tag-only is the intent, commit it; consider keeping a cheap ubuntu lint-only job on PRs. Delete the .bak and add `*.bak` to `.gitignore` (fileops generates these on every edit).

### 2.6 Version chaos

Five different versions coexist: `0.1.0` (justfile `VER`, plugin.cfg, web_sota package.json, mobile gateway hello message), `0.2.0` (pyproject, mcpb manifest), `0.2.1` (Tauri artifacts), `0.3.0` (STATUS.md, hardcoded in `/api/v1/status` and lifespan log). Single-source it: `importlib.metadata.version("godot-mcp")` at runtime, one bump touchpoint, and fix justfile `VER` since it names the `.mcpb` output.

### 2.7 CHANGELOG.md head is corrupted

Two duplicate `[Unreleased] — 2026-06-14` blocks sit *above* the file header, containing mangled escape sequences: a literal BEL character (`\a` from "allow_origins" written through PowerShell) and a literal tab (`\t` from "tauri://localhost"). Merge both blocks into the real `[Unreleased]` section and retype the damaged lines.

### 2.8 Tool-count fiction

- `server.py` comment block: "12 tools registered via core_tools" — it registers **15** (GLB, OBJ, play_animation were added later).
- STATUS.md: "14 Godot bridge tools" — it's 15.
- `just tools` prints a hardcoded string "37+ tools" without counting anything. Make it actually enumerate registered tools or delete it. Hardcoded fake output is exactly what IMPLEMENTATION_HONESTY_STANDARD bans.

### 2.9 Misc code bugs

- `ws_gateway._handle_generation_intent`: `if mode in ("environment", "environment")` — duplicate literal; second value presumably meant `"world"` or `"scene"`.
- `fastmcp>=3.4.2` has no upper bound; fleet standard is `>=3.x,<4`. Same in mcpb/pyproject.
- `websockets>=12.0` dependency appears unused (bridge is raw TCP; FastAPI WS uses Starlette). Verify and drop.
- `_FILES_DIR`/`_OUTPUTS_DIR` are computed relative to the package (`__file__/../../../uploads`) — correct in a src-layout dev checkout, wrong under the PyInstaller sidecar/site-packages. Make them env-configurable with a default like `~/.godot-mcp/uploads`.
- `PUT /api/v1/settings` persists `godot_path/host/port` to `~/.godot-mcp/settings.json`, but nothing ever reads that file — `GODOT_HOST/PORT/PATH` come from env at import time. Settings are write-only theater. Wire `_load_settings()` into bridge config (with reconnect), or label the page "not implemented".
- Docstrings and module headers throughout say "WebSocket bridge"; it is a newline-delimited-JSON **TCP** bridge (STATUS.md gets it right). Rename to stop confusing every future agent that reads the code.

---

## 3. P2 — Fleet standards compliance gaps

| Standard | Status in godot-mcp |
|---|---|
| Prefab UI (mandatory for list/status/stats tools) | **Absent.** No `prefab-ui` dependency, no ToolResult cards. `godot_status`, `fleet_exchange_status`, `itch_status`, `steam_status`, `workflow_list`, `artifact_list` are prime candidates. |
| `/api/capabilities` introspection (WEBAPP_STANDARDS §1.4, mandatory) | **Absent.** Webapp hardcodes feature availability. |
| Bun (BUN_STANDARDS) | **Not migrated.** web_sota has `package-lock.json`; justfile calls `npm`/`npx` throughout. `biome` is invoked but not in devDependencies (npx prompts to download). No `bun.lock`. |
| Portmanteau tool design | 56 flat tools. The 15 engine-control tools are defensible as-is (agent ergonomics), but itch (6), steam (7), fleet (6) would each collapse into one portmanteau with an `operation` enum, cutting the surface from 56 to ~25. |
| MCPB via mcpb CLI | Violated (see 1.3). |
| Justfile standards | Parse-broken (1.1); duplicate `cua-nsis-test` recipe (local + fleet.just — works via override, but redundant). |
| llms.txt / llms-full.txt pair | Present. Good. |
| glama.json | Present. Good. |
| Logs page standard | Implemented properly (`activity_log` + `/api/logs` + `/logs`). Good. |
| Naked-PC install (`start.ps1` Require-Command etc.) | Not audited in depth this pass — verify when touching start scripts. |

---

## 4. Gaps (known/acknowledged plus newly identified)

1. **Splat rendering in Godot** — acknowledged in STATUS. SPZ/PLY staging works; in-engine rendering doesn't. Options: GDExtension gaussian-splat renderer (community addons exist for Godot 4.x), or keep the Spark viewer handoff and document it as the design decision (arguably correct — don't chase parity with Spark).
2. **Bridge actions not exposed:** `add_node`, `remove_node`, `save_scene` exist in mcp_bridge.gd (game_builder uses `add_node` internally) but have no MCP tool and no REST action_map entry. Expose as a `godot_scene` portmanteau (operation: add_node|remove_node|save_scene|modify_node).
3. **No visual feedback loop.** No `capture_viewport` bridge action exists. For an *AI* game-dev server this is the single biggest missing capability: the agent generates a scene and can never see it. `godot_capture_viewport` (PNG to disk/base64) enables verify-loops, README screenshots, and mobile previews. Pairs with the fleet Verification Standards.
4. **No input injection** (`Input.parse_input_event` via bridge) — needed for agent playtesting of generated games.
5. **Generated GDScript is never validated.** `generate_game_logic` writes whatever the LLM produced. Add a `godot --headless --check-only` pass per generated file and feed errors back for one repair round. Cheap, closes the biggest quality hole in `build_game`.
6. **GamePlan → multi-node hierarchy** — on the existing roadmap; `compose_game_scene` only creates flat top-level nodes.
7. **Live E2E of build_game** — blocked on 1.4; once the sampling fallback exists, add a `just gb-smoke` recipe running design→logic against Ollama with worlds skipped.

---

## 5. What is genuinely good

- Module layout is clean and consistent (routes/service/tools per domain); the service layer separates MCP tools from REST properly.
- `activity_log.py` is a solid, thread-safe, correctly ring-buffered implementation of the fleet logs standard.
- itch/Steam shipping paths have sensible safety defaults (dry_run true, push-preview before push, env-driven secrets with hints, `_record_ship` audit).
- Docs are unusually extensive (30+ files incl. PRD, architecture, mobile protocol reference, ship guides) and mostly accurate below the STATUS headline.
- 52 tests, pytest-asyncio configured, Playwright smoke scaffold present.
- Sample-game catalog with 4.4 patching scripts is a real asset for demos.
- Steam integration deliberately proxies steam-mcp rather than reimplementing SteamPipe — correct fleet pattern.

---

## 6. Suggested execution order

Day 1 (unblock): fix justfile parse + `{{REPO}}`; fix LOG_RING task; fix `modify-node`; unify bridge singleton; commit or revert ci.yml + fix CI dev-deps; CHANGELOG cleanup; version single-sourcing.

Day 2 (flagship): sampling fallback chain (ctx → API → Ollama) plus `sample_text` content/system fixes; `asyncio.to_thread` wrapping + bridge send lock; GDScript `--check-only` validation pass; gb-smoke recipe.

Day 3 (packaging + standards): rebuild MCPB via mcpb-pack.ps1 (delete stale mcpb/src/server.py); mount MCP HTTP transport or drop "dual" claims; Bun migration for web_sota; `/api/capabilities`; first Prefab cards (status tools).

Later: capture_viewport + input injection bridge actions; godot_scene portmanteau; splat R&D decision; portmanteau consolidation of itch/steam/fleet; STATUS.md refresh with honest tool counts.

See `TODO.md` at repo root for the tracked checklist.
