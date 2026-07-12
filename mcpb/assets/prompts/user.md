# godot-mcp — User Guide and Tutorials

## Quick Start

### Prerequisites
- Python 3.12 or higher with the uv package manager installed.
- Godot 4.x Engine: Download the latest stable release from godotengine.org. The .NET version is not required. The standard Godot 4 build works for both the editor and headless export mode.
- Optional but recommended: Butler CLI from itch.io for publishing Godot games to itch.io. Install from https://itchio.itch.io/butler or set the BUTLER_PATH environment variable pointing to the butler.exe location.

### Installation Steps
Open a PowerShell terminal and run the following commands:
```powershell
git clone https://github.com/sandraschi/godot-mcp.git
cd godot-mcp
uv sync
just bootstrap
```
The bootstrap command installs Godot if not already present via a download from the official GitHub releases, synchronizes all Python dependencies using uv, and installs the Vite web dashboard dependencies using npm. After bootstrap completes, the godot-mcp server environment is fully ready.

### Basic Startup
Two components must be running for full functionality: the Godot engine with the MCP bridge addon, and the godot-mcp MCP server.

1. Launch the Godot editor with the bridge project: `just godot-editor`. This opens the Godot editor window loaded with the project from the repository root. The MCP bridge addon (located at dev/mcp_bridge.gd) starts a TCP listener on port 9080 when Godot initializes.
2. In a separate terminal, start the MCP server: `just serve --mode dual --port 10993`. This starts the FastMCP server on port 10993 with SSE endpoint at /sse and the REST API on the same port.
3. Verify the connection: `just health` or navigate to http://localhost:10993/api/v1/status in a browser. A successful response shows Godot engine version, current FPS, node count, and bridge connectivity status.

### Using as an MCP Client
To use godot-mcp with Claude Desktop or Cursor, configure the MCP client to connect via stdio or HTTP/SSE:

**Stdio mode (recommended for Claude Desktop):**
```json
{
  "mcpServers": {
    "godot-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "D:/Dev/repos/godot-mcp", "run_server.py"],
      "env": { "PYTHONPATH": "D:/Dev/repos/godot-mcp/src", "PYTHONUNBUFFERED": "1" }
    }
  }
}
```

**HTTP/SSE mode (recommended for Cursor):**
```json
{
  "mcpServers": {
    "godot-mcp": {
      "type": "url",
      "url": "http://localhost:10993/sse"
    }
  }
}
```

### Configuration Reference
Set environment variables before starting the server to customize behavior:
- GODOT_PATH: Override Godot executable discovery. Set to the absolute path of godot.exe.
- GODOT_HOST and GODOT_PORT: Change the Godot bridge TCP address (default 127.0.0.1:9080). Useful if Godot runs on a different machine or the port is occupied.
- BUTLER_API_KEY: Required for itch.io publishing. Obtain from https://itch.io/user/settings/api-keys.
- ITCH_TARGET: Default itch.io user/game slug. Format is "username/game-name".
- FLEET_EXCHANGE_ROOT: Custom fleet exchange directory path for cross-repo assets.

## Tutorial 1: Importing a GLB Model from Blender

This is the most common pipeline: export a 3D model from Blender as GLB, import into Godot using godot-mcp, and verify the result.

**Detailed steps:**
1. In Blender, select your model objects and go to File, Export, glTF 2.0 (.glb/.gltf). Enable the following export settings: include selected objects only, apply modifiers, include mesh data and materials, include animation tracks only if your model has baked animations. Binary (.glb) format is preferred for smaller file size.
2. Open a PowerShell terminal and start the Godot editor: `just godot-editor`. Wait for the Godot window to appear and the bridge to initialize.
3. In a second terminal, start the MCP server: `just serve --mode dual --port 10993`. Wait for the "Uvicorn running" log message.
4. Use the MCP import tool with your model path:
   ```python
   await godot_import_glb(
       path="C:/Users/YourName/Documents/blender-exports/robot.glb",
       name="Robot",
       scale=1.0
   )
   ```
5. Verify the import by reading the scene tree:
   ```python
   scene = await godot_read_scene_tree()
   ```
   The response shows the "Robot" root node with child mesh nodes.

**Expected result:** The GLB mesh appears as a node in the Godot editor Scene panel with its original hierarchy, materials, and mesh data preserved.

## Tutorial 2: Setting Up a Complete Scene with Camera and Lighting

Build a viewable 3D scene in one workflow after importing a model.

**Detailed steps:**
1. First, import a 3D model as shown in Tutorial 1.
2. Create a Camera3D with orbit controls positioned to frame your model:
   ```python
   await godot_create_camera(
       name="MainCamera",
       position_y=5,
       position_z=10,
       fov=75
   )
   ```
3. Add a directional light to simulate sun illumination:
   ```python
   await godot_add_light(
       light_type="directional",
       name="Sun",
       intensity=2.0
   )
   ```
4. Add an ambient light for fill illumination (prevents completely black shadows):
   ```python
   await godot_add_light(
       light_type="ambient",
       intensity=0.3
   )
   ```
5. Optionally add a warm fill light from the opposite side:
   ```python
   await godot_add_light(
       light_type="omni",
       name="FillLight",
       intensity=0.8,
       position_x=-5,
       position_y=3,
       position_z=-5
   )
   ```
6. Run the scene in Godot by clicking the Play Scene button or pressing F6. The viewport shows your model illuminated by the three light sources, viewed through the orbit-controlled camera. You can click and drag to orbit around the model, scroll to zoom in and out.

**Tips:** For outdoor scenes, use a directional light with high intensity (2.0-3.0) and a low-angle ambient. For indoor scenes, use multiple omni lights positioned where lamps or windows would be.

## Tutorial 3: Applying PBR Materials to Individual Nodes

Change the visual appearance of any MeshInstance3D node in the scene using StandardMaterial3D with PBR parameters.

**Detailed steps:**
1. After importing a mesh, identify the target node name. Use godot_read_scene_tree to see all node names if unsure.
2. Apply a blue metallic-looking material:
   ```python
   await godot_set_material(
       node="Robot",
       color="#4488ff",
       roughness=0.2
   )
   ```
3. Apply a rough green material to a ground plane:
   ```python
   await godot_set_material(
       node="Ground",
       color="#556633",
       roughness=0.9
   )
   ```
4. Apply a mirror-smooth material for a reflective surface:
   ```python
   await godot_set_material(
       node="Floor",
       color="#222233",
       roughness=0.05
   )
   ```
5. The material is created as a StandardMaterial3D resource and assigned to the node's material_override property. You can see the change immediately in the Godot editor viewport.

**Reference:** Roughness values: 0.0-0.1 = mirror/specular (metal, polished surfaces), 0.2-0.4 = semi-gloss (plastic, painted surfaces), 0.5-0.7 = satin (wood, stone), 0.8-1.0 = matte (fabric, rough concrete).

## Tutorial 4: CFD Visualization with Velocity Fields

Visualize computational fluid dynamics data exported from freecad-mcp, qcad-mcp, or other CFD simulation tools.

**Detailed steps:**
1. Prepare your CFD data as a CSV file with exactly 6 columns: x (position), y (position), z (position), vx (velocity x component), vy (velocity y component), vz (velocity z component). No header row is required; the bridge parser reads all 6 columns as floats.
2. Load the velocity field into the Godot scene:
   ```python
   await godot_load_velocity_field(
       csv_path="C:/data/cfd/flow_around_cylinder.csv",
       name="AirflowData"
   )
   ```
   The tool returns the point count and bounding box extents, confirming the data was parsed.
3. Create a GPU particle system within the velocity field bounding box:
   ```python
   await godot_spawn_particles(
       count=10000,
       name="FlowLines",
       color="#00aaff",
       spread_x=12,
       spread_y=6,
       spread_z=12
   )
   ```
4. Animate the particles to follow the velocity field:
   ```python
   await godot_animate_streamlines(
       velocity_field="AirflowData",
       particle_system="FlowLines",
       speed=1.5
   )
   ```
5. The particles now flow along the velocity vectors. You can adjust the speed parameter to slow down or speed up the visualization. For scientific visualization, also set up a camera and lighting to capture the result:
   ```python
   await godot_create_camera(name="VisCam", position_x=15, position_y=10, position_z=15, look_at_x=0, look_at_y=0, look_at_z=0)
   await godot_add_light(light_type="directional", intensity=2.0)
   ```

## Tutorial 5: Animation Playback on Imported Characters

Play skeletal or transform animations on GLB models that have baked animation tracks.

**Detailed steps:**
1. Import a GLB file that contains animation tracks (exported from Blender with animation enabled):
   ```python
   await godot_import_glb(path="C:/models/dancing_character.glb", name="Dancer", scale=0.01)
   ```
2. List the available animation clips on the imported model:
   ```python
   await godot_play_animation(root_name="Dancer", animation="")
   ```
   Returns a list like ["idle", "walk", "run", "dance_01", "wave"].
3. Play a specific animation:
   ```python
   await godot_play_animation(
       root_name="Dancer",
       animation="dance_01",
       loop=True,
       speed_scale=1.0
   )
   ```
4. Speed up playback for a fast-paced effect:
   ```python
   await godot_play_animation(
       root_name="Dancer",
       animation="run",
       loop=True,
       speed_scale=2.0
   )
   ```

## Tutorial 6: Exploring and Modifying the Scene Tree

Understand the Godot scene hierarchy and make project-wide configuration changes.

**Detailed steps:**
1. Read the entire scene tree to inspect the current structure:
   ```python
   tree = await godot_read_scene_tree()
   node_count = tree["data"]["node_count"]
   root = tree["data"]["scene_tree"]["name"]
   ```
2. Change the project display name:
   ```python
   await godot_set_config(
       section="application",
       key="config/name",
       value="My Godot Project"
   )
   ```
3. Set the default window size for desktop export:
   ```python
   await godot_set_config(section="display", key="window/size/width", value="1920")
   await godot_set_config(section="display", key="window/size/height", value="1080")
   ```
4. Check if Godot is in headless mode:
   ```python
   await godot_headless_verify()
   ```

## Tutorial 7: Exporting to HTML5 for Web Publishing

Publish your Godot scene as a self-contained WebAssembly web application.

**Detailed steps:**
1. Ensure export templates are installed: `just install-export-templates 4.4`. This downloads the Godot export templates for version 4.4 from the official repository.
2. Configure export presets if needed by ensuring export_presets.cfg exists in your project. The justfile handles this automatically for sample projects.
3. Export to HTML5:
   ```python
   await godot_export_web(
       output_path="C:/builds/my-game/web/index.html",
       resolution_x=1280,
       resolution_y=720
   )
   ```
4. The export produces an index.html, a WebAssembly .wasm file, and supporting JavaScript files. Upload the entire output directory to any static web host (GitHub Pages, Netlify, itch.io).

## Tutorial 8: Full Publishing Pipeline to itch.io

Export a Godot game project and upload it to itch.io via the Butler CLI in a single workflow.

**Detailed steps:**
1. Install Butler: download from https://itchio.itch.io/butler and ensure it is in your PATH. Alternatively, install via the just bootstrap command which offers to install it.
2. Set your itch.io API key as an environment variable. Obtain the key from https://itch.io/user/settings/api-keys:
   ```powershell
   $env:BUTLER_API_KEY = "your_itchio_api_key_here"
   ```
3. Set your default itch target (your user name and game slug):
   ```powershell
   $env:ITCH_TARGET = "yourusername/your-game"
   ```
4. Verify Butler is detected:
   ```python
   status = await itch_status()
   ```
5. Export and push to itch.io in one call:
   ```python
   result = await ship_to_itch(
       target="web",
       game="dodge",
       itch_target="yourusername/your-game",
       channel="html",
       preview=True,
       push=True
   )
   ```
6. The tool runs the Godot headless export first, then executes Butler push-preview to show what files will change, and finally runs Butler push to upload the build. Visit the itch.io game page to verify the uploaded build.

## Tutorial 9: Steam Publishing via steam-mcp

Deploy your Godot game to the Steam platform using the steam-mcp integration server.

**Detailed steps:**
1. Ensure steam-mcp is running on port 11020. If not, start it: `just serve` from the steam-mcp repository.
2. Verify steam-mcp connectivity from godot-mcp:
   ```python
   status = await steam_status()
   ```
3. Stage a Windows build for Steam depot upload:
   ```python
   await steam_stage_build(game="dodge", app_id=480)
   ```
4. Upload to the beta branch (always dry run first):
   ```python
   await ship_to_steam_prerelease(dry_run=True)
   ```
5. Review the generated VDF and command output. If correct, perform a live upload:
   ```python
   await ship_to_steam_prerelease(dry_run=False)
   ```
6. For a full release to the default branch:
   ```python
   await ship_to_steam_release(dry_run=True)
   await ship_to_steam_release(dry_run=False)
   ```

## Tutorial 10: AI-Powered Game Building from Natural Language

Generate a complete Godot game from a text description using the Game Builder pipeline with LLM sampling and World Labs integration.

**Detailed steps:**
1. Design the game concept:
   ```python
   result = await design_game(
       game_concept="A 3D exploration game where the player discovers ancient ruins on floating islands with puzzles and hidden treasures"
   )
   plan = result["plan"]
   ```
   The tool returns a structured GamePlan with title, genre, description, worlds, scenes, scripts, and asset references.
2. Generate 3D world geometry via the World Labs bridge:
   ```python
   worlds = await generate_game_worlds(
       game_plan_json=json.dumps(plan)
   )
   ```
3. Compose the Godot scene by importing the generated meshes:
   ```python
   scene = await compose_game_scene(
       game_plan_json=json.dumps(plan),
       worlds_result_json=json.dumps(worlds)
   )
   ```
4. Generate GDScript game logic:
   ```python
   await generate_game_logic(
       game_plan_json=json.dumps(plan)
   )
   ```
5. Build, export, and ship in one command:
   ```python
   await build_game(
       game_concept="A 3D exploration game with ancient ruins on floating islands",
       ship=True,
       itch_target="yourusername/ruins-explorer"
   )
   ```

## Tutorial 11: Using the Artifact Depot for Asset Management

Organize and search your Godot assets using the local artifact depot.

**Detailed steps:**
1. Register a scene artifact with descriptive metadata:
   ```python
   await artifact_register(
       name="Ancient Ruins Scene",
       artifact_type="scene",
       description="A large outdoor scene with ruined temple structures",
       author="DevTeam",
       tags=["ruins", "outdoor", "temple", "exploration"]
   )
   ```
2. Search for artifacts by keyword:
   ```python
   found = await artifact_search(query="ruins")
   ```
3. List all artifacts of a specific type:
   ```python
   all_scenes = await artifact_list(artifact_type="scene", limit=50)
   ```
4. Get full details for a specific artifact:
   ```python
   artifact = await artifact_get(artifact_id="abc123")
   ```
5. Delete artifacts when no longer needed:
   ```python
   await artifact_delete(artifact_id="abc123")
   ```

## Tutorial 12: Using Prefab Templates

Apply pre-built scene component configurations with parameter overrides.

**Detailed steps:**
1. List all available prefabs to see what templates exist:
   ```python
   all_prefabs = await prefab_list()
   ```
2. Filter by category to find lighting templates:
   ```python
   lighting = await prefab_list(category="lighting")
   ```
3. Apply a prefab, overriding specific parameters:
   ```python
   await prefab_apply(
       prefab_id="standard_lighting",
       params={"intensity": 2.0, "color": "#ffdd88"}
   )
   ```

## Tutorial 13: Workflows for Multi-Step Operations

Run pre-defined multi-step workflows that chain multiple tools together for common tasks.

**Detailed steps:**
1. List available workflows:
   ```python
   await workflow_list()
   ```
2. Run the scene setup workflow (creates camera, lighting, and default material):
   ```python
   await workflow_run(workflow_name="scene_setup")
   ```
3. Run the CFD particle workflow with a velocity field:
   ```python
   await workflow_run(
       workflow_name="particle_cfd",
       csv_path="C:/data/velocity_field.csv"
   )
   ```
4. Run the itch.io ship workflow:
   ```python
   await workflow_run(
       workflow_name="ship_web_itch",
       game="dodge",
       itch_target="yourusername/your-game"
   )
   ```

## Tutorial 14: Cross-Server MCP Bridge

Connect godot-mcp to other fleet MCP servers for cross-repo tool access and asset exchange.

**Detailed steps:**
1. Discover which fleet servers are available. Common fleet MCP servers include qcad-mcp on port 10966, freecad-mcp on port 10944, avatar-mcp on port 10793, and blender-mcp on port 10849.
2. Connect to a remote MCP server such as qcad-mcp for CAD model import:
   ```python
   await bridge_connect(server_url="http://localhost:10966")
   ```
3. Call a tool on the connected server to export geometry data:
   ```python
   cad_result = await bridge_call_tool(
       server_url="http://localhost:10966",
       tool_name="qcad_export_stl",
       arguments={"path": "C:/exchange/cad_model.stl"}
   )
   ```
4. Switch back to godot-mcp to import the resulting file into the Godot scene:
   ```python
   await godot_import_stl(
       path="C:/exchange/cad_model.stl",
       name="CAD_Part",
       scale=0.01
   )
   ```
5. Connect to blender-mcp for high-poly model exchange:
   ```python
   await bridge_connect(server_url="http://localhost:10849")
   ```
6. Use the bridge to generate a model and export it as GLB, then import into Godot:
   ```python
   blend_result = await bridge_call_tool(
       server_url="http://localhost:10849",
       tool_name="blender_export_glb",
       arguments={"output_path": "C:/exchange/sculpt.glb"}
   )
   await godot_import_glb(path="C:/exchange/sculpt.glb", name="Sculpture")
   ```

## API Reference

### GET /api/v1/status
Returns a comprehensive status object with these keys:
- ok: boolean indicating server health
- service: "godot-mcp"
- version: server version string
- godot: object with available (bool), path (str), host (str), port (int), ws_connected (bool)
- itch: object with butler status, auth status, defaults, last_ship
- steam: object with steam_mcp_available (bool), app_ids (list), error (optional)
- fleet: object with exchange_path (str), files (list), pipeline_status

### POST /api/v1/control/tool
Request body format:
```json
{
  "tool": "godot_status",
  "arguments": {}
}
```
Response format:
```json
{
  "success": true,
  "message": "Tool executed",
  "tool": "godot_status",
  "data": {"godot_version": "4.4", "fps": 60, "node_count": 42},
  "arguments": {}
}
```
On error, returns success: false with an error message and recovery hints.

### GET /api/v1/logs/stream
Server-Sent Events endpoint. Each event line has the format:
```
data: 2026-06-21T12:00:00 [INFO] tool_call: godot_status (ok)
```
Consume with any SSE client or EventSource in the browser.

### WebSocket /mobile/v1
iOS mobile gateway supporting three app protocols:
- spatial-vibe: ARKit spatial lens for Godot scene manipulation
- state-surveiller: Multi-agent test monitoring and hot-fix dashboard
- pocket-architect: Prompt-driven generative asset pipeline

### GET /mobile/v1/help
Returns full protocol reference as machine-readable JSON documenting all message types, intent types, channel names, and payload schemas.

### POST /mobile/v1/command
REST fallback for mobile commands. Accepts a MobileCommand envelope and returns a MobileResponse.

## Troubleshooting

### Godot Bridge Connection Issues
**Issue:** godot_status returns bridge_connected: false.
**Solutions:**
- Verify the Godot editor is running: `just godot-editor`. The editor must have the MCP bridge addon loaded.
- Check firewall rules: ensure port 9080 (TCP) is not blocked.
- Verify GODOT_HOST and GODOT_PORT if using custom settings.
- Check the Godot Output panel for bridge errors (look for "MCP bridge" messages).
- Restart the Godot editor completely and try again.

### Export Failures
**Issue:** godot_export_web or godot_export_release fails.
**Solutions:**
- Install export templates: `just install-export-templates 4.4`
- Verify export_presets.cfg exists in the project directory. The templates/ directory contains a reference preset.
- For HTML5 export, ensure the Godot version matches the export template version.
- Check disk space in the output directory.
- For Windows export, install the appropriate Windows export template.

### Butler Not Found
**Issue:** itch_status shows butler.found: false.
**Solutions:**
- Download Butler from https://itchio.itch.io/butler and place it in your PATH.
- Set BUTLER_PATH to the absolute path of butler.exe.
- Verify the download is the Windows executable (butler.exe) and is not blocked by antivirus.

### Import Failures
**Issue:** godot_import_glb or godot_import_stl returns success: false.
**Solutions:**
- Verify the file exists at the specified path.
- Check that the file is a valid binary STL or GLB format.
- Ensure Godot has enough memory for large meshes (reduce mesh complexity or increase Godot limits).
- Verify the Godot bridge is connected before importing.

## FAQ

**Q: Can I use godot-mcp without Godot installed on my machine?**
A: Some tools work without Godot: itch_status, steam_status, fleet_exchange_status, artifact_*, fleet_worldlabs_get_world, fleet_worldlabs_stage_mesh. However, all godot_* tools (scene manipulation, import, export) require a running Godot engine connected via the TCP bridge.

**Q: What 3D file formats are supported for import?**
A: Three formats are supported: GLB/GLTF (glTF 2.0 binary and text), STL (binary format only), and OBJ (Wavefront with optional MTL material file). Each uses Godot's native import pipeline for that format.

**Q: Can this work with Godot 3.x?**
A: No. The WebSocket bridge and all GDScript commands are written for Godot 4.x APIs. Godot 3.x uses a different scene tree API and rendering architecture that is not compatible.

**Q: Is there a web dashboard?**
A: Yes. A Vite React web dashboard runs on port 10992. Start it with `just web` or `npm run dev` from the webapp/ directory. The dashboard shows live status, active tools, connection health, and AI chat integration.

**Q: What ports does godot-mcp use?**
A: Backend REST API and MCP SSE on port 10993, Vite web dashboard on port 10992, Godot TCP bridge on port 9080. All ports are configurable via environment variables.

**Q: Can I run this headlessly for automated builds?**
A: Yes. Use `just godot-headless` to start Godot in headless mode with the bridge project, then `just serve` to start the MCP server. This enables automated export pipelines and CI/CD workflows without a GPU or display.

**Q: How do I set up the Godot MCP bridge addon?**
A: The bridge GDScript is already included in the repository at dev/mcp_bridge.gd. When you open this repository as a Godot project (`just godot-editor`), the bridge script starts automatically and listens on port 9080 for incoming MCP server connections.

**Q: What is the fleet exchange and how do I use it?**
A: The fleet exchange is a shared directory (default D:\Dev\repos\_exchange) used by multiple MCP servers for GLB/OBJ/STL asset interchange. Tools like fleet_import_from_exchange import meshes from this directory, while tools from other servers (freecad-mcp, qcad-mcp) export meshes into it.

**Q: Can I publish to platforms other than itch.io and Steam?**
A: The godot_export_web tool exports any Godot scene to HTML5/WebAssembly, which can be hosted on any web platform (GitHub Pages, Netlify, Vercel) or uploaded as a downloadable file on any game distribution platform.

**Q: How many MCP tools does godot-mcp register?**
A: Over 55 tools across scene management, asset import, animation, particles, export, fleet exchange, World Labs, itch.io, Steam, game builder, artifact depot, prefabs, prompts, AI sampling, workflows, MCPB, and cross-server bridge modules.

**Q: Can I create my own prefabs?**
A: Currently prefabs are defined in the catalog source code. Custom prefabs can be added by extending the catalogs found in src/godot_mcp/prefabs/catalog.py with new entries including the tool sequence and parameter schema.

**Q: How does the LLM sampling work?**
A: Tools like ai_generate_gdscript, ai_describe_artifact, and prompt_execute use FastMCP's ctx.sample() feature to call back to the connected LLM client. If the client does not support sampling (e.g., some stdio-based clients), the tools fall back to a local sampling URL configured via the ARXIV_MCP_SAMPLING_BASE_URL environment variable or return a descriptive error.

**Q: What happens if I call a tool when the Godot bridge is disconnected?**
A: Most godot_* tools automatically attempt to reconnect by calling bridge.connect() on the first call. If reconnection fails, the tool returns success: false with an error message including bridge connection status and recovery hints. The itchio and Steam tools do not require a Godot bridge connection.

**Q: Is there a way to run multiple godot_* operations atomically?**
A: For multi-step operations, use the workflow_run tool with a built-in workflow (scene_setup, particle_cfd, ship_web_itch) which executes a sequence of related tools in order. The MCPB build tool (mcpb_build) also creates a portable bundle of tool sequences that can be replayed.

**Q: What sample games are available for testing?**
A: Run `just demo-list` to see available sample projects. These include Heart Platformer (2D), Dodge the Creeps (tutorial game), Pong, Procedural Generation demos, SkeleRealms (3D RPG framework), and VibeCode Runner.
