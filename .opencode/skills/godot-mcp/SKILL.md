# godot-mcp

AI-driven Godot 4 engine control via MCP — scene manipulation, 3D import, particles, animation, publishing.

## Before starting work
1. Check bridge status: `godot_status`
2. Read engine state: `godot_read_scene_tree` or `godot_state_digest`
3. If bridge is down, call `start_bridge` to launch Godot headless

## Key tools
- **Scene**: `godot_scene(operation="add_node"|"remove_node"|"modify_node"|"save_scene")`
- **Import**: `godot_import_stl`, `godot_import_glb`, `godot_import_obj`
- **Read**: `godot_read_node` (single node), `godot_read_scene_tree` (full), `godot_state_digest` (watch group)
- **Input**: `godot_simulate_input` (key, action, joypad, mouse, text)
- **Playtesting**: `godot_game_time(action="freeze"|"unfreeze"|"step")`, `godot_step_until(condition="...")`
- **Capture**: `godot_capture_viewport`
- **Publishing**: `itch_ops`, `steam_ops`

## At end of work
- Save scene: `godot_scene(operation="save_scene")`
- Export if shipping: `export_and_ship` or `ship_to_itch`
