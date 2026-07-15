# Tool Reference — Godot MCP

**95+ MCP tools** across all modules. Tools are registered via FastMCP 3.4
with versioning and READ_ONLY/MUTATING annotations.

---

## Engine Control (core_tools.py — 31 tools)

All require the Godot TCP bridge (port 9080) to be running.

| Tool | Annotations | Version | Description |
|------|-------------|---------|-------------|
| `godot_status` | READ_ONLY | 0.1.0 | Engine version, FPS, node count, bridge state |
| `godot_import_stl` | MUTATING | 0.1.0 | Import binary STL mesh as MeshInstance3D |
| `godot_import_glb` | MUTATING | 0.1.0 | Import GLB/GLTF model via GLTFDocument |
| `godot_import_obj` | MUTATING | 0.1.0 | Import Wavefront OBJ with MTL support |
| `godot_play_animation` | MUTATING | 0.1.0 | List/play GLB animation clips |
| `godot_load_velocity_field` | MUTATING | 0.1.0 | Load CSV velocity data (x,y,z,vx,vy,vz) |
| `godot_spawn_particles` | MUTATING | 0.1.0 | Create GPUParticles3D with configurable emission |
| `godot_animate_streamlines` | MUTATING | 0.1.0 | Animate particles along velocity field vectors |
| `godot_create_camera` | MUTATING | 0.1.0 | Create Camera3D with orbit controls |
| `godot_add_light` | MUTATING | 0.1.0 | Directional/ambient/omni light |
| `godot_set_material` | MUTATING | 0.1.0 | Assign StandardMaterial3D PBR to mesh |
| `godot_export_web` | MUTATING | 0.1.0 | HTML5/WebAssembly export via headless or in-editor |
| `godot_read_scene_tree` | READ_ONLY | 0.1.0 | Dump scene hierarchy as JSON |
| `godot_set_config` | MUTATING | 0.1.0 | Write to project.godot INI-style config |
| `godot_headless_verify` | READ_ONLY | 0.1.0 | Check headless mode + CLI command |
| `godot_capture_viewport` | READ_ONLY | 0.1.0 | Capture viewport as PNG, returns path + dimensions |
| `godot_simulate_input` | MUTATING | 0.1.0 | Keyboard/action/joypad/mouse/text input injection |
| `godot_read_node` | READ_ONLY | 0.1.0 | Read a single node's properties by name/path |
| `godot_inspect_resource` | READ_ONLY | 0.1.0 | Inspect SpriteFrames, TileSet, Materials, Textures as JSON |
| `godot_tilemap` | MUTATING | 0.1.0 | Read/edit TileMapLayer and GridMap cells |
| `godot_animation` | MUTATING | 0.1.0 | Query and author keyframes/tracks on AnimationPlayer |
| `godot_validate_meshes` | READ_ONLY | 0.1.0 | Detect corrupt mesh data (NaN, degenerate, zero normals) |
| `godot_profile` | READ_ONLY | 0.1.0 | Performance metrics + frame spike detection |
| `godot_help` | READ_ONLY | 0.1.0 | Context-aware tool help and examples |
| `godot_import_splat` | MUTATING | 0.2.0 | Import 3D Gaussian splats (.ply/.spz) with billboarded shader |
| `godot_state_digest` | READ_ONLY | 0.2.0 | Read structured game state (watch group or named nodes) |
| `godot_game_time` | MUTATING | 0.3.0 | Freeze/unfreeze/step the game clock deterministically |
| `godot_step_until` | MUTATING | 0.3.0 | Step frame-by-step until a GDScript condition is true |
| `godot_scene` | MUTATING | 0.1.0 | Portmanteau: add/remove/modify nodes, save scene |
| `godot_generate_procedural_texture` | MUTATING | 0.1.0 | Create gradient/noise/checker/solid textures at runtime |
| `start_bridge` | MUTATING | 0.1.0 | Locate Godot and launch headless with bridge addon |

---

## Itch.io Publishing (itch/tools.py)

| Tool | Annotations | Description |
|------|-------------|-------------|
| `itch_ops` | READ_ONLY | **Portmanteau**: status, export, preview, push, latest, ship |
| `itch_status` | READ_ONLY | Check Butler install, API key, default slug |
| `godot_export_release` | MUTATING | Export sample/custom project (web/windows) |
| `itch_push_preview` | READ_ONLY | Diff NEW/MODIFIED/DELETED before push |
| `itch_push` | MUTATING | Upload build via Butler |
| `itch_latest_version` | READ_ONLY | Query api.itch.io/wharf for newest build |
| `ship_to_itch` | MUTATING | Full pipeline: export -> preview -> push |

---

## Steam Publishing (steam/tools.py)

| Tool | Annotations | Description |
|------|-------------|-------------|
| `steam_ops` | READ_ONLY | **Portmanteau**: status, checklist, monetization, stage, prerelease, release, ship |
| `steam_status` | READ_ONLY | SteamPipe/steamcmd readiness, app/depot IDs |
| `steam_checklist` | READ_ONLY | Steam Direct release checklist |
| `steam_monetization_guide` | READ_ONLY | Pricing and revenue guidance |
| `steam_stage_build` | MUTATING | Export Windows -> fleet exchange for SteamPipe |
| `ship_to_steam_prerelease` | MUTATING | Upload to beta branch (dry_run=True default) |
| `ship_to_steam_release` | MUTATING | Upload to live branch (dry_run=True default) |
| `ship_to_steam` | MUTATING | End-to-end Steam ship pipeline |

---

## Fleet Pipeline (fleet/tools.py)

| Tool | Annotations | Description |
|------|-------------|-------------|
| `fleet_ops` | READ_ONLY | **Portmanteau**: exchange_status, import, worldlabs_get, worldlabs_stage_mesh, worldlabs_stage_splat, worldlabs_import |
| `fleet_exchange_status` | READ_ONLY | Depot assets and pipeline readiness |
| `fleet_import_from_exchange` | MUTATING | Import GLB/OBJ/STL from fleet exchange |
| `fleet_worldlabs_get_world` | READ_ONLY | Fetch Marble world asset URLs |
| `fleet_worldlabs_stage_mesh` | MUTATING | Download Chisel collision GLB to exchange |
| `fleet_worldlabs_stage_splat` | MUTATING | Download SPZ splat to exchange |
| `fleet_worldlabs_import_mesh` | MUTATING | Download + import Marble GLB into Godot |

---

## Game Builder (game_builder/tools.py)

| Tool | Annotations | Description |
|------|-------------|-------------|
| `design_game` | READ_ONLY | Natural language -> GamePlan (worlds, scenes, scripts) |
| `generate_game_worlds` | MUTATING | Marble world generation + collider GLB staging |
| `compose_game_scene` | MUTATING | Assemble Godot scene from GamePlan + worlds |
| `generate_game_logic` | MUTATING | Generate GDScript files from GamePlan (gdlint + godot --check-only validated) |
| `generate_game_tests` | MUTATING | Generate GUT test scripts + run via Godot headless |
| `generate_dialogue` | MUTATING | Generate DialogueManager.gd + Dialogic .dtl from NPCs |
| `export_and_ship` | MUTATING | Export + itch.io push in one call |
| `build_game` | MUTATING | End-to-end: design -> worlds -> compose -> logic -> test -> dialogue -> export |

---

## Artifact Depot (artifacts/tools.py)

| Tool | Annotations | Description |
|------|-------------|-------------|
| `artifact_list` | READ_ONLY | List artifacts, filter by type, paginated |
| `artifact_search` | READ_ONLY | Search by name/description/tags |
| `artifact_get` | READ_ONLY | Get single artifact details |
| `artifact_register` | MUTATING | Register new artifact in depot |
| `artifact_delete` | MUTATING | Delete artifact from depot |

---

## Bridge / Cross-Server (mcp_bridge/tools.py)

| Tool | Annotations | Description |
|------|-------------|-------------|
| `bridge_connect` | MUTATING | Connect to remote MCP server |
| `bridge_call_tool` | READ_ONLY | Call tool on remote MCP server |

---

## MCPB Packaging (mcpb/tools.py)

| Tool | Annotations | Description |
|------|-------------|-------------|
| `mcpb_build` | MUTATING | Build MCPB bundle for distribution |
| `mcpb_inspect` | READ_ONLY | Inspect MCPB bundle contents |

---

## Prefab UI Cards (prefabs/card_tools.py — app=True)

| Tool | Description |
|------|-------------|
| `show_godot_status_card` | Godot engine version, FPS, node count, bridge state |
| `show_itch_status_card` | Butler install, API key, default slug |
| `show_steam_status_card` | SteamPipe readiness, app/depot IDs |
| `show_fleet_status_card` | Exchange depot assets, World Labs bridge |
| `show_workflows_card` | Built-in workflows with step counts |
| `show_viewport_card` | Latest viewport capture |

---

---

## Documentation (docs_tools.py)

| Tool | Annotations | Description |
|------|-------------|-------------|
| `godot_docs` | READ_ONLY | Fetch Godot class reference as markdown from docs.godotengine.org |

## Prefabs, Prompts, Sampling, Workflows

| Module | Tools |
|--------|-------|
| `prefabs/tools.py` | `prefab_list`, `prefab_apply` |
| `prompts/tools.py` | `prompt_list`, `prompt_execute` |
| `sampling/tools.py` | `ai_describe_artifact`, `ai_generate_gdscript` |
| `workflows/tools.py` | `workflow_list` (scene_setup, particle_cfd, ship_web_itch, ship_windows_steam_beta, ship_windows_steam_release), `workflow_run` |
| `addon_tools.py` | `install_godot_addon`, `install_community_plugin` |
