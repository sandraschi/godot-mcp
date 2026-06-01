# Fleet Pipeline Assessment — godot-mcp

**Date:** 2026-05-25 (gaps filled)  
**Package:** `pyproject.toml` 0.2.0 · **API status:** 0.3.0 · **Roadmap label:** v0.3.0  
**Scope:** Maker MCPs → `_exchange` → Godot → export/ship → AI game-from-prompt

---

## Executive summary

| Layer | Status | Notes |
|-------|--------|-------|
| **Fleet exchange** | ✅ Shipped | 6 tools, REST, Just recipes, 9 unit tests |
| **World Labs GLB → Godot** | ✅ Shipped | `fleet_worldlabs_import_mesh` |
| **World Labs SPZ → Godot** | ❌ Not in-engine | Stage + Spark URL only |
| **Game Builder (prompt → game)** | ✅ Wired | REST, UI, scenes, script sync |
| **`build_game` live E2E** | 🟡 Manual | Needs worldlabs + bridge + LLM |
| **Logs `/logs`** | ✅ Fleet standard | `/api/logs` + tail/export/clear |

**Bottom line:** Fleet handoffs and game_builder orchestration are wired. Remaining gaps: SPZ in Godot, live E2E CI, scene script attachment polish for multi-node hierarchies.

---

## Tool inventory (49 MCP tools)

| Module | Count | REST via `/api/v1/control/tool` |
|--------|------:|----------------------------------|
| Godot bridge (`core_tools`) | 15 | ✅ bridge actions |
| itch / Butler | 6 | ✅ |
| **fleet** | 6 | ✅ |
| **game_builder** | 6 | ✅ REST + `/api/v1/control/tool` |
| artifacts, workflows, bridge, sampling, prefabs, prompts, mcpb | 10 | partial |

**Tests:** 49 passing (fleet, game_builder, activity log API).

---

## Fleet module — unchanged, still solid

Implemented 2026-05-22 in `src/godot_mcp/fleet/`.

| Tool | Purpose |
|------|---------|
| `fleet_exchange_status` | List `_exchange` assets + readiness flags |
| `fleet_import_from_exchange` | GLB/OBJ/STL → Godot bridge |
| `fleet_worldlabs_get_world` | Asset URLs + Spark viewer link |
| `fleet_worldlabs_stage_mesh` | Collider GLB → `_exchange/models/worldlabs/` |
| `fleet_worldlabs_stage_splat` | SPZ to exchange (no Godot render) |
| `fleet_worldlabs_import_mesh` | Stage + `godot_import_glb` |

**Just:** `fleet-status`, `fleet-import`, `fleet-worldlabs-info`, `fleet-worldlabs-stage-mesh`, `fleet-worldlabs-import`

**Env:** `FLEET_EXCHANGE_ROOT`, `WORLDLABS_BRIDGE_URL`, `WORLDLABS_WEB_URL`

### Splat gap (still open)

| Approach | godot-mcp |
|----------|-----------|
| `godot_import_splat` bridge action | ❌ Not started |
| Spark viewer URL in tool responses | ✅ |
| GLB collision proxy in Godot | ✅ |
| Unity / Blender splat handoffs | Documented in worldlabs-mcp; not automated |

---

## Game Builder — new since last assessment

**Module:** `src/godot_mcp/game_builder/` (plan, prompts, pipeline, tools)  
**Spec:** `docs/SPEC_GAME_BUILDER.md`  
**Registered:** via `tools/__init__.py` · also wired in mobile/ws_gateway command paths

| Tool | Intended step | Implementation |
|------|---------------|----------------|
| `design_game` | LLM → GamePlan JSON | ✅ `sample_text` + Pydantic parse |
| `generate_game_worlds` | worldlabs `generate_world_from_text` + poll | ✅ MCP bridge to 10865 |
| `compose_game_scene` | Import GLBs, lights, camera, nodes | 🟡 Partial — see gaps |
| `generate_game_logic` | LLM writes GDScript | ✅ returns code dict (not written to disk yet) |
| `export_and_ship` | HTML5 + optional itch | ✅ reuses itch service |
| `build_game` | Full pipeline | 🟡 Calls all steps; blocked by compose/staging gaps |

### Phase status vs spec

| Spec phase | Status |
|------------|--------|
| Phase 1 — core module + MCP tools | ✅ Done |
| Phase 2 — REST + `/game-builder` UI + SSE | ❌ Not started |
| Phase 3 — `templates/game-template/` + genre templates | ❌ Not started |

---

## Integration gaps (updated 2026-05-25)

### Fixed

1. **`generate_game_worlds` → fleet** — calls `stage_worldlabs_mesh(marble_world_id)` after each completed operation
2. **Plan slug → Marble id** — `compose_game_scene(plan, world_results)` uses `marble_world_id` + `mesh_path`
3. **Script persistence** — `write_scripts_to_project` + `templates/game-template/`
4. **Project assets** — staged GLBs copied to `assets/worldlabs/` before export
5. **Bridge `add_node`** — Node2D, Control, CanvasLayer, CharacterBody2D

### Remaining

1. **REST / dashboard** — ✅ game_builder REST + `/game-builder` page; fleet page still optional
2. **R&D:** `godot_import_splat` bridge action
3. **Live E2E CI** for `build_game`
4. **Multi-node scene trees** — flat `.tscn` per plan node today

---

## What works end-to-end today

| Workflow | Ready? |
|----------|--------|
| Blender GLB → `_exchange` → `fleet-import` → Godot | ✅ |
| World Labs world id → `just fleet-worldlabs-import` → Godot | ✅ (manual) |
| Sample game → `just ship web vibecode` | ✅ |
| `design_game` alone (with sampling client) | ✅ likely |
| End-to-end `build_game` → shipped HTML5 | 🟡 Wired; needs live worldlabs + bridge + LLM |

---

## Recommended next work (priority order)

1. **Live E2E:** `build_game` with worldlabs + godot-bridge + sampling client
2. **Scene wiring:** attach generated scripts to `.tscn` nodes automatically
3. **REST:** add game_builder to `PYTHON_TOOLS` or dedicated routes
4. **R&D:** `godot_import_splat` (desktop-first)
5. **UI:** `/game-builder` page with step progress

---

## Quick reference

```powershell
# Fleet (works today)
just serve
just godot-bridge
just fleet-worldlabs-import YOUR_MARBLE_WORLD_ID LevelMesh

# Game builder (MCP + sampling — fleet wired)
# build_game(concept) → worlds staged → compose imports → scripts written → export
# compose_game_scene(plan_json, worlds_result_json=...)  # pass generate_game_worlds output
```

See also: [fleet-game-pipeline.md](fleet-game-pipeline.md), [SPEC_GAME_BUILDER.md](SPEC_GAME_BUILDER.md), [maker/worldlabs-bridge-example.md](../maker/worldlabs-bridge-example.md).
