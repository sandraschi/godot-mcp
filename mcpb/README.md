# godot-mcp (MCPB Bundle)

Godot MCP server - Godot 4.x engine control via TCP bridge, STL/GLB/OBJ import, GPU particles, animation, HTML5 export, itch.io/Steam shipping, AI game builder through MCP tools and REST API

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "godot-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "godot_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **list_skills_api**: List all available skills.
- **get_skill_api**: Get the content of a specific skill.
- **fleet_health**: fleet_health
- **fleet_diagnostics**: fleet_diagnostics
- **api_status**: Server status including Godot engine and TCP bridge info.
- **api_capabilities**: Runtime feature gating for the webapp (fleet capability introspection standard).
- **list_files**: List uploaded files and output files.
- **download_file**: Download a file from uploads or outputs.
- **execute_tool**: Execute a Godot MCP tool via REST bridge.
- **start_bridge_endpoint**: Locate Godot and launch it headless with the MCP bridge addon.
- **find_godot_endpoint**: Check if Godot is installed and where.
- **llm_detect**: Detect GPU, VRAM, Ollama, and installed models.
- **llm_recommend**: Recommend the best LLM model based on detected hardware + installed models.
- **capture_viewport_endpoint**: Capture Godot viewport as PNG. Bridge must be connected.
- **simulate_input_endpoint**: Simulate keyboard input in the Godot engine. Bridge must be connected.
- **profile_snapshot_endpoint**: Read Godot performance metrics (14 monitors).
- **profile_enable_endpoint**: Enable/disable auto-profiling (300-frame rolling window).
- **profile_history_endpoint**: Read profiling history with spike detection.
- **read_node_endpoint**: Read a single node's properties by name or path.
- **state_digest_endpoint**: Read structured game state (watch group or named nodes).
- **validate_meshes_endpoint**: Validate all meshes for geometric corruption.
- **procedural_texture_endpoint**: Generate a procedural texture (gradient, noise, checker, solid).
- **live_viewport**: Return the latest viewport capture as a PNG image.
- **list_plugins**: List available community plugins and their install status.
- **install_plugin**: Install a community plugin from the registry.
- **stream_logs**: stream_logs
- **mobile_help**: Full protocol reference for iOS mobile clients - machine-readable JSON.
- **mobile_command_fallback**: REST fallback for iOS mobile commands (stateless, no subscriptions).
- **install_addon**: Install the Godot MCP bridge addon into a target project.
- **llm_chat_stream**: POST /api/llm/chat/stream - streaming chat via Ollama/OpenAI-compatible.
- **llm_chat**: POST /api/llm/chat - non-streaming chat.
- **get_settings**: get_settings
- **save_settings**: save_settings
- **list_artifacts**: list_artifacts
- **search_artifacts**: search_artifacts
- **get_artifact**: get_artifact
- **download_artifact**: download_artifact
- **register_artifact**: register_artifact
- **delete_artifact**: delete_artifact
- **fleet_status_route**: fleet_status_route
- **exchange_import_route**: exchange_import_route
- **worldlabs_world_route**: worldlabs_world_route
- **worldlabs_stage_mesh_route**: worldlabs_stage_mesh_route
- **worldlabs_stage_splat_route**: worldlabs_stage_splat_route
- **worldlabs_import_mesh_route**: worldlabs_import_mesh_route
- **design_route**: design_route
- **worlds_route**: worlds_route
- **compose_route**: compose_route
- **logic_route**: logic_route
- **export_route**: export_route
- **build_route**: build_route
- **itch_status_route**: itch_status_route
- **push_preview_route**: push_preview_route
- **push_route**: push_route
- **ship_route**: ship_route
- **latest_route**: latest_route
- **itch_status_status**: itch_status(status)
- **itch_status_export**: itch_status(export)
- **itch_status_preview**: itch_status(preview)
- **itch_status_push**: itch_status(push)
- **itch_status_latest**: itch_status(latest)
- **itch_status_ship**: itch_status(ship)
- **logs_query**: logs_query
- **logs_stats**: logs_stats
- **logs_export**: logs_export
- **logs_clear**: logs_clear
- **steam_status_route**: steam_status_route
- **steam_checklist_route**: steam_checklist_route
- **steam_monetization_route**: steam_monetization_route
- **steam_stage_route**: steam_stage_route
- **steam_upload_prerelease_route**: steam_upload_prerelease_route
- **steam_upload_release_route**: steam_upload_release_route
- **steam_ship_route**: steam_ship_route
- **steam_status_status**: steam_status(status)
- **steam_status_checklist**: steam_status(checklist)
- **steam_status_monetization**: steam_status(monetization)
- **steam_status_stage**: steam_status(stage)
- **steam_status_prerelease**: steam_status(prerelease)
- **steam_status_release**: steam_status(release)
- **steam_status_ship**: steam_status(ship)
- **install_godot_addon**: install_godot_addon
- **install_community_plugin**: install_community_plugin
- **godot_status_read**: godot_status(read)
- **godot_status_set_cell**: godot_status(set_cell)
- **godot_status_erase_cell**: godot_status(erase_cell)
- **godot_status_clear**: godot_status(clear)
- **vbot_connect**: vbot_connect
- **vbot_subscribe**: vbot_subscribe
- **vbot_perceive**: vbot_perceive
- **vbot_send_state**: vbot_send_state
- **vbot_poll_actions**: vbot_poll_actions
- **vbot_bridge_status**: vbot_bridge_status
- **vbot_disconnect**: vbot_disconnect

## Requirements

- Python 3.12+
- uv
