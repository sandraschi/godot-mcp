# godot-mcp — Product Requirements Document

**Status:** Active (alpha) | **Version:** 0.3.0 | **Date:** 2026-07-15

---

## 1. Executive Summary

godot-mcp is a FastMCP 3.2+ server that controls a **live Godot 4 engine** over a local TCP bridge. It serves three roles in the fleet:

1. **Fleet visualization endpoint** — CAD→CFD pipelines (qcad-mcp, freecad-mcp, FluidX3D) and blender-mcp → GLB/OBJ import
2. **Game export pipeline** — itch.io and Steam shipping from MCP tools
3. **FOSS avatar renderer** — VRM avatar viewer with emotion-driven expressions, blendshapes, and viewport streaming, as an alternative to proprietary platforms (Resonite, VRChat)

**Two-process runtime (required):**

1. **Python MCP gateway** — port **10993** (REST + MCP SSE), webapp **10992**
2. **Godot bridge** — `main_bridge.tscn` + `mcp_bridge.gd` on TCP **9080**

The server starts even if the bridge is down; tools reconnect lazily.

---

## 2. Goals

| Goal | Success metric |
|------|----------------|
| Agent-driven scene control | `godot_status` returns FPS + bridge connected |
| Fleet geometry import | STL / GLB / OBJ / VRM via bridge actions |
| CFD visualization | CSV velocity fields + GPU particles |
| VRM avatar rendering | Import, display, express emotion, stream viewport |
| Web export | HTML5 via bridge or `godot --headless --export-release` fallback |
| itch.io shipping | Butler push via MCP, REST, `just ship`, dashboard `/ship` |
| Developer ergonomics | `just serve`, `just godot-bridge`, `just demo-run` |

---

## 3. MCP tool surface

### Core engine (31+ tools)

| Tool | Purpose |
|------|---------|
| `godot_status` | Engine + bridge health |
| `godot_import_stl` | Binary STL mesh |
| `godot_import_glb` | GLTF binary/text |
| `godot_import_obj` | Wavefront OBJ |
| `godot_import_vrm` | VRM avatar import (V-Sekai addon) |
| `godot_list_vrm` | List VRM models in depot |
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
| +15 more scene/animation/playtesting tools |

### Avatar pipeline (in development)

| Tool | Status | Purpose |
|------|--------|---------|
| `godot_import_vrm` | ✅ Done | Import VRM via V-Sekai addon |
| `godot_list_vrm` | ✅ Done | Browse avatar depot |
| `set_expression` | ⬜ P2 | Emotion blendshape mapping |
| `process_visemes` | ⬜ P3 | Lip-sync from TTS phonemes |
| `capture_viewport` | ⬜ P1 | MJPEG viewport stream |

### itch.io / Butler (6 tools)

| Tool | Purpose |
|------|---------|
| `itch_status` | Butler + API key + defaults |
| `godot_export_release` | Headless export |
| `itch_push_preview` | Butler diff before upload |
| `itch_push` | Upload to itch.io |
| `itch_latest_version` | Wharf API query |
| `ship_to_itch` | Export → preview → push |

---

## 4. Non-goals

- Replacing the Godot editor for manual level design
- Hosting multiplayer game servers
- Social VR platform (this is a FEATURE — see §7)
- Bundling Godot export templates in the MCP wheel

---

## 5. Avatar Pipeline — Why Godot

Godot serves as the fleet's **FOSS avatar renderer**, replacing the need for proprietary platforms (Resonite, VRChat) for the private AI companion use case.

| Feature | Godot + V-Sekai | Resonite | VRChat | Vircadia |
|---------|----------------|----------|--------|----------|
| Self-hosted | ✅ | ✅ | ❌ | ✅ |
| FOSS | ✅ MIT | ❌ | ❌ | ✅ |
| VRM import | ✅ via addon | ✅ native | ❌ | ❌ |
| Headless | ✅ --headless | ✅ headless | ❌ | ✅ |
| MCP control | ✅ 95 tools | ⚠️ basic | ⚠️ OSC | ❌ |
| Social features | ❌ (plus) | ✅ | ✅ | ✅ |
| Active dev | ✅ daily | ✅ weekly | ❌ EAC | ❌ dead |

**Downside** (is actually a plus): Godot has no social layer. No friends, no worlds browser, no moderation. For a private AI companion that lives on your machine and talks to you alone, this is exactly right. No EAC, no TOS, no platform risk.

See [VRM_AVATAR_PIPELINE.md](VRM_AVATAR_PIPELINE.md) for the full roadmap.

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
| `BUTLER_API_KEY` | itch.io API key |
| `ITCH_TARGET` | Default `user/game` slug |

---

## 7. Roadmap

### P1 — Core avatar scene
- [ ] Godot template project with VRM viewer scene + camera orbit + lighting
- [ ] Viewport streaming (MJPEG from Godot → webapp)

### P2 — Emotion-driven expression
- [ ] Blendshape mirroring (emotion tag → VRM expression)
- [ ] Auto-blink, breathing, idle animation

### P3 — Lip-sync
- [ ] Phoneme extraction from Gemini TTS
- [ ] Mouth blendshape mapping

### P4 — Scene composition
- [ ] Environment presets (room, shrine, classroom)
- [ ] Background switching, prop spawning

### P5 — Editor automation
- [ ] VRM-to-scene wizard (`godot_vrm_create_scene`)
- [ ] Animation retargeting, pose presets, screenshots

---

## 8. References

- Repo: `D:\Dev\repos\godot-mcp`
- VRM pipeline: [VRM_AVATAR_PIPELINE.md](VRM_AVATAR_PIPELINE.md)
- Architecture: [architecture.md](architecture.md)
- Central fleet page: `mcp-central-docs/projects/godot-mcp/README.md`
