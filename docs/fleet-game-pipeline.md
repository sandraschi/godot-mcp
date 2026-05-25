# Fleet Game Pipeline — Makers → Godot

**Last updated:** May 2026  
**Audience:** Hobby 3D games and godot-mcp users leveraging the MCP fleet (blender-mcp, worldlabs-mcp, etc.).

**Related:** [Maker bridges](../maker/README.md) · [Little game guide](little-game-guide.md) · [Ship to itch.io](ship-to-itch.md) · MCD [worldlabs-mcp integration](https://github.com/sandraschi/mcp-central-docs/blob/main/integrations/worldlabs-mcp.md)

---

## Fleet role map

```
Prompt / CAD / scan
        ↓
   maker MCPs (authoring)
        ↓
   D:\Dev\repos\_exchange\   ← fleet handoff bus
        ↓
   godot-mcp (import, scene, particles, export)
        ↓
   itch.io / HTML5 / Windows
```

| Repo | Port (typical) | Best for games |
|------|----------------|----------------|
| **blender-mcp** | 10848 | Characters, props, kits, GLB export, decimate, materials |
| **worldlabs-mcp** | 10864 / 10865 | AI worlds — **splats** (SPZ/RAD) + **collision GLB** |
| **freecad-mcp** | 10944 | Hard-surface props, mechanical parts → STL |
| **qcad-mcp** | 10966 | 2D → STL footprints |
| **godot-mcp** | 10993 | Import GLB/OBJ/STL, lights, particles, export, ship |
| **unity3d-mcp** | (varies) | Reference: **native Gaussian splat** in-engine (Aras-P package) |

2D satirical games (e.g. `samples/vibecode-runner`) do not need makers — fleet helps when you want **3D assets or worlds**.

---

## What works today

### 0. Fleet automation (godot-mcp v0.2.1+)

Module `godot_mcp/fleet/` wraps exchange + World Labs HTTP:

```text
worldlabs-mcp bridge (10865)
  → fleet_worldlabs_get_world / stage_mesh / import_mesh
  → D:\Dev\repos\_exchange\models\worldlabs\*.glb
  → godot_import_glb (bridge 9080)
```

Just: `just fleet-status`, `just fleet-worldlabs-import <world_id>`.  
Assessment: [FLEET_ASSESSMENT.md](FLEET_ASSESSMENT.md).

### 1. Blender → Godot (recommended for game assets)

See [maker/blender-bridge-example.md](../maker/blender-bridge-example.md).

```text
blender-mcp: model + decimate + export_glb
  → copy to _exchange/models/
  → godot-mcp: godot_import_glb
  → godot_set_material / godot_add_light
  → just little-game-export web
```

**Use for:** trees, crates, player mesh, low-poly enemies, kitbash levels.

### 2. World Labs → Godot **mesh** (collision proxy) — automated

Marble outputs two things:

| Asset | Format | In Godot today |
|-------|--------|----------------|
| **Visual splat** | `.spz`, `.rad`, `.ply` | ❌ Staged to exchange; Spark viewer URL returned |
| **Collision / Chisel mesh** | `.glb` | ✅ `fleet_worldlabs_import_mesh` or `godot_import_glb` |

```powershell
just fleet-worldlabs-info YOUR_WORLD_ID
just fleet-worldlabs-import YOUR_WORLD_ID LevelCollider
```

**Workflow:**

1. `worldlabs-mcp`: `generate_world_from_text` → `get_world` → download **`mesh_url`** (GLB).
2. Save under `D:\Dev\repos\_exchange\models\worldlabs\<world_id>.glb`.
3. `just depot-import D:\Dev\repos\_exchange\models\worldlabs\....glb WorldBlockout`
   or MCP `godot_import_glb`.
4. Use as **invisible collision**, low-poly stand-in, or distant backdrop — not the full splat look.

### 3. Fleet exchange depot

Convention: `D:\Dev\repos\_exchange\` (`cad/`, `models/`, `cfd/`, …).

```powershell
just depot-ls
just depot-import D:\Dev\repos\_exchange\models\robot.glb Robot
```

Any maker that writes into `_exchange` can feed godot-mcp without custom glue.

### 4. MCP bridge federation

```powershell
$env:MCP_BRIDGE_URLS = "http://localhost:10848/sse,http://localhost:10865/sse"
just serve
```

Agents can call blender/worldlabs tools and godot tools in one session (see `godot_mcp.mcp_bridge`).

---

## Can you put a World Labs **splat** in a Godot world?

**Short answer:** Not end-to-end in the fleet **yet**. Unity has it; Godot needs an addon path.

### Why splats ≠ GLB

Gaussian splats are **millions of oriented 3D Gaussians** (radiance field), not triangles. Godot’s built-in importer expects meshes (GLB/OBJ/STL). The pretty Marble look is in **SPZ/RAD**, not the Chisel GLB.

### Fleet status

| Path | Status |
|------|--------|
| worldlabs → **Spark viewer** (browser) | ✅ worldlabs-mcp web / `.rad` streaming |
| worldlabs → **Unity** splat renderer | ✅ unity3d-mcp + `com.aras-p.gaussian-splatting` |
| worldlabs → **Blender** SPZ handoff | ✅ `/api/handoff` → blender-mcp |
| worldlabs → **Resonite** | ✅ OSC / resonite-mcp |
| worldlabs → **Godot** SPZ/splat | ❌ **Not wired** |
| worldlabs → **Godot** GLB mesh only | ✅ today via `godot_import_glb` |

### Practical options until Godot splat support exists

**A. Hybrid hub (fastest)**  
- **Game:** Godot (gameplay, UI, 2D/3D logic).  
- **World preview:** Link or embed worldlabs Spark viewer URL for “enter world” menu (HTML5 export can open external URL).  
- **Collision in Godot:** Import Chisel GLB for physics/walking.

**B. Mesh-only world (good enough for blockout)**  
- Import GLB, retexture in Godot, add `CharacterBody3D` + `StaticBody3D` from mesh.  
- Loses splat lighting; fine for prototyping.

**C. Blender bake-down**  
- Handoff SPZ → blender-mcp (`blender_splatting` / crop / collision).  
- Bake to textured low-poly or export GLB → godot.  
- Manual quality tradeoff; fleet handoff exists to Blender, not yet automated to Godot.

**D. Future: Godot Gaussian splat addon + godot-mcp tool**  
- Community addons exist (e.g. Godot 4 Gaussian splat loaders — evaluate license + Web export support).  
- Planned fleet shape:

```text
worldlabs-mcp: get_world → download spz to _exchange/worldlabs/
godot-mcp: godot_import_splat (new) → SplatInstance3D or addon node
godot_export_web → verify splat shader works in HTML5 (often the hard part)
```

Web/HTML5 splat rendering is **much harder** than desktop; Spark uses WebGL2 + Rust. Expect **desktop-first** splats in Godot, web second.

---

## Suggested workflows by game type

### Little 2D game (VibeCode Runner)

Fleet optional. Ship with `just ship web vibecode`. Makers add scope, not speed.

### 3D hobby prototype

1. **Blockout:** worldlabs GLB **or** blender kit pieces → godot.  
2. **Hero assets:** blender-mcp → GLB → materials in Godot.  
3. **Juice:** godot particles, lights, camera.  
4. **Ship:** `just ship web <game>`.

### “Walk around my AI world”

1. worldlabs: generate world, cache SPZ locally (Spark viewer).  
2. godot: import **same world’s GLB** for floor/collision.  
3. Third-person controller in Godot; sky/panorama from worldlabs `panorama_url` as `PanoramaSkyMaterial` if desired.  
4. Optional: open full splat fidelity in Spark tab for screenshots / trailer.

### CAD-anchored sim viz (existing fleet strength)

```
qcad → freecad → FluidX3D CSV → godot_mcp velocity particles
```

See [maker/README.md](../maker/README.md) and [ai-flows.md](ai-flows.md).

---

## Improving games with makers (checklist)

| Need | Use | godot-mcp |
|------|-----|-----------|
| Low-poly prop | blender-mcp `export_glb` | `godot_import_glb` |
| Terrain heightmap | worldlabs (doc example) / blender | bridge `import_heightmap`* |
| AI environment blockout | worldlabs `mesh_url` GLB | `godot_import_glb` |
| Full splat beauty | worldlabs Spark / Unity | hybrid or wait for splat tool |
| Textures | gimp-mcp / blender bake | `godot_set_material` |
| Wind/CFD feel | FluidX3D → CSV | `godot_load_velocity_field`, particles |
| Share build | — | `ship_to_itch`, `/ship` |

\*Heightmap import in bridge example is aspirational — verify against current `mcp_bridge.gd` actions before relying on it.

---

## Next fleet wiring (recommended)

1. **`worldlabs → _exchange → godot_import_glb`** — documented Just recipe (download mesh from `get_world`).  
2. **`godot_import_splat` spike** — evaluate Godot 4 addon + desktop export only.  
3. **Maker workflow in godot-mcp** — `ship_world_mesh` preset: world id → GLB import → empty scene with collision.  
4. **Document handoff gap** in worldlabs-mcp EXPORT_GUIDE § Godot (mirror this doc).

---

## See also

- [maker/blender-bridge-example.md](../maker/blender-bridge-example.md)  
- [maker/worldlabs-bridge-example.md](../maker/worldlabs-bridge-example.md)  
- `worldlabs-mcp/docs/EXPORT_GUIDE.md` — SPZ vs GLB payload  
- `unity3d-mcp` — reference splat integration (`WorldLabsManager`)  
- MCD fleet mirror: `projects/godot-mcp/FLEET_GAME_PIPELINE.md`
