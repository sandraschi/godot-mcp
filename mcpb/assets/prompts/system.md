# godot-mcp — Complete MCP Server Capabilities

## Server Overview

godot-mcp is a Model Context Protocol (MCP) server that provides programmatic control over the Godot 4.x game engine through a comprehensive suite of tools, resources, prompts, and workflows. It bridges AI agents and Godot using a WebSocket connection, enabling full scene manipulation, 3D asset import (STL, GLB/GLTF, OBJ), animation playback, GPU particle system management, PBR material assignment, project configuration, HTML5 export, and complete publishing pipelines to itch.io via Butler CLI and Steam via steam-mcp.

The server architecture consists of three integrated layers: (1) a Python FastMCP server running on port 10993 that exposes 55+ MCP tools via stdio or HTTP/SSE dual transport, (2) a WebSocket TCP bridge connecting to a running Godot 4 editor or headless binary on port 9080 for real-time scene manipulation, and (3) a FastAPI REST API layer for fleet integration, artifact depot management, game building pipeline orchestration, iOS mobile gateway support, and cross-server MCP bridging.

Integration points include: Godot Engine via TCP bridge on port 9080 (sends GDScript-coded commands for mesh import, camera creation, lighting, material assignment, animation, particle systems, export, and scene tree queries), World Labs bridge on port 10865 for generative 3D world mesh/splat download, steam-mcp on port 11020 for Steamworks publishing operations, fleet exchange depot at a configurable cross-repo directory for GLB/OBJ/STL asset interchange, the local artifact depot at data/artifacts/ for persisting reusable scenes, meshes, materials, particle systems, GDScripts, and prefabs, and an iOS mobile WebSocket gateway at /mobile/v1 for ARKit spatial interactions and remote scene control.

## Tools — Complete Reference with Parameters and Examples

### Scene Management (Godot Bridge)

The Godot bridge connects to a running Godot 4 editor or headless instance via TCP on port 9080. All godot_* tools communicate through this bridge, sending JSON-encoded commands that are processed by GDScript code on the Godot side.

**godot_status** (annotations=READ_ONLY, version=0.1.0): Query the connected Godot engine for live state including engine version string, current FPS, total scene node count, and bridge connection health. Takes no parameters beyond the implicit bridge connection. Returns a structured dict with keys: success (bool), data (dict containing godot_version as string, node_count as integer, fps as float, bridge_connected as bool). Example: `await godot_status()` returns `{"success": true, "data": {"godot_version": "4.4.stable", "node_count": 42, "fps": 60.0, "bridge_connected": true}}`. Use as the first call to verify bridge connectivity before any scene manipulation.

**godot_read_scene_tree** (annotations=READ_ONLY, version=0.1.0): Perform a recursive dump of the entire Godot scene hierarchy, returning every node with its name, GDScript type string, and full scene path. The output is a nested JSON structure mirroring the Godot editor Scene panel. Takes no parameters. Returns: success (bool), data (dict with scene_tree as nested dict with name, type, path, children keys, and node_count as integer). Example: `await godot_read_scene_tree()` returns the complete node hierarchy. Use for debugging scene structure, verifying imports, or understanding the scene before manipulation.

**godot_set_config** (annotations=MUTATING, version=0.1.0): Write a key-value pair to the project.godot INI-style configuration file via ConfigFile API. Parameters: section (str, required): the config section name such as "application", "rendering", "display", "physics", "audio". key (str, required): the config key such as "config/name", "quality/driver/driver_name", "window/size/width". value (str, required): the config value as a string. Returns: success (bool), data (dict with updated as bool, section, key, value). Examples: `await godot_set_config(section="application", key="config/name", value="My Project")`, `await godot_set_config(section="rendering", key="quality/driver/driver_name", value="GLES3")`. The change takes effect immediately in the Godot editor but requires a restart for runtime effects.

**godot_headless_verify** (annotations=READ_ONLY, version=0.1.0): Check whether the connected Godot engine is running in headless mode (no display server). Returns headless status and a suggested CLI command for running a GDScript in headless mode. Parameters: script (str, default "res://dev/mcp_verify.gd"): path to a GDScript to verify. Returns: success (bool), data (dict with headless as bool, script_path as str, message as str). Example: `await godot_headless_verify(script="res://tests/mcp_headless_test.gd")`.

### Node & Mesh Creation

**godot_create_camera** (annotations=MUTATING, version=0.1.0): Create a Camera3D node in the scene with an attached GDScript-based orbit controller. The camera is set as current (active). Parameters: name (str, default "MCP_Camera"): node name. position_x (float, default 0.0): X position in world space. position_y (float, default 5.0): Y position. position_z (float, default 10.0): Z position. look_at_x/y/z (float, default 0.0): target point for the camera to face. fov (float, 1-179, default 75.0): vertical field of view in degrees. Returns: success (bool), data (dict with created as bool, name, fov, position dict). Examples: `await godot_create_camera(name="RenderCam", position_y=10, position_z=15, fov=60)`, `await godot_create_camera(name="CloseUp", position_x=2, position_y=1, position_z=3, look_at_x=0, look_at_y=0, look_at_z=0)`.

**godot_add_light** (annotations=MUTATING, version=0.1.0): Add a dynamic light source node. Supports three types: directional (DirectionalLight3D, parallel sun-like rays, no position needed), ambient (no physical node, sets environment ambient light), omni (OmniLight3D, point light with position). Parameters: light_type (str, default "directional"): one of "directional", "ambient", "omni". name (str, optional): node name, auto-generated if empty. intensity (float, ge=0, default 1.0): light energy. position_x/y/z (float, default 5.0): light world position, only used for omni/spot types. Returns: success (bool), data (dict with created, name, type, intensity). Examples: `await godot_add_light(light_type="directional", intensity=2.0)`, `await godot_add_light(light_type="omni", name="KeyLight", intensity=1.5, position_x=0, position_y=3, position_z=5)`.

**godot_set_material** (annotations=MUTATING, version=0.1.0): Create and assign a StandardMaterial3D to a MeshInstance3D node. Sets PBR parameters. Parameters: node (str, required): name of the target MeshInstance3D node. color (str, default "#ffffff"): hex RGB/RGBA albedo color. roughness (float, 0-1, default 0.5): PBR roughness where 0.0 is mirror and 1.0 is fully diffuse. Returns: success (bool), data (dict with set as bool, node, color, roughness). Examples: `await godot_set_material(node="STL_Mesh", color="#4488ff", roughness=0.3)`, `await godot_set_material(node="Ground", color="#88aa44", roughness=0.8)`, `await godot_set_material(node="MetalPart", color="#aaaaaa", roughness=0.1)`.

### 3D Asset Import

**godot_import_stl** (annotations=MUTATING, version=0.1.0): Import a binary STL file as a MeshInstance3D. Reads STL vertex and normal data on the Godot side, creates an ArrayMesh, and adds it to the scene. Common pipeline: freecad-mcp or qcad-mcp exports STL, which is then imported here. Parameters: path (str, required): absolute file path to the .stl file. name (str, default "STL_Mesh"): resulting MeshInstance3D node name. scale (float, ge=0.001, default 1.0): uniform scale factor. position_x/y/z (float, default 0.0): world position. Returns: success (bool), data (dict with imported, name, vertices as int, aabb with size_x/y/z floats). Example: `await godot_import_stl(path="C:/uploads/part.stl", name="MyPart", scale=0.01)`.

**godot_import_glb** (annotations=MUTATING, version=0.1.0): Import a GLB (binary) or GLTF (text) glTF 2.0 model using Godot's native GLTFDocument importer. Preserves node hierarchy, mesh data, materials, and animation tracks from the glTF file. This is the primary import path for the blender-mcp to godot-mcp pipeline. Parameters: path (str, required): absolute file path to .glb or .gltf file. name (str, default "GLB_Import"): root node name. scale (float, ge=0.001, default 1.0): uniform scale. position_x/y/z (float, default 0.0): world position. Returns: success (bool), data (dict with imported as bool, name, total_nodes as int, mesh_count as int). Examples: `await godot_import_glb(path="C:/exchange/robot.glb", name="Robot", scale=0.01)`, `await godot_import_glb(path="C:/models/scene.gltf")`.

**godot_import_obj** (annotations=MUTATING, version=0.1.0): Import a Wavefront OBJ file with optional MTL material file using Godot's ResourceLoader. Supports the freecad-mcp CFD streamline export to godot-mcp pipeline. Parameters: path (str, required): absolute path. name (str, default "OBJ_Import"): node name. scale (float, ge=0.001, default 1.0). position_x/y/z (float, default 0.0). Returns: success (bool), data (dict with imported as bool, name). Example: `await godot_import_obj(path="C:/exchange/streamlines.obj", name="CFD_Streamlines")`.

### Animation

**godot_play_animation** (annotations=MUTATING, version=0.1.0): Play or list animation clips on an AnimationPlayer node. Typically used after importing a GLB file that includes baked animation tracks (common pipeline: Blender VMD bake to GLB export, then godot_import_glb, then godot_play_animation). Parameters: root_name (str, default ""): search root node name; empty searches the entire scene. animation (str, default ""): animation clip name to play; empty lists available clips. loop (bool, default True): loop the animation. speed_scale (float, 0.01-10.0, default 1.0): playback speed multiplier. Returns when playing: success (bool), data with playing bool, animation str, available_animations list. When listing: success (bool), data with listed bool, animations list. Examples: `await godot_play_animation(root_name="Dancer", animation="")`, `await godot_play_animation(root_name="Dancer", animation="dance_01", loop=True)`.

### GPU Particle Systems (CFD Visualization)

**godot_load_velocity_field** (annotations=MUTATING, version=0.1.0): Load a CSV velocity field dataset into the Godot scene as node metadata. CSV must have columns: x, y, z, vx, vy, vz representing 3D positions and vector components. Used for CFD visualization pipelines. Parameters: csv_path (str, required): absolute path to CSV file. name (str, default "VelocityField"): data node name. Returns: success (bool), data (dict with loaded bool, name, point_count int, bbox with min/max x/y/z floats). Example: `await godot_load_velocity_field(csv_path="C:/data/velocity_field.csv", name="FlowData")`.

**godot_spawn_particles** (annotations=MUTATING, version=0.1.0): Create a GPUParticles3D system in the Godot scene with configurable emission volume, particle count, sphere draw pass, and color. Parameters: count (int, 1-1000000, default 1000): number of GPU particles. name (str, default "StreamlineParticles"): node name. color (str, default "#00aaff"): hex color for the particle material. spread_x/y/z (float, default 5.0): emission box extents. Returns: success, data with spawned bool, name, count int, particle_system str. Example: `await godot_spawn_particles(count=5000, name="CFD_Flow", spread_x=10, spread_y=10, spread_z=10)`.

**godot_animate_streamlines** (annotations=MUTATING, version=0.1.0): Configure a GPUParticles3D system to follow a previously loaded velocity field. Adjusts emission box to match the velocity field bounding box, sets initial velocity range from field vectors, and enables particle emission. Parameters: velocity_field (str, default "VelocityField"): name of the velocity field data node. particle_system (str, default "StreamlineParticles"): GPUParticles3D node name. speed (float, default 1.0): animation speed multiplier. Returns: success, data with animated bool, particle_system str, velocity_field str, speed_multiplier float, point_count int. Example: `await godot_animate_streamlines(velocity_field="FlowData", particle_system="CFD_Flow", speed=2.0)`.

### Export

**godot_export_web** (annotations=MUTATING, version=0.1.0): Export the current Godot scene to HTML5/WebAssembly. Attempts in-editor export via the GDScript bridge first. If the bridge reports templates unavailable or is disconnected, falls back to running godot --headless --export-release Web via subprocess. Parameters: output_path (str, default "user://export/web/index.html"): output path (absolute or res://). resolution_x/y (int, default 1280x720): viewport size. Returns: success, data with exported bool, message str, output_path str. Example: `await godot_export_web(output_path="C:/builds/godot-web/index.html", resolution_x=1920, resolution_y=1080)`.

### Fleet Exchange & World Labs

The fleet exchange integration enables cross-repo asset sharing. Other MCP servers (freecad-mcp, qcad-mcp, blender-mcp) place GLB/STL/OBJ files in a shared directory that godot-mcp can discover and import.

**fleet_exchange_status** (annotations=READ_ONLY, version=0.2.1): List available assets in the fleet exchange depot and report pipeline readiness. No parameters. Returns exchange_path, file count, and recent files.

**fleet_import_from_exchange** (annotations=MUTATING, version=0.2.1): Copy a mesh from the fleet exchange directory and import it into Godot via the bridge. Parameters: path (str, required): relative path under FLEET_EXCHANGE_ROOT. name (str, default "FleetImport"): node name. scale (float, ge=0.001, default 1.0).

**fleet_worldlabs_get_world** (annotations=READ_ONLY, version=0.2.1): Fetch World Labs world metadata from the worldlabs-mcp bridge API. Returns asset URLs for mesh collider, splat point cloud, panorama image, and thumbnail. Parameters: world_id (str, required): Marble world id (alphanumeric). Returns: success, world_id, world metadata, assets dict, spark_viewer_url.

**fleet_worldlabs_stage_mesh** (annotations=MUTATING, version=0.2.1): Download a World Labs Chisel collision GLB file to the fleet exchange directory without importing into Godot. Parameters: world_id (str, required). Returns: success, download path, file size.

**fleet_worldlabs_stage_splat** (annotations=MUTATING, version=0.2.1): Download a World Labs SPZ splat file to the exchange directory for Spark or Unity consumption. Parameters: world_id (str, required), resolution ("100k"|"500k"|"full", default "500k"). Returns: success, download path.

**fleet_worldlabs_import_mesh** (annotations=MUTATING, version=0.2.1): Download a World Labs collider GLB and import it directly into the Godot scene. Parameters: world_id (str, required), node_name (str, optional), scale (float, default 1.0). Returns: success, import details.

### Itch.io Publishing (Butler CLI)

The itch.io publishing pipeline uses Butler CLI for uploading builds. All six tools form a complete publish workflow from export to deployment.

**itch_status** (annotations=READ_ONLY, version=0.2.1): Check the local Butler CLI installation, whether BUTLER_API_KEY is set, default itch target slug, and last ship record. No parameters. Returns butler detection, auth status, defaults, last_ship.

**godot_export_release** (annotations=MUTATING, version=0.2.1): Export a Godot sample or custom project to Web or Windows using godot --headless --export-release. Parameters: target ("web"|"windows", default "web"), game (str, default "dodge"), project_path (str, optional), output_path (str, optional). Returns export details including output file path and upload directory.

**itch_push_preview** (annotations=READ_ONLY, version=0.2.1): Run Butler push-preview to show NEW/MODIFIED/DELETED file differences before uploading. Parameters: upload_dir (str, required), itch_target (str, optional), channel (str, optional). Returns Butler diff output.

**itch_push** (annotations=MUTATING, version=0.2.1): Upload a build directory to itch.io via Butler push. Parameters: upload_dir (str, required), itch_target (str, optional), channel (str, optional), hidden (bool, default False). Returns Butler result with stdout/stderr.

**itch_latest_version** (annotations=READ_ONLY, version=0.2.1): Query api.itch.io/wharf/latest for the most recent build version on a specific channel. Parameters: itch_target (str, optional), channel (str, optional). Returns URL and raw API response.

**ship_to_itch** (annotations=MUTATING, version=0.2.1): Complete pipeline that exports a Godot project, optionally runs Butler push-preview, and optionally pushes to itch.io. Parameters: target, game, project_path, itch_target, channel, preview (bool, default True), push (bool, default True), hidden (bool, default False). Returns export, preview, and push results.

### Steam Publishing (via steam-mcp)

Steam publishing requires a running steam-mcp server on port 11020.

**steam_status** (annotations=READ_ONLY, version=0.3.0): Check connectivity to steam-mcp, list configured Steam App IDs and Depot IDs, and verify steamcmd readiness.

**steam_checklist** (annotations=READ_ONLY, version=0.3.0): Return the Steam Direct release checklist from steam-mcp for validating content readiness. Parameters: content_root (str, default "").

**steam_monetization_guide** (annotations=READ_ONLY, version=0.3.0): Return pricing setup guidance and revenue sharing information (manual Steamworks configuration steps).

**steam_stage_build** (annotations=MUTATING, version=0.3.0): Export a Windows build and stage the files to the fleet exchange directory for Steam depot upload. Parameters: game (str, default "dodge"), project_path (str, optional), app_id (int, optional).

**ship_to_steam_prerelease** (annotations=MUTATING, version=0.3.0): Upload a staged build to the Steam beta/prerelease branch via steam-mcp. Parameters: content_root (str, default ""), dry_run (bool, default True).

**ship_to_steam_release** (annotations=MUTATING, version=0.3.0): Upload a staged build to the Steam default (live) branch. Parameters: content_root (str, default ""), dry_run (bool, default True).

**ship_to_steam** (annotations=MUTATING, version=0.3.0): Complete Steam pipeline: export Windows build, stage to exchange, generate VDF, and upload via steam-mcp. Parameters: game, project_path, phase ("prerelease"|"release"), dry_run (bool, default True).

### Game Builder AI Pipeline

The game builder pipeline uses LLM sampling via ctx.sample() to design, generate, compose, and ship complete games from natural language descriptions.

**design_game** (annotations=READ_ONLY, version=0.3.0): Design a complete game from a natural language concept using AI. Returns a structured GamePlan with title, genre, description, worlds list, scenes list, scripts list, and asset references. Uses ctx.sample() for the LLM call. Parameters: game_concept (str, required): a natural language description. Returns: success, plan dict, summary string. Example: `await design_game(game_concept="A 2D platformer where the player jumps between floating islands")`.

**generate_game_worlds** (annotations=MUTATING, version=0.3.0): Generate 3D worlds using the World Labs bridge for each world in the game plan. Downloads collider GLB meshes to the fleet exchange. Parameters: game_plan_json (str, required), worldlabs_url (str, default "http://127.0.0.1:10865").

**compose_game_scene** (annotations=MUTATING, version=0.3.0): Assemble the Godot scene by importing staged World Labs GLB meshes via the fleet bridge. Creates nodes, arranges them by world position, and sets up the scene hierarchy per the game plan. Parameters: game_plan_json (str, required), worlds_result_json (str, optional).

**generate_game_logic** (annotations=MUTATING, version=0.3.0): Generate GDScript files for game mechanics using LLM sampling. Optionally persists generated .gd files into a Godot project directory. Parameters: game_plan_json (str, required), game_project_path (str, default ""). Returns generated scripts and project sync results.

**export_and_ship** (annotations=MUTATING, version=0.3.0): Export the completed Godot project and optionally ship to itch.io. Parameters: game_plan_json (str, required), game_project_path (str, required), itch_target (str, default ""), channel (str, default "html").

**build_game** (annotations=MUTATING, version=0.3.0): End-to-end game build pipeline combining design, world generation, scene composition, logic generation, and optional export/ship into a single tool call. Parameters: game_concept (str, required), worldlabs_url (str), game_project_path (str), ship (bool, default False), itch_target (str).

### Artifact Depot

The artifact depot is a local metadata store for Godot game assets. It persists artifact records including name, type, description, author, and tags, enabling cross-session asset management.

**artifact_list** (annotations=READ_ONLY, version=0.1.0): List artifacts with optional type filter and pagination. Parameters: artifact_type (str, optional): "scene", "mesh", "material", "particle_system", "script", "project", "prefab". skip (int, default 0). limit (int, 1-100, default 20).

**artifact_search** (annotations=READ_ONLY, version=0.1.0): Full-text search artifacts by name, description, and tags. Parameters: query (str, required), artifact_type (str, optional).

**artifact_get** (annotations=READ_ONLY, version=0.1.0): Get full details for a single artifact by its depot ID. Parameters: artifact_id (str, required).

**artifact_register** (annotations=MUTATING, version=0.1.0): Register a new artifact in the depot (metadata only, no file upload). Parameters: name (str, required), artifact_type (str, required), description (str, default ""), author (str, default ""), tags (list[str], default []).

**artifact_delete** (annotations=MUTATING, version=0.1.0): Delete an artifact from the depot by ID. Parameters: artifact_id (str, required).

### Prefabs

Prefabs are reusable tool sequences that can be applied with a single call.

**prefab_list** (annotations=READ_ONLY, version=0.1.0): List available prefab templates with optional category filter. Parameters: category (str, optional): "lighting", "camera", "particles", "materials".

**prefab_apply** (annotations=MUTATING, version=0.1.0): Apply a prefab template by executing its tool sequence. Supports parameter overrides. Parameters: prefab_id (str, required), params (dict, default {}).

### LLM Sampling & Prompts

**prompt_list** (annotations=READ_ONLY, version=0.1.0): List available prompt templates.

**prompt_execute** (annotations=MUTATING, version=0.1.0): Execute a prompt template with parameter substitution and LLM sampling. Parameters: prompt_id (str, required), params (dict, default {}).

**ai_describe_artifact** (annotations=READ_ONLY, version=0.1.0): Generate an AI-powered description for an artifact using LLM sampling. Parameters: name, artifact_type, features (str, default "").

**ai_generate_gdscript** (annotations=MUTATING, version=0.1.0): Generate GDScript code from a natural language specification. Parameters: specification (str, required). Uses ctx.sample().

### Workflows

Agentic workflows are multi-step processes that chain multiple tools together.

**workflow_list** (annotations=READ_ONLY, version=0.1.0): List available built-in workflows with descriptions and step counts.

**workflow_run** (annotations=MUTATING, version=0.1.0): Execute a predefined multi-step workflow. Available workflows: scene_setup (creates camera, light, and material), particle_cfd (full CFD visualization pipeline), ship_web_itch (export + push to itch.io), ship_windows_steam_beta/release (Windows build + Steam upload).

### Cross-Server Bridge

**bridge_connect** (annotations=MUTATING, version=0.1.0): Connect to another fleet MCP server via its REST API endpoint.

**bridge_call_tool** (annotations=READ_ONLY, version=0.1.0): Call a named tool on a connected remote MCP server. Parameters: server_url (str), tool_name (str), arguments (dict).

### MCPB Bundle Management

**mcpb_build** (annotations=MUTATING, version=0.1.0): Create a portable .mcpb bundle file from a tool sequence.

**mcpb_inspect** (annotations=READ_ONLY, version=0.1.0): Read manifest from an existing .mcpb file.

## Resources

- skill://{skill_name}/SKILL.md: Access skill documentation markdown by name.
- skill://list: List all available skill names as JSON.

## Configuration

Complete environment variable reference:
- GODOT_PATH: Absolute path to godot.exe. Overrides PATH-based discovery. Example: "C:/Program Files/Godot/godot.exe".
- GODOT_HOST: Godot bridge TCP host (default: 127.0.0.1).
- GODOT_PORT: Godot bridge TCP port (default: 9080).
- MCP_PORT: Server HTTP port (default: 10993).
- MCP_HOST: Server bind address (default: 0.0.0.0).
- MCP_BRIDGE_URLS: Comma-separated list of external MCP server URLs to proxy via create_proxy.
- BUTLER_API_KEY: itch.io API key for Butler CLI publishing commands.
- BUTLER_PATH: Explicit path to butler.exe (bypasses PATH/shutil discovery).
- ITCH_TARGET: Default itch.io user/game slug for publishing.
- STEAM_MCP_URL: steam-mcp server base URL (default: http://127.0.0.1:11020).
- WORLDLABS_BRIDGE_URL: World Labs bridge API (default: http://127.0.0.1:10865).
- WORLDLABS_WEB_URL: World Labs web viewer (default: http://127.0.0.1:10864).
- FLEET_EXCHANGE_ROOT: Cross-repo fleet asset exchange directory.
- GODOT_TAURI: Set to "1" when running inside the Tauri desktop wrapper to enable Tauri CORS origins.

## REST API Endpoints

- GET /api/v1/status: Combined server, Godot engine, itch.io, Steam, and fleet status.
- POST /api/v1/control/tool: Execute any registered MCP tool by name with arguments.
- GET /api/v1/logs/stream: SSE stream of timestamped activity log entries.
- WebSocket /mobile/v1: iOS mobile gateway for Spatial Vibe, State Surveiller, and Pocket Architect apps.
- GET /mobile/v1/help: Machine-readable mobile gateway protocol reference.
- POST /mobile/v1/command: REST fallback for stateless mobile commands.

## Data Sources

- Godot Engine 4.x: TCP bridge on port 9080 for scene manipulation and queries.
- SQLite artifact depot: Local database at data/artifacts/ for artifact metadata persistence.
- Fleet exchange: Configurable shared directory for cross-repo GLB/OBJ/STL asset interchange.
- World Labs bridge: REST API for generative 3D world mesh, splat, and panorama downloads.
- steam-mcp: REST API server for Steamworks publishing operations.
- Itch.io Butler CLI: Local butler.exe for itch.io build uploads and version queries.
