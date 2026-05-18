# Godot MCP — Skill

You are connected to the Godot MCP server, which controls the Godot 4 game engine via WebSocket bridge.

## When to Use This Server

Call this server's tools when:
- You want to create, modify, or inspect a 3D scene in Godot
- You need to import STL geometry for visualization
- You need to load CFD velocity field data and animate particles along it
- You need to set up cameras, lights, and PBR materials
- You want to export a Godot scene to HTML5/WebAssembly
- You want an AI-generated description for a game asset (uses LLM sampling)

## Tool Categories

### Scene Management
- `godot_status` — Check engine status, FPS, node count
- `godot_read_scene_tree` — Inspect the full scene hierarchy
- `godot_set_config` — Modify project.godot settings

### Geometry
- `godot_import_stl` — Import STL mesh as MeshInstance3D

### CFD Visualization
- `godot_load_velocity_field` — Load CSV velocity data
- `godot_spawn_particles` — Create GPU particle system
- `godot_animate_streamlines` — Animate particles along velocity field

### Scene Composition
- `godot_create_camera` — Add camera with orbit controls
- `godot_add_light` — Add directional/ambient/omni light
- `godot_set_material` — Assign PBR material to mesh

### Export
- `godot_export_web` — Export scene to HTML5

### Workflows (Agentic)
- `workflow_list` — List multi-step workflows
- `workflow_run` — Execute a workflow (e.g. scene_setup, particle_cfd)

### Prefabs (Templates)
- `prefab_list` — List reusable component templates
- `prefab_apply` — Apply a prefab with parameters

### Artifacts
- `artifact_list` — List items in the local depot
- `artifact_search` — Search depot by name/tags
- `artifact_get` — Get artifact details
- `artifact_register` — Register a new artifact
- `artifact_delete` — Remove an artifact

### AI (Sampling)
- `ai_describe_artifact` — Generate artifact description via LLM
- `ai_generate_gdscript` — Generate GDScript code via LLM

## Workflow Pattern

For a typical scene setup:
1. `godot_create_camera` — position the view
2. `godot_add_light` — illuminate the scene
3. `godot_import_stl` — load geometry
4. `godot_set_material` — style the mesh

Or use `workflow_run(workflow_name="scene_setup")` to do all at once.

## Tips

- Godot must be running with the MCP bridge addon on port 9080
- The bridge connects lazily — first tool call may trigger connection
- Use `godot_export_web` for HTML5 builds deployable anywhere
