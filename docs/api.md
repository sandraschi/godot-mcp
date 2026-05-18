# Godot MCP — Full API Reference

**Version**: 0.1.0 | **Ports**: TCP Bridge 9080, REST/SSE 10993

---

## 1. TCP Bridge Protocol

The Python backend communicates with the Godot engine via a TCP socket on port 9080. The GDScript `mcp_bridge.gd` Autoload runs a `TCPServer` that accepts JSON commands over a persistent connection.

### Transport Format

Messages are **newline-delimited JSON** (NDJSON). Each message is a single JSON object followed by `\n`. A single long-lived TCP connection is maintained — no HTTP framing.

### Handshake Sequence

On initial TCP connect, the Godot bridge immediately sends a handshake message:

**Bridge → Python (handshake)**:
```json
{
  "type": "handshake",
  "version": "0.1.0",
  "godot_version": {
    "major": 4,
    "minor": 6,
    "patch": 2
  },
  "ready": true
}
```

The Python server stores the connection in `_connected = True` and the Godot version for later use. No acknowledgment is required — the handshake is informational.

### Request Schema (Python → Bridge)

| Field | Type | Description |
|-------|------|-------------|
| `action` | string | Action type from the supported list |
| `params` | object | Action-specific parameters |
| `request_id` | string | Correlation ID echoed in response |

```json
{
  "action": "import_stl",
  "params": {
    "path": "C:/data/mesh.stl",
    "name": "MyMesh",
    "scale": 1.0,
    "position": [0.0, 0.0, 0.0]
  },
  "request_id": "py_42"
}
```

### Response Schema (Bridge → Python)

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Always `"response"` |
| `request_id` | string | Echoed from the request |
| `success` | boolean | Whether the operation succeeded |
| `data` | object/null | Result data on success |
| `error` | string/null | Error message on failure |

**Success**:
```json
{
  "type": "response",
  "request_id": "py_42",
  "success": true,
  "data": {
    "imported": true,
    "name": "MyMesh",
    "vertices": 45000,
    "aabb": {"size_x": 15.0, "size_y": 8.0, "size_z": 12.0}
  }
}
```

**Error**:
```json
{
  "type": "response",
  "request_id": "py_42",
  "success": false,
  "error": "File not found: C:/data/mesh.stl"
}
```

### Action Types

#### 1. `status`

Query the Godot engine for runtime state: version, scene tree node count, FPS, and bridge connectivity health.

**Params**: none

**Response data**:
```json
{
  "godot_version": "4.6.2",
  "node_count": 12,
  "root_nodes": ["Root", "MCP_Scene", "MCP_Camera"],
  "fps": 60.0,
  "bridge_connected": true
}
```

#### 2. `import_stl`

Import a binary STL mesh file into the Godot scene as a `MeshInstance3D`. The bridge reads the STL file, extracts vertex positions and normals, builds an `ArrayMesh`, and adds it to `STL_Imports` container.

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | string | (required) | Absolute path to binary STL file |
| `name` | string | `"STL_Mesh"` | Node name for the imported mesh |
| `scale` | float | `1.0` | Uniform scale factor (min 0.001) |
| `position` | [float,float,float] | `[0,0,0]` | World position [x, y, z] |

**Response data**:
```json
{
  "imported": true,
  "name": "MyMesh",
  "vertices": 45000,
  "aabb": {"size_x": 15.0, "size_y": 8.0, "size_z": 12.0}
}
```

#### 3. `load_velocity_field`

Load a CSV velocity field dataset into a `Node3D` as node metadata. Used for CFD visualization pipeline. The CSV must have 6 columns: `x, y, z, vx, vy, vz`.

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `csv_path` | string | (required) | Absolute path to CSV velocity field |
| `name` | string | `"VelocityField"` | Node name for data container |

**Response data**:
```json
{
  "loaded": true,
  "name": "FlowData",
  "point_count": 50000,
  "bbox": {
    "min_x": -10.0, "min_y": 0.0, "min_z": -5.0,
    "max_x": 10.0, "max_y": 5.0, "max_z": 5.0
  }
}
```

#### 4. `spawn_particles`

Create a `GPUParticles3D` system in the `Particle_Systems` container. Configures draw pass with a sphere mesh and sets basic emission parameters.

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `count` | int | `1000` | Particle count (1–1,000,000) |
| `name` | string | `"StreamlineParticles"` | Node name |
| `color` | string | `"#00aaff"` | Hex color for particle material |
| `spread` | [float,float,float] | `[5,5,5]` | Emission box extents [x, y, z] |

**Response data**:
```json
{
  "spawned": true,
  "name": "FlowParticles",
  "count": 10000,
  "particle_system": "GPUParticles3D"
}
```

#### 5. `animate_streamlines`

Link a particle system to a velocity field for streamline animation. Adjusts the emission box to match the velocity field bounding box and configures initial velocity range from the field vectors.

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `velocity_field` | string | `"VelocityField"` | Name of velocity data node |
| `particle_system` | string | `"StreamlineParticles"` | Name of particle system node |
| `speed` | float | `1.0` | Animation speed multiplier |

**Response data**:
```json
{
  "animated": true,
  "particle_system": "FlowParticles",
  "velocity_field": "FlowData",
  "speed_multiplier": 1.5,
  "point_count": 50000
}
```

#### 6. `create_camera`

Create a `Camera3D` in the `Cameras` container. Configures position, look-at target, and field of view. Attaches a script for orbit controls (mouse drag to rotate, scroll to zoom, Alt+drag to pan).

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | `"MCP_Camera"` | Node name |
| `position` | [float,float,float] | `[0,5,10]` | Camera world position |
| `look_at` | [float,float,float] | `[0,0,0]` | Target look-at point |
| `fov` | float | `75.0` | Field of view in degrees (1–179) |

**Response data**:
```json
{
  "created": true,
  "name": "RenderCam",
  "fov": 60.0,
  "position": {"x": 0.0, "y": 15.0, "z": 20.0}
}
```

#### 7. `add_light`

Add a dynamic light source to the `Lights` container. Supports three types: directional (sun-like), ambient (fill light), and omni (point light with positional control).

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `light_type` | string | `"directional"` | One of: `"directional"`, `"ambient"`, `"omni"` |
| `name` | string | auto-generated | Node name |
| `intensity` | float | `1.0` | Light energy multiplier (min 0.0) |
| `position` | [float,float,float] | `[5,5,5]` | Position (omni only) |

**Response data**:
```json
{
  "created": true,
  "name": "MCP_Light_directional",
  "type": "directional",
  "intensity": 2.0
}
```

#### 8. `set_material`

Assign a `StandardMaterial3D` (PBR) to an existing `MeshInstance3D`. Sets albedo color and roughness. The material uses the metallic-roughness PBR workflow.

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `node` | string | (required) | Target MeshInstance3D node name |
| `color` | string | `"#ffffff"` | Hex albedo color |
| `roughness` | float | `0.5` | PBR roughness (0 = mirror, 1 = matte) |

**Response data**:
```json
{
  "set": true,
  "node": "River_Mesh",
  "color": "#336699",
  "roughness": 0.4
}
```

#### 9. `export_web`

Export the current loaded scene as HTML5/WebAssembly. Requires Godot HTML5 export templates to be installed. Returns a message with the export result.

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `output_path` | string | `"user://export/web/index.html"` | Output path (`res://` or absolute) |

**Response data**:
```json
{
  "exported": true,
  "message": "Scene exported to C:/builds/cfd-viz/index.html",
  "requires_cli": false
}
```

#### 10. `read_scene_tree`

Recursively read the full Godot scene tree and return it as nested JSON. Each node includes its name, type, path, and children.

**Params**: none

**Response data**:
```json
{
  "scene_tree": {
    "name": "Root",
    "type": "Node",
    "path": "/root",
    "children": [
      {
        "name": "MCP_Scene",
        "type": "Node3D",
        "path": "/root/MCP_Scene",
        "children": [
          {
            "name": "River_Mesh",
            "type": "MeshInstance3D",
            "path": "/root/MCP_Scene/River_Mesh",
            "children": []
          }
        ]
      }
    ]
  },
  "node_count": 12
}
```

#### 11. `set_config`

Write a key-value pair to the Godot project's `project.godot` INI-style configuration file. Uses the Godot `ConfigFile` API internally.

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `section` | string | (required) | Config section (e.g. `"application"`, `"rendering"`) |
| `key` | string | (required) | Config key |
| `value` | string | (required) | Config value |

**Response data**:
```json
{
  "updated": true,
  "section": "rendering",
  "key": "anti_aliasing/quality/msaa_3d",
  "value": "2"
}
```

#### 12. `headless_verify`

Check whether the Godot engine is running in headless mode (`--headless` flag). Returns the current mode and the path of the verification script.

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `script` | string | `"res://dev/mcp_verify.gd"` | GDScript to verify |

**Response data**:
```json
{
  "headless": false,
  "script_path": "res://dev/mcp_verify.gd",
  "message": "Godot is running in editor mode — not headless"
}
```

#### 13. `add_node`

Create a generic node of any `Node`-derived type in the scene tree under a specified parent. Supports all engine node types (MeshInstance3D, Node3D, etc.).

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `node_type` | string | (required) | Fully qualified node type (e.g. `"MeshInstance3D"`, `"Node3D"`) |
| `name` | string | (required) | Name for the new node |
| `parent_path` | string | `"/root"` | Parent node path to attach under |

**Response data**:
```json
{
  "created": true,
  "name": "MyNode",
  "type": "Node3D",
  "path": "/root/MCP_Scene/MyNode"
}
```

#### 14. `remove_node`

Remove a node from the scene tree by name. Searches recursively using `_find_node_by_name()`.

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | (required) | Name of the node to remove |

**Response data**:
```json
{
  "removed": true,
  "name": "TemporaryNode",
  "path": "/root/MCP_Scene/TemporaryNode"
}
```

#### 15. `save_scene`

Save the current scene to a `.tscn` file. Wraps the Godot `ResourceSaver.save()` call.

**Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | string | `"res://current_scene.tscn"` | Output path for the scene file |

**Response data**:
```json
{
  "saved": true,
  "path": "res://current_scene.tscn",
  "node_count": 12
}
```

---

## 2. GodotBridge Class API

Located at `src/godot_mcp/services/godot_bridge.py`. The `GodotBridge` class is a synchronous TCP socket client that connects to the GDScript bridge.

### Constructor

```python
GodotBridge(host: str = "127.0.0.1", port: int = 9080, timeout: float = 5.0)
```

| Param | Default | Description |
|-------|---------|-------------|
| `host` | `"127.0.0.1"` | Godot bridge hostname |
| `port` | `9080` | Godot bridge TCP port |
| `timeout` | `5.0` | Socket connect/read timeout in seconds |

### Methods

#### `connect() -> bool`

Open a TCP socket to the Godot bridge. Reads the initial handshake JSON. Sets `_connected` and stores `godot_version`.

```python
bridge = GodotBridge()
if bridge.connect():
    print(f"Connected to Godot {bridge.godot_version}")
```

**Returns**: `True` on successful connect and handshake, `False` on failure (timeout, connection refused, bad handshake).

#### `disconnect() -> None`

Close the TCP socket and reset the connected state. Called automatically in the server's shutdown lifespan.

```python
bridge.disconnect()
```

#### `send(action: str, params: dict = None, request_id: str = None) -> dict`

Serialize and send a JSON command to the Godot bridge. Blocks until a response is received. Generates a sequential `request_id` if not provided (e.g. `"py_1"`, `"py_2"`).

```python
result = bridge.send("status")
# Returns: {"type": "response", "request_id": "py_1", "success": true, "data": {...}}
```

| Param | Default | Description |
|-------|---------|-------------|
| `action` | (required) | Action type string |
| `params` | `{}` | Parameters dict |
| `request_id` | auto-incremented | Correlation ID |

**Returns**: Parsed JSON response dict. Raises `ConnectionError` if not connected. Raises `TimeoutError` if no response within timeout.

#### `is_installed() -> bool`

Static method. Check whether Godot is installed and discoverable on the system. Checks `GODOT_PATH` env var, then `shutil.which("godot")`, then common install paths.

```python
if GodotBridge.is_installed():
    print("Godot found")
```

**Returns**: `True` if a `godot` executable is found.

#### `find_godot_path() -> str | None`

Static method. Return the absolute path to the Godot executable, or `None` if not found.

```python
godot_path = GodotBridge.find_godot_path()
```

**Returns**: String path or `None`.

---

## 3. REST API

The FastAPI server exposes three REST endpoints on port 10993, separate from the MCP SSE transport.

### `GET /api/v1/status`

Server health and Godot connectivity status. Returns immediately, does not require Godot to be running.

**Response**:
```json
{
  "ok": true,
  "service": "godot-mcp",
  "version": "0.1.0",
  "godot": {
    "available": true,
    "path": "C:\\Program Files\\Godot\\godot.exe",
    "host": "127.0.0.1",
    "port": 9080,
    "ws_connected": true
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ok` | bool | Server is operational |
| `service` | string | Always `"godot-mcp"` |
| `version` | string | Server version |
| `godot.available` | bool | Godot executable found on system |
| `godot.path` | string/null | Detected Godot path |
| `godot.host` | string | Bridge host |
| `godot.port` | int | Bridge port |
| `godot.ws_connected` | bool | TCP bridge currently connected |

### `POST /api/v1/control/tool`

Execute a godot-mcp tool via REST (alternative to SSE MCP transport). Accepts a tool name and arguments, dispatches to the matching MCP tool function, and returns structured results.

**Request**:
```json
{
  "tool": "godot_status",
  "arguments": {}
}
```

**Success Response** (HTTP 200):
```json
{
  "success": true,
  "message": "Tool executed",
  "tool": "godot_status",
  "data": {
    "godot_version": "4.6.2",
    "node_count": 12,
    "fps": 60.0
  },
  "arguments": {}
}
```

**Error — Unknown Tool** (HTTP 400):
```json
{
  "detail": "Unknown tool: bad_tool_name"
}
```

**Error — Tool Execution Failure** (HTTP 500):
```json
{
  "success": false,
  "error": "Bridge connection lost: connection refused at 127.0.0.1:9080",
  "tool": "godot_status",
  "arguments": {}
}
```

### `GET /api/v1/logs/stream`

Server-Sent Events (SSE) endpoint that streams server logs in real time. Uses a ring buffer of 2000 most recent entries so late-connected clients receive recent history.

**Event format**:
```
data: 2026-05-18 12:34:56,789 - godot-mcp - INFO - Godot MCP startup — engine found at C:\Program Files\Godot\godot.exe
```

**Response headers**:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

---

## 4. MCP Tools (12)

Full reference for each MCP tool is documented in [mcp-server.md](./mcp-server.md). This section provides the summary table and fast signature lookup.

| # | Tool | Access | Description |
|---|------|--------|-------------|
| 1 | `godot_status` | READ_ONLY | Engine version, FPS, node count |
| 2 | `godot_import_stl` | MUTATING | Import STL → MeshInstance3D |
| 3 | `godot_load_velocity_field` | MUTATING | CSV velocity data → node metadata |
| 4 | `godot_spawn_particles` | MUTATING | GPUParticles3D system |
| 5 | `godot_animate_streamlines` | MUTATING | Particles follow velocity field |
| 6 | `godot_create_camera` | MUTATING | Camera3D + orbit controls |
| 7 | `godot_add_light` | MUTATING | Directional/ambient/omni light |
| 8 | `godot_set_material` | MUTATING | PBR StandardMaterial3D |
| 9 | `godot_export_web` | MUTATING | HTML5/WASM build export |
| 10 | `godot_read_scene_tree` | READ_ONLY | Full scene hierarchy |
| 11 | `godot_set_config` | MUTATING | project.godot config |
| 12 | `godot_headless_verify` | READ_ONLY | Headless mode check |

All tools return the standard envelope:
```json
{
  "success": true,
  "data": { ... }
}
```

On failure:
```json
{
  "success": false,
  "error": "Description of what went wrong"
}
```

---

## 5. Error Codes and Handling

### TCP Bridge Errors

| Error | HTTP Equiv | Cause | Recovery |
|-------|-----------|-------|----------|
| `connection_refused` | 503 | Godot engine not running or bridge not loaded | Start Godot project, verify mcp_bridge.gd Autoload |
| `connection_timeout` | 504 | Bridge didn't respond within 5s timeout | Check Godot process is not hung; restart engine |
| `handshake_failed` | 502 | Bridge sent malformed JSON on connect | Update mcp_bridge.gd to match server version |
| `not_connected` | 503 | `send()` on disconnected bridge | Reconnect via `bridge.connect()` |
| `socket_error` | 500 | OS-level socket failure | Check firewall, port 9080 not in use |

### Action Execution Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| `unknown_action` | Action type not in match block | Use one of the 15 defined action strings |
| `file_not_found` | STL/CSV path does not exist | Verify absolute path and file permissions |
| `node_not_found` | Target node name not in scene tree | Check name via `read_scene_tree` first |
| `invalid_params` | Missing required param or type mismatch | Check param table for the action |
| `export_failed` | HTML5 export templates missing | Install Godot export templates or use CLI |
| `mesh_import_error` | STL file corrupt or not binary format | Use binary STL (not ASCII); check file integrity |
| `particle_limit_exceeded` | Count > 1,000,000 | Reduce particle count |

### MCP Tool Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| `bridge_not_connected` | TCP connection to bridge lost | Auto-reconnect in lifespan handler |
| `godot_not_installed` | `is_installed()` returned False | Set `GODOT_PATH` env var |
| `invalid_argument` | Missing or malformed parameter | Check tool signature in mcp-server.md |
| `tool_execution_error` | Generic bridge-side failure | Check Godot console for GDScript errors |

### HTTP Status Codes

| Code | When |
|------|------|
| 200 | Successful tool execution via REST |
| 400 | Unknown tool name or invalid request body |
| 500 | Tool function raised an exception |
| 503 | Godot bridge not connected |
