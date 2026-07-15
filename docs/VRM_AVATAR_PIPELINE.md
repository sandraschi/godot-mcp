# VRM Avatar Pipeline — Godot as FOSS Avatar Renderer

**Status**: In progress  
**Last updated**: 2026-07-15

## Why Godot for Avatars

Godot is MIT-licensed, self-hosted, headless-capable, and controllable via MCP. It has no social layer, no multiplayer requirement, no EAC, no SaaS dependency — which is exactly what we want for a private AI companion. The avatar renders on Goliath, streams to your browser, and answers to no platform TOS.

## Current State

| Capability | Status | Details |
|------------|--------|---------|
| VRM import via bridge | ✅ | `godot_import_vrm(path, name)` copies VRM to project, loads via V-Sekai addon |
| V-Sekai addon install | ✅ | `install_community_plugin("vrm")` — adds VRM 1.0 + MToon + spring bones |
| Model listing | ✅ | `godot_list_vrm()` — lists `.vrm` files from `~/.avatarmcp/models/` |
| GLTF/GLB import | ✅ | Existing `godot_import_glb` for non-VRM 3D assets |
| Scene manipulation | ✅ | 31 core tools for lighting, camera, materials, nodes |
| Viewport capture | ⬜ | `godot_capture_viewport` exists but needs MJPEG streaming |
| Headless mode | ✅ | `--headless` flag confirmed working (used in launch_bridge) |
| Avatar depot | ✅ | `~/.avatarmcp/models/` shared across fleet |

## TODO

### P1 — Core avatar scene

- [ ] **Godot template project** — create `templates/vrm-viewer/` with:
  - VRM auto-load scene (watches `models/` directory)
  - Camera orbit controller (drag to rotate)
  - Three-point lighting setup
  - HDRI skybox
  - Ground plane with shadow
- [ ] **Viewport streaming** — MJPEG or WebRTC stream from Godot viewport to webapp
  - GDScript: capture `$Viewport.get_texture().get_image()` → encode JPEG → serve via HTTP
  - Python side: proxy stream through godot-mcp API
  - Webapp: `<img>` tag with MJPEG stream or WebRTC `<video>`

### P2 — Emotion-driven expression

- [ ] **Blendshape mirroring** — emotion tag → VRM expression preset
  - Map: `[happy]` → `joy`, `[sad]` → `sorrow`, `[angry]` → `anger`, etc.
  - GDScript bridge command: `set_expression(expression_name, weight)`
  - Learnbot-mcp calls this alongside TTS and robot motion
- [ ] **Auto-blink** — periodic blink blendshape
- [ ] **Breathing** — subtle chest/body idle animation
- [ ] **Eye gaze** — track camera position (simple look-at)

### P3 — Lip-sync

- [ ] **Phoneme extraction** — Gemini TTS returns viseme/phoneme data (check API)
- [ ] **Mouth blendshape mapping** — map phonemes to VRM mouth shapes (A, I, U, E, O)
- [ ] **GDScript bridge** — `process_visemes(phoneme_array)` — blendshape keyframes from TTS

### P4 — Scene composition

- [ ] **Environment presets** — room, garden, shrine, classroom (tscn files)
- [ ] **Background switching** — `godot_set_environment(preset)` changes HDRI + ground
- [ ] **Object spawning** — props, furniture, teaching aids around the avatar
- [ ] **Multi-avatar** — load multiple VRMs for group scenes (teacher + student)

### P5 — Social layer (optional, lightweight)

Godot ships with ENet (UDP), WebRTC, and WebSocket built in. Adding social features uses existing modules — no engine fork needed.

- [ ] **ENet sync** — sync avatar position/rotation/expression to a second client
  - GDScript: `ENetMultiplayerPeer`, 50 lines for transform replication
  - Web export with `--headless` as lobby server
- [ ] **WebRTC voice** — speech-mcp already handles TTS; WebRTC for user-to-user voice
  - Godot's `WebRTCPeerConnection` wrapper
  - Or: learnbot handles voice, users just see the avatar
- [ ] **Web export** — `godot_export_web` → friend opens URL → sees Miko-chan
  - No install, no login — just a browser tab
- [ ] **Guest book** — persistent messages from visitors appear as notecards in-world
  - SQLite-backed, served via godot-mcp REST

**Design philosophy**: The social layer is additive, not foundational. The avatar works perfectly alone. Adding sync, voice, or web export doesn't change the core loop — it just lets other people see what you see. This keeps the architecture simple and avoids the feature creep that killed Vircadia.

### P6 — Godot editor automation

- [ ] **VRM-to-scene wizard** — `godot_vrm_create_scene(vrm_path, preset="studio")` — full scene setup in one command
- [ ] **Avatar animation** — load FBX/GLB animation clips, retarget to VRM skeleton
- [ ] **Pose presets** — T-pose, A-pose, sitting, bowing, pointing
- [ ] **Screenshot** — `godot_vrm_screenshot()` — render avatar with current expression and lighting

### P7 — Research directions

Interesting papers and concepts to explore for novel social avatar interaction:

- **arXiv:2403.17134** — Coordinated inauthentic behavior ecologies (anti-patterns to avoid)
- **Nowak & Biocca (2003)** — "The Effect of Agency and Anthropomorphism on Sense of Telepresence" — classic on avatar agency perception
- **Blascovich & Bailenson (2011)** — "Infinite Reality" — social presence theory for avatars
- **Slater & Wilbur (1997)** — "A Framework for Immersive Virtual Environments" — presence dimensions
- **Search arXiv cs.HC** for "avatar-mediated interaction" and "social presence virtual humans" for current work

## Architecture

```
learnbot-mcp (conversation + emotion tags)
    │
    ├── speech-mcp (Gemini TTS with prosody)
    ├── yahboom-mcp (robot motion — Boomy)
    │
    └── godot-mcp ──TCP──► Godot 4 --headless ──MJPEG► learnbot webapp
                                │
                                ├── V-Sekai/godot-vrm addon
                                │     ├── VRM 1.0 import
                                │     ├── Spring bones (hair, skirt)
                                │     ├── MToon shader
                                │     └── Expression blendshapes
                                │
                                ├── Template scene
                                │     ├── Camera orbit
                                │     ├── Three-point lighting
                                │     └── HDRI environment
                                │
                                └── Custom GDScript bridge
                                      ├── import_vrm
                                      ├── set_expression
                                      ├── process_visemes
                                      └── capture_viewport
```

## Why Not Vircadia / Resonite / VRChat

| Platform | Social? | FOSS? | Headless? | VRM? | MCP? | Active? |
|----------|---------|-------|-----------|------|------|---------|
| **Godot + V-Sekai** | None (plus) | ✅ MIT | ✅ | ✅ | ✅ (95 tools) | ✅ Daily |
| **Resonite** | Yes | ❌ | ✅ | ✅ | ⚠️ basic | ✅ Weekly |
| **Vircadia** | Yes | ✅ | ✅ | ❌ | ❌ | ❌ Dead |
| **VRChat** | Yes | ❌ | ❌ | ❌ | ⚠️ OSC only | ✅ EAC |

Godot's lack of social features is a feature for this use case — Miko-chan is a private companion, not a public avatar. No moderation, no EAC, no TOS, no strangers.
