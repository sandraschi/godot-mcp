# Avatars and VRM (godot-mcp)

godot-mcp automates **Godot 4** for games, CFD visualization, and fleet mesh import. It is **not** a VRM or MMD server.

**Decision record:** `mcp-central-docs/docs/avatars/GODOT_VRM_MMD_DECISION.md`

## Can we add VRM loader + MMD player?

| Tool | Can? | Should (fleet)? |
|------|------|-----------------|
| `godot_import_vrm` | Yes (~2–5 days + addon) | **Optional** — only if Godot needs live spring bones |
| `godot_play_vmd` | Hard (1–2+ weeks) | **No** — bake in blender-mcp instead |
| `godot_play_animation` | **Shipped** | **Yes** — use after Blender-baked GLB import |

**Doll Dancer iOS app:** Swift + Xcode 26 agentic — **not** godot-mcp.

## What connects to the avatar pipeline

| Avatar need | Use instead of godot-mcp |
|-------------|-------------------------|
| Load VRM | avatar-mcp + VTube / Unity / native iOS app |
| VRoid Hub | avatar-mcp `hub_download` |
| MMD dances (VMD) | blender-mcp bake → GLB → `godot_import_glb` |
| VRChat upload | unity3d-mcp + vrchat-mcp |

## Recommended character path (games)

```text
avatar-mcp (VRM staging)
    → blender-mcp (export GLB + baked animation)
        → godot_import_glb
            → godot_play_animation (planned)
```

## Two fleet tracks

```text
Social / iOS:  Hub → avatar-mcp → Swift app (Xcode 26)
Game:          Blender → godot-mcp → itch/web export
```

## Central documentation

- `mcp-central-docs/docs/avatars/GODOT_VRM_MMD_DECISION.md`
- `mcp-central-docs/docs/avatars/GODOT_AND_AVATARS.md`
- `mcp-central-docs/apple/development/AGENTIC_XCODE_26.md`
- `docs/fleet-game-pipeline.md` (repo)

## Ports

| Port | Role |
|------|------|
| 10992 | Dashboard |
| 10993 | MCP / HTTP API |
| 9080 | GDScript TCP bridge |
