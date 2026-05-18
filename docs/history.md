# Godot MCP — History

---

## Part 1: Godot Engine History

### 2001-2014: The Closed-Source Era (Larvotor)

Godot's origin story begins in 2001 when Argentine programmers **Juan Linietsky** and **Ariel Manzur** started developing a proprietary game engine they called **Larvotor**. The engine was used in-house for their game development projects and wasn't publicly available.

Key milestones:
- **2001**: First lines of code written by Linietsky
- **2007**: Engine capable of shipping commercial games on PC and mobile
- **2013**: Internal rewrite begins — the engine is restructured with a modular architecture, node/scene system, and GDScript
- **Early 2014**: Decision made to open-source the engine under the MIT license

### February 2014: Godot 1.0 — Open-Source Release

On February 4, 2014, the engine was publicly released on GitHub under the MIT license as **Godot** (the name inspired by Samuel Beckett's *Waiting for Godot* — representing the endless wait for a truly open-source game engine).

- **1.0** (Dec 2014): First proper release. 2D engine, basic 3D, GDScript (new scripting language designed for the engine)
- **License**: MIT — fully permissive. Developers owe nothing, not even credit.

### 2015-2017: Godot 2.x — Growing Pains

**2.0** (Feb 2016): Major UI system, Web export via Emscripten, 2D skeletal animation, improved editor.

**2.1** (Jul 2016): Asset Library, plugin system, PBR materials. Community growing steadily.

During this period, the core team worked with occasional contract funding. Both founders held other jobs.

### January 2018: Godot 3.0 — The 3D Leap

**3.0** was the first version with a competitive 3D renderer (based on OpenGL ES 3.0). Key additions:
- Physically Based Rendering (PBR)
- Bullet physics engine integration
- New audio engine (Redux)
- Static typing for GDScript (3.1)
- Visual scripting for non-programmers

**3.1** (Mar 2019): GDScript static typing, OpenGL ES 2.0 fallback, VR/AR support.

**3.2** (Jan 2020): WebXR, RTX support, improved Web export. Godot Foundation established as a non-profit.

### September 2023: The Unity Exodus — Godot's Tipping Point

On September 12, 2023, Unity Technologies announced the **Runtime Fee** — a per-install charge that would apply retroactively to all existing Unity games. The backlash was immediate and massive:

- Thousands of developers publicly announced migration to Godot
- **€1 million+** in donations to the Godot Foundation in three weeks
- GitHub stars jumped from ~50,000 to ~75,000 in a month
- Discord membership doubled
- Major studios announced Godot adoption

This event permanently changed Godot's trajectory. What was previously a "hobbyist engine" became the leading open-source alternative to Unity.

### March 2023: Godot 4.0 — Vulkan Era

**4.0** was the most significant technical rewrite since 1.0:
- Brand new **Vulkan renderer** replacing OpenGL
- **SDFGI**: Signed Distance Field Global Illumination (real-time GI)
- **Volumetric fog**, FSR upscaling
- **New 3D physics** (GodotPhysics, later replaced by Jolt)
- **GDScript 2.0**: Full static typing, lambda functions, new syntax
- **C#**: .NET 6 support via CoreCLR (replacing Mono)
- **Forward+ renderer** for desktop, **Mobile** renderer for phones

The transition from 3.x to 4.0 was bumpy:
- Many 3.x projects required significant porting work
- The C# migration from Mono to .NET broke compatibility
- GodotPhysics in 4.0 was less capable than Bullet in 3.x

### 2024: The Year of Consolidation

**4.1** (Jul 2023): FSR 2.2, better particles, editor UX polish.

**4.2** (Nov 2023): AMD FSR 2.2, lightmapper improvements, **Jolt Physics integration** (optional).

**4.3** (Aug 2024): Skeletal animation retargeting, Wayland support, improved C# integration. Stability significantly improved.

### 2025: Jolt and D3D12

**4.4** (Mar 2025): Jolt Physics as opt-in, improved rendering, Meta Quest 3 native support.

**4.5** (Sep 2025): Jolt Physics improvements, Direct3D 12 backend on Windows, Metal improvements on macOS. Rendering performance improved ~30% over 4.0.

### 2026: Jolt Becomes Default

**4.6** (Jan 2026): **Jolt Physics is now the default** physics engine, replacing GodotPhysics entirely. **Direct3D 12 is the default on Windows** (faster than Vulkan on most Windows GPUs). .NET 8 support.

**4.6.2** (Apr 2026): Current stable release. Bugfixes, improved C# hot reload.

**4.7** (Beta, in development): HDR display support, BVH ray tracing groundwork, multi-window editor, audio mixing improvements.

### Timeline Summary

| Year | Version | Key Event |
|------|---------|-----------|
| 2001 | — | Linietsky starts Larvotor engine |
| 2014 | 1.0 | Godot open-sourced under MIT |
| 2016 | 2.0 | Web export, 2D skeletal animation |
| 2018 | 3.0 | PBR renderer, Bullet physics |
| 2020 | 3.2 | WebXR, Godot Foundation |
| 2023 | 4.0 | Vulkan renderer, SDFGI |
| 2023 | — | Unity Runtime Fee → Godot exodus |
| 2025 | 4.4 | Jolt Physics (opt-in) |
| 2026 | 4.6 | Jolt as default, D3D12 as default |

---

## Part 2: godot-mcp History

### v0.1.0 — Origin

**Initial release**. Built from the fleet standard template (FastMCP 3.2 + FastAPI + React Vite webapp).

**Core design decisions**:
- **TCP bridge pattern**: Python ↔ Godot GDScript over JSON/NDJSON. Chosen over direct GDScript editor plugins because it allows the MCP server to run independently of the Godot editor, enabling headless CI/CD and multi-client access.
- **15 TCP actions**: Mirroring Godot's scene manipulation capabilities — import, spawn, animate, configure, export.
- **12 MCP tools**: Exposing the 15 bridge actions through FastMCP tool decorators for MCP clients.
- **Dual transport**: Both SSE (for cloud/network MCP clients) and stdio (for local process-based clients).

**Initial tool set**:
- Status, import STL, load velocity, spawn particles, animate streamlines, create camera, add light, set material, export web, read scene tree, set config, headless verify

### Fleet Integration

godot-mcp was designed as the **visualization terminal** in a multi-repo pipeline:

```
qcad-mcp → STL geometry
    ↓
freecad-mcp → BIM validation
    ↓
FluidX3D → CSV velocity field
    ↓
godot-mcp → Scene import, render, animate, export
    ↓
resonite-mcp → XR world deployment
```

Each repos exposes MCP tools that godot-mcp can consume via `MCP_BRIDGE_URLS`, enabling end-to-end AI-orchestrated pipelines.

### Cross-Repo Tool Bridge

With the `MCP_BRIDGE_URLS` environment variable, godot-mcp can proxy MCP tools from:
- `qcad-mcp` (port 10966): CAD geometry creation (`plan_extrude`)
- `freecad-mcp` (port 10944): BIM model conversion (`import_stl`, `convert_format`)

This allows a single AI agent to:
1. Generate geometry in qcad-mcp
2. Validate in freecad-mcp
3. Simulate CFD (external GPU computation)
4. Import and visualize in godot-mcp
5. Export to web or XR

All through one MCP server.

### Current Status

- **Stable**: Core tools working, TCP bridge reliable
- **In Development**: Multi-agent coordination, real-time collaborative editing, procedural generation helpers
- **Tested**: Windows (primary), Linux (CI), macOS (partial)

### Roadmap

| Quarter | Focus |
|---------|-------|
| 2026 Q2 | Scripted animation tools, material presets, river/terrain generators |
| 2026 Q3 | Multi-agent scene composition, GDScript generation from natural language |
| 2026 Q4 | Real-time collaborative editing, WebRTC scene streaming |
| 2027 Q1 | AI-assisted shader generation, automated testing framework |
