# Changelog

All notable changes to **godot-mcp** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-05-22

### Added
- **Sample games workflow**: `samples/` with official `godot-demo-projects`, Heart Platformer, procedural generation, skelerealms; `just demo-list`, `just demo-run`, `just demo-import` (auto `--import` on first run).
- **Bridge diagnostics**: `just bridge-test`, `just bridge-status`, `just godot-bridge` (headless bridge project).
- **Product docs**: `docs/PRD.md`; MCD fleet pages at `mcp-central-docs/projects/godot-mcp/`.

### Fixed
- **GDScript bridge**: Removed duplicate `_count_meshes` in `mcp_bridge.gd` (parse error blocked TCP listener on 9080).
- **Justfile 1.50**: Quoted recipe defaults (`mode="dual"`, `count="10"`), PowerShell-safe `doctor`/`freeze`, `depot-import`/`tool` args.
- **Platformer on Godot 4.4**: Patched `libraries/ = SubResource(...)` → `libraries = { "": SubResource(...) }` in six `.tscn` files (fixes missing `idle`/`walk` animations).

### Changed
- `samples/README.md` — demo catalog, import notes, 4.4 vs 4.6 guidance.
- `docs/install.md`, `docs/cli.md`, `STATUS.md` — two-process startup, bridge troubleshooting.

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
- Godot 4.0 WebSocket bridge (port 9080) with 15 GDScript action handlers.
- Artifact depot (`~/.godot-mcp/depot/`), MCPB bundles, prefab catalog, workflow engine, prompt templates.
- MCP bridge federation (`MCP_BRIDGE_URLS`) for cross-server tool calling.
- Tauri 2.0 native wrapper scaffold.
