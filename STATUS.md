# Status — godot-mcp

**Status**: v0.2.1 — 14 MCP tools; TCP bridge verified end-to-end; sample demos runnable.

**Repo**: `D:\Dev\repos\godot-mcp`  
**Ports**: Backend 10993, Frontend 10992, Bridge 9080  
**Updated**: 2026-05-22

## Runtime (two processes)

| Process | Command | Port |
|---------|---------|------|
| MCP gateway | `just serve` or `start.ps1` | 10993 / 10992 |
| Godot bridge | `just godot-bridge` | 9080 |

Verify: `just bridge-test` → `Bridge OK - Godot 4.4.x @ … FPS`

Startup log warning `Connection refused at 127.0.0.1:9080` is expected until the bridge runs.

## Architecture

Godot 4 engine → TCP bridge (`mcp_bridge.gd` in `main_bridge.tscn`) → Python MCP → REST/SSE + webapp.

See `docs/architecture.md`, `docs/PRD.md`.

## MCP tools (14)

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

## Sample games

| Recipe | Demo |
|--------|------|
| `just demo-run` | Heart Platformer (4.0) |
| `just demo-run platformer` | Official 2D platformer (4.4-patched) |
| `just demo-run pong` | Pong |
| `just demo-list` | All aliases |

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

## Done recently (2026-05-22)

- Bridge parse fix; port 9080 listens
- Justfile parses under just 1.50
- Platformer patch script `scripts/patch-platformer-godot44.ps1`
- Tauri 2.0 + PyInstaller sidecar (~27 MB backend bundled)
- MCD project page + PRD

## Next steps

1. Optional: auto-launch bridge from `start.ps1`
2. CI job with headless Godot + bridge smoke test
3. qcad/freecad → import integration test on `_exchange` depot
