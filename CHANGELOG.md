# Changelog

All notable changes to **godot-mcp** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
