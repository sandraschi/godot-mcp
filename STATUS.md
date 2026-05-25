# Status — godot-mcp

**Status**: v0.3.0 — 14 Godot bridge tools + 6 itch ship tools + 6 fleet pipeline tools + **6 game_builder tools**; TCP bridge verified; World Labs GLB import wired; AI game-from-prompt pipeline.

**Repo**: `D:\Dev\repos\godot-mcp`  
**Ports**: Backend 10993, Frontend 10992, Bridge 9080, World Labs 10864/10865  
**Updated**: 2026-05-25

## Runtime (two processes)

| Process | Command | Port |
|---------|---------|------|
| MCP gateway | `just serve` or `start.ps1` | 10993 / 10992 |
| Godot bridge | `just godot-bridge` | 9080 |

Verify: `just bridge-test` → `Bridge OK - Godot 4.4.x @ … FPS`

Startup log warning `Connection refused at 127.0.0.1:9080` is expected until the bridge runs.

## Architecture

Godot 4 engine → TCP bridge (`mcp_bridge.gd` in `main_bridge.tscn`) → Python MCP → REST/SSE + webapp.

See `docs/architecture.md`, `docs/PRD.md`, `docs/ship-to-itch.md`.

## MCP tools

### Godot bridge (14)

| Tool | Status |
|------|--------|
| `godot_status` | Verified live |
| `godot_import_stl` | Implemented |
| `godot_import_glb` | Implemented |
| `godot_import_obj` | Implemented |
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
| `/ship` | Export, Butler preview/push, env status |
| `/workflows` | Includes `ship_web_itch` preset |
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

## Tauri native app (v0.2.1)

| Artifact | Path |
|----------|------|
| NSIS installer | `native/target/release/bundle/nsis/Godot MCP_0.2.1_x64-setup.exe` |
| MSI installer | `native/target/release/bundle/msi/Godot MCP_0.2.1_x64_en-US.msi` |
| Dev binary | `native/target/release/godot-mcp-native.exe` |

Build (requires Rust, Node 20+, uv, ~10 min first run):

```powershell
just tauri-build
```

Sidecar only: `just tauri-sidecar`. Dev shell: `just tauri-dev` (expects `web_sota` on 10992).

## Done recently (2026-05-25)

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

## Next steps

1. End-to-end game_builder test: prompt → worlds → Godot → HTML5
2. Optional: `/fleet` + `/game-builder` dashboard pages (REST already exists)
3. R&D: `godot_import_splat` bridge action (SPZ in-engine)
4. Game template project (`templates/game-template/`) for build_game target
