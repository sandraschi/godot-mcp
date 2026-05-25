# Fleet Pipeline Assessment — godot-mcp

**Date:** 2026-05-22  
**Version:** 0.2.1 (fleet module)  
**Scope:** Maker MCPs → `_exchange` → Godot import/export

---

## Executive summary

| Capability | Status | Notes |
|------------|--------|-------|
| Blender GLB → Godot | ✅ Works | Manual or `depot-import` / `fleet-import` |
| World Labs **collider GLB** → Godot | ✅ **Implemented** | `fleet_worldlabs_import_mesh`, `just fleet-worldlabs-import` |
| World Labs SPZ splat → Godot in-engine | ❌ Not supported | Stage to exchange + Spark viewer URL only |
| FreeCAD/QCAD STL → Godot | ✅ Works | `godot_import_stl` / `fleet_import_from_exchange` |
| Exchange depot listing | ✅ **Implemented** | `fleet_exchange_status`, `just fleet-status` |
| itch.io ship after import | ✅ Works | Unchanged — `just ship` |

**Recommendation for hobby 3D:** Use **Blender** for authored props; use **World Labs mesh** as collision/placeholder geometry while viewing splats in Spark (browser) or Unity (native splat).

---

## What was implemented (2026-05-22)

### Module: `src/godot_mcp/fleet/`

| File | Role |
|------|------|
| `exchange.py` | `FLEET_EXCHANGE_ROOT`, path validation, asset listing |
| `worldlabs.py` | HTTP client to worldlabs bridge (`10865`), asset URL extraction, download |
| `pipeline.py` | Stage mesh/splat, import via Godot TCP bridge |
| `service.py` | Service layer for REST/MCP |
| `tools.py` | Six MCP tools |
| `routes.py` | REST `/api/v1/fleet/*` |

### MCP tools (6)

| Tool | Mutating | Purpose |
|------|----------|---------|
| `fleet_exchange_status` | No | Exchange root, asset list, pipeline flags |
| `fleet_worldlabs_get_world` | No | Asset URLs + Spark viewer link |
| `fleet_import_from_exchange` | Yes | GLB/OBJ/STL → Godot bridge |
| `fleet_worldlabs_stage_mesh` | Yes | Download collider GLB only |
| `fleet_worldlabs_stage_splat` | Yes | Download SPZ to exchange (no Godot import) |
| `fleet_worldlabs_import_mesh` | Yes | Stage + `godot_import_glb` |

### Just recipes

| Recipe | Action |
|--------|--------|
| `just fleet-status` | GET `/api/v1/fleet/status` |
| `just fleet-import <path> [name]` | Exchange import |
| `just fleet-worldlabs-info <world_id>` | Asset URLs |
| `just fleet-worldlabs-stage-mesh <world_id>` | Download GLB |
| `just fleet-worldlabs-import <world_id> [name]` | Download + import |

### Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `FLEET_EXCHANGE_ROOT` | `D:/Dev/repos/_exchange` | Handoff bus |
| `WORLDLABS_BRIDGE_URL` | `http://127.0.0.1:10865` | Marble API |
| `WORLDLABS_WEB_URL` | `http://127.0.0.1:10864` | Spark viewer base |

---

## Gap analysis (honest)

### Gaussian splats in Godot

| Approach | Feasibility | godot-mcp status |
|----------|-------------|------------------|
| Import SPZ/RAD natively | R&D | Not started — no `godot_import_splat` bridge action |
| Spark viewer in SubViewport | Possible | Returns URL only; no embedded WebView tool |
| Unity splat + export | Works in fleet | Documented in worldlabs-mcp handoffs |
| GLB collision proxy + splat in browser | **Practical today** | ✅ Implemented mesh path |

### Missing (future)

1. **`godot_import_splat`** — needs GDScript renderer or external plugin in bridge project
2. **Auto-bridge launch** from `start.ps1` (still manual `just godot-bridge`)
3. **blender-mcp direct call** from godot-mcp (today: exchange file copy)
4. **CI smoke test** with mock worldlabs HTTP + mock bridge
5. **Web UI** `/fleet` page (REST exists; no dashboard yet)

---

## Test coverage

| Area | Tests |
|------|-------|
| Exchange path validation | `tests/test_fleet.py` |
| World Labs asset parsing | `tests/test_fleet.py` |
| Spark URL builder | `tests/test_fleet.py` |
| Live HTTP / bridge | Manual only |

---

## Quick workflow: World Labs world in Godot

```powershell
# Terminals: just serve, just godot-bridge, worldlabs-mcp running
just fleet-worldlabs-info YOUR_WORLD_ID
just fleet-worldlabs-import YOUR_WORLD_ID MyLevelMesh
# Open Spark for splat preview (URL in JSON response)
```

See also: [fleet-game-pipeline.md](fleet-game-pipeline.md), [maker/worldlabs-bridge-example.md](../maker/worldlabs-bridge-example.md).
