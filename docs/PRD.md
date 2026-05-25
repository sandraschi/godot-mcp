# godot-mcp — Product Requirements Document

**Status:** Active (alpha) | **Version:** 0.2.1 | **Date:** 2026-05-22

---

## 1. Executive Summary

godot-mcp is a FastMCP 3.2+ server that controls a **live Godot 4 engine** over a local TCP bridge. It is the fleet visualization and game-export endpoint for CAD→CFD pipelines (qcad-mcp, freecad-mcp, FluidX3D) and for blender-mcp → GLB/OBJ import workflows.

**Two-process runtime (required):**

1. **Python MCP gateway** — port **10993** (REST + MCP SSE), webapp **10992**
2. **Godot bridge** — `main_bridge.tscn` + `mcp_bridge.gd` on TCP **9080**

The server starts even if the bridge is down; tools reconnect lazily.

---

## 2. Goals

| Goal | Success metric |
|------|----------------|
| Agent-driven scene control | `godot_status` returns FPS + bridge connected |
| Fleet geometry import | STL / GLB / OBJ via bridge actions |
| CFD visualization | CSV velocity fields + GPU particles |
| Web export | HTML5 via bridge or `godot --headless --export-release` fallback |
| itch.io shipping | Butler push via MCP, REST, `just ship`, dashboard `/ship` |
| Developer ergonomics | `just serve`, `just godot-bridge`, `just demo-run`, `just bridge-test`, `just ship` |
| Sample games | Cloned demos under `samples/` with import + 4.4 compatibility patches |

---

## 3. MCP tool surface (14 tools)

| Tool | Purpose |
|------|---------|
| `godot_status` | Engine + bridge health |
| `godot_import_stl` | Binary STL mesh |
| `godot_import_glb` | GLTF binary/text |
| `godot_import_obj` | Wavefront OBJ |
| `godot_load_velocity_field` | FluidX3D CSV |
| `godot_spawn_particles` | GPUParticles3D |
| `godot_animate_streamlines` | Particle motion |
| `godot_create_camera` | Camera3D |
| `godot_add_light` | Scene lighting |
| `godot_set_material` | PBR albedo/roughness |
| `godot_export_web` | HTML5 export |
| `godot_read_scene_tree` | Scene introspection |
| `godot_set_config` | Project settings |
| `godot_headless_verify` | Script smoke test |

Optional: `MCP_BRIDGE_URLS` proxies tools from other fleet MCP servers.

### itch.io / Butler (6 tools) — v0.2.1

No TCP bridge required. Module: `godot_mcp/itch/`.

| Tool | Purpose |
|------|---------|
| `itch_status` | Butler + API key + defaults |
| `godot_export_release` | Headless export (`web` / `windows`) |
| `itch_push_preview` | Butler diff before upload |
| `itch_push` | Upload to `user/game:channel` |
| `itch_latest_version` | Wharf API query |
| `ship_to_itch` | Export → preview → push |

Workflow `ship_web_itch`. REST: `/api/v1/itch/*`. See [ship-to-itch.md](ship-to-itch.md).

---

## 4. Non-goals (current release)

- Replacing the Godot editor for manual level design
- Hosting multiplayer game servers
- Bundling Godot export templates in the MCP wheel
- Auto-starting the bridge from `start.ps1` (documented two-step start)

---

## 5. Sample games (`samples/`)

| Alias | Project | Notes |
|-------|---------|-------|
| `heart` | Heart-Platformer-Godot-4 | Godot 4.0 — default demo |
| `platformer` | godot-demo-projects/2d/platformer | Patched `libraries = {}` for 4.4 |
| `dodge`, `pong`, … | godot-demo-projects/2d/* | Run `just demo-import` on first use |
| `procedural` | godot-4-procedural-generation | GDQuest PCG |
| `skelerealms` | skelerealms | 3D RPG framework |

Recipes: `just demo-list`, `just demo-run <alias>`, `just demo-import <alias>`.

---

## 6. Ports and env

| Port | Role |
|------|------|
| 10993 | FastAPI + FastMCP |
| 10992 | Vite dashboard |
| 9080 | GDScript TCP bridge |

| Env | Default |
|-----|---------|
| `GODOT_HOST` | `127.0.0.1` |
| `GODOT_PORT` | `9080` |
| `GODOT_PATH` | auto-detect `godot.exe` |
| `BUTLER_API_KEY` | itch.io API key (push only) |
| `ITCH_TARGET` | Default `user/game` slug |
| `BUTLER_PATH` | Optional path to `butler.exe` |
| `ITCH_CHANNEL_WEB` | Default `html` |
| `ITCH_CHANNEL_WIN` | Default `win` |
| `GODOT_EXPORT_GAME` | Default sample `dodge` |

---

## 7. Roadmap

- [ ] `start.ps1` optional `--with-bridge` (spawn headless bridge)
- [ ] Integration tests against live Godot in CI (skipped today)
- [x] itch.io Butler ship tools + `/ship` dashboard (v0.2.1)
- [ ] Mock Butler integration test in CI
- [ ] Godot 4.6 install path as fleet default for unpatched official demos
- [ ] MCP tools for `godot_create_scene` / node CRUD (MCPB bundles reference these)

---

## 8. References

- Repo: `D:\Dev\repos\godot-mcp`
- Central fleet page: `mcp-central-docs/projects/godot-mcp/README.md`
- Architecture: [architecture.md](architecture.md)
- CLI: [cli.md](cli.md)
- Ship: [ship-to-itch.md](ship-to-itch.md)
