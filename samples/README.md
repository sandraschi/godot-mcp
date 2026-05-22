# Sample Games

This directory contains Godot 4 sample games cloned from open-source repos.
Each is a full Godot project you can open and run.

## Included Samples

| Game | Source | Genre | Godot | Description |
|------|--------|-------|-------|-------------|
| godot-demo-projects | godotengine/demo-projects | Mixed (50+) | 4.x | Official 50+ demos covering 2D, 3D, audio, XR, networking, GUI |
| procedural-generation | gdquest-demos | PCG | 4.x | Procedural generation demos: dungeons, worlds, weapons |
| heart-platformer | uheartbeast | 2D Platformer | 4.x | Platformer movement template with juice and polish |
| skelerealms | SlashScreen | Open World RPG | 4.x | Bethesda-style 3D open world RPG framework |

## Opening a Sample

```powershell
just demo-list
just demo-run                  # default: Heart Platformer (Godot 4.0)
just demo-run platformer       # official 2D platformer
just demo-run dodge            # Dodge the Creeps
just demo-run pong
just demo-run procedural
just demo-run skelerealms
```

Or open a project directly:

```powershell
godot --path samples\godot-demo-projects\2d\platformer
```

MCP bridge (`just godot-bridge`) uses the repo root `main_bridge.tscn` project. Sample games run in a **second** Godot window and do not replace the bridge.

**First run:** cloned demos have no `.godot/imported/` cache until Godot imports PNGs/audio for your engine version. `just demo-run` does this automatically; or run `just demo-import pong` once manually.

**Godot 4.6 demos on 4.4 engine:** Official `godot-demo-projects` target 4.6 (`libraries/` scene syntax). After clone, run:

```powershell
pwsh -File scripts/patch-platformer-godot44.ps1
```

Or install Godot 4.6: `just install-godot version="4.6"`. **Heart Platformer** is native 4.0 and needs no patch.

## MCPB Bundles

Each sample has an MCPB bundle in samples/bundles/ that describes
the tool sequence needed to recreate it via godot-mcp tools.
