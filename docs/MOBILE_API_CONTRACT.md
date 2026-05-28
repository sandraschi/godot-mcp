# Mobile API Contract — iOS ↔ Goliath Gateway

**Version**: 0.1.0
**Target**: WWDC iOS 27 beta (June 8, 2026)
**Gateway**: `ws://<goliath-host>:10993/mobile/v1` (WebSocket) + `POST /mobile/v1/command` (REST fallback)

---

> **Deep documentation** is in `docs/mobile/`:
> - [Architecture & Data Flow](mobile/ARCHITECTURE.md)
> - [App #1: Spatial Vibe-Director](mobile/APP_SPATIAL_VIBE.md)
> - [App #2: State-Surveiller](mobile/APP_STATE_SURVEILLER.md)
> - [App #3: Pocket Architect](mobile/APP_POCKET_ARCHITECT.md)
> - [Protocol Reference](mobile/PROTOCOL_REFERENCE.md)
> - [Extending the Gateway](mobile/EXTENDING.md)
>
> This file is the original contract spec. For day-to-day work, start at [docs/mobile/INDEX.md](mobile/INDEX.md).

---

## 1. Transport Layer

### WebSocket (Primary)

```
ws://<host>:10993/mobile/v1
```

Message envelope:
```json
{
  "id": "uuid-v4",
  "type": "command | subscribe | unsubscribe | intent",
  "app": "spatial-vibe | state-surveiller | pocket-architect",
  "timestamp": "2026-06-08T14:00:00Z",
  "payload": { "...app-specific..." }
}
```

Responses:
```json
{
  "id": "uuid-v4",
  "type": "ack | result | error | event | frame",
  "correlation_id": "message-id-being-replied-to",
  "timestamp": "...",
  "payload": { "...response-specific..." }
}
```

### REST (Fallback — stateless commands)

```
POST /api/v1/mobile/command
Content-Type: application/json
Authorization: Bearer <mobile-jwt>

{
  "id": "uuid-v4",
  "app": "spatial-vibe",
  "payload": { "...app-specific..." }
}
```

Returns same envelope as WS response.

### Auth

Initial WS handshake includes `Authorization: Bearer <mobile-jwt>` header.
JWT issued by Goliath auth service, 24h expiry. Scoped to one app at a time.

---

## 2. Spatial Vibe-Director (App #1)

### Purpose
Phone as spatial lens → voice + ARKit anchors → scene manipulation in Godot.

### Schema: Spatial Anchor

```json
{
  "anchor_id": "uuid-v4",
  "transform": {
    "position": { "x": float, "y": float, "z": float },
    "rotation": { "x": float, "y": float, "z": float, "w": float },
    "scale": { "x": float, "y": float, "z": float }
  },
  "physical_space": {
    "room_shape": "rectangle | l-shaped | open",
    "floor_level": float,
    "dimensions": { "width": float, "length": float, "height": float }
  },
  "tracking_state": "normal | limited | unavailable"
}
```

### Schema: Spatial Intent (Voice + Gesture)

```json
{
  "intent_type": "place_asset | anchor_light | wire_trigger | move_node | delete_node | query_space",
  "transcript": "drop a low-poly tower against that wall",
  "confidence": 0.0-1.0,
  "target_anchor": "anchor-uuid | null",
  "parameters": {
    "asset_ref": "artifact-uuid | prefab-name | null",
    "material": { "color": "#hex", "roughness": float } | null,
    "trigger_condition": "proximity | look_at | timer" | null,
    "paired_anchor": "anchor-uuid | null"
  }
}
```

### Mapped Tool Chains

| iOS Intent | godot-mcp Tools (Sequence) |
|---|---|
| `place_asset` | `godot_import_glb` → `godot_set_material` |
| `anchor_light` | `godot_add_light` |
| `wire_trigger` | `godot_read_scene_tree` → `workflow_run` (custom) |
| `move_node` | `godot_read_scene_tree` → bridge `modify-node` |
| `query_space` | `godot_read_scene_tree` |

### Example Flow

```
iOS (ARKit frame + voice):
  → {"type": "intent", "app": "spatial-vibe",
     "payload": {
       "intent_type": "place_asset",
       "transcript": "drop a low-poly asset tower right against that wall",
       "target_anchor": "wall_001",
       "parameters": {
         "asset_ref": "artifact:lowpoly_tower_01",
         "material": {"color": "#4488ff", "roughness": 0.3}
       }
     }}

Goliath dispatch:
  → artifact_get("lowpoly_tower_01")
  → godot_import_glb(path=artifact.path, scale=1.0,
       position_x=wall_001.x + offset,
       position_y=floor_level,
       position_z=wall_001.z)
  → godot_set_material(node="lowpoly_tower_01", color="#4488ff", roughness=0.3)

Response:
  → {"type": "result", "correlation_id": "...",
     "payload": {
       "success": true,
       "scene_tree_path": "/root/Main/LowPolyTower",
       "screenshot_b64": "..."
     }}
```

---

## 3. Agentic State-Surveiller & QA Crucible (App #2)

### Purpose
Real-time multi-agent test monitoring + hot-fix intervention dashboard.

### Schema: Agent State Snapshot

```json
{
  "agent_id": "string",
  "status": "running | stuck | crashed | completed | idle",
  "current_action": "string",
  "duration_sec": float,
  "scene_state": { "node_count": int, "fps": float, "physics_bodies": int },
  "last_error": "string | null",
  "screenshot_b64": "base64-frame | null",
  "lddo_score": 0.0-1.0
}
```

### Schema: Intervention Command

```json
{
  "intervention_type": "reparent | set_param | force_restart | kill_agent | resume_loop",
  "target_agent": "agent-uuid",
  "parameters": {
    "node_path": "string | null",
    "property": "string | null",
    "value": "any | null",
    "new_parent": "string | null"
  }
}
```

### Schema: Subscription Model

```json
// iOS subscribes to state updates
{"type": "subscribe", "app": "state-surveiller",
 "payload": {"channels": ["agent:*", "logs", "frames:agent_01"]}}

// Server pushes events
{"type": "event", "correlation_id": null,
 "payload": {
   "channel": "agent:agent_01",
   "event": "stuck",
   "data": { "agent_id": "agent_01", "stuck_at": "wave_14", "duration_sec": 120 }
 }}
```

### Mapped Tool Chains

| iOS Intent | godot-mcp Tools |
|---|---|
| `reparent` | `godot_read_scene_tree` → bridge `game_reparent_node` (GDScript) |
| `set_param` | `godot_set_config` + bridge `game_physics_body` (GDScript) |
| `force_restart` | `workflow_run` (test agent restart) |
| `kill_agent` | `bridge_call_tool` (agent management) |
| `resume_loop` | `workflow_run` (resume agent loop) |

### Example Flow

```
iOS subscribes:
  → {"type": "subscribe", "app": "state-surveiller",
     "payload": {"channels": ["agent:*", "logs"]}}

Server push (agent stuck):
  → {"type": "event", "payload": {
       "channel": "agent:test_bot_03",
       "event": "stuck",
       "data": {
         "agent_id": "test_bot_03",
         "scene_state": {"node_count": 142, "fps": 58, "physics_bodies": 7},
         "last_error": "RigidBody 'debris_07' clipping through floor"
       }}}

iOS issues intervention:
  → {"type": "command", "app": "state-surveiller",
     "payload": {
       "intervention_type": "set_param",
       "target_agent": "test_bot_03",
       "parameters": {
         "node_path": "/root/World/Debris/debris_07",
         "property": "mass",
         "value": 0.5
       }}}

Goliath dispatch:
  → bridge send("modify-node", {node: "debris_07", property: "mass", value: 0.5})
  → bridge send("game_eval", {script: "clear_linear_velocity('debris_07')"})
  → workflow_run("resume_test_agent", {agent: "test_bot_03"})
```

---

## 4. Pocket Vibe-Architect (App #3)

### Purpose
Minimalist prompt-to-asset deck. High-level generative steering.

### Schema: Generation Intent

```json
{
  "prompt": "generate a dark-synth modular sci-fi corridor tilemap layout",
  "mode": "environment | asset | ui_theme | behavior_machine",
  "constraints": {
    "style": "dark-synth | cyberpunk | minimalist | organic",
    "poly_count_target": int | null,
    "resolution": "low | medium | high",
    "reference_assets": ["uuid", "uuid"] | null
  },
  "outputs_requested": ["screenshot", "video_clip", "scene_file", "gdscript"]
}
```

### Schema: Generation Result

```json
{
  "generation_id": "uuid",
  "status": "queued | generating | complete | failed",
  "artifacts": [
    {
      "type": "screenshot | video_clip | scene_file | gdscript",
      "url": "data:image/png;base64,... | artifact-uuid",
      "thumbnail_b64": "base64"
    }
  ],
  "artifact_ids": ["depot-uuid"],
  "errors": ["string"] | null
}
```

### Schema: Approval Action

```json
{
  "action": "approve | reject | tweak",
  "generation_id": "uuid",
  "feedback": "make the corridor wider and add flickering neon strips",
  "tweak_params": {
    "scale": float | null,
    "color_scheme": ["hex", "hex"] | null,
    "complexity": "low | medium | high" | null
  }
}
```

### Mapped Tool Chains

| iOS Intent | godot-mcp Tools |
|---|---|
| `generate:environment` | `design_game` → `generate_game_worlds` → `compose_game_scene` |
| `generate:asset` | `artifact_search` → `godot_import_glb` → `godot_set_material` |
| `generate:ui_theme` | `godot_set_config` → `prompt_execute("material_advisor")` |
| `generate:behavior_machine` | `ai_generate_gdscript` → bridge `game_eval` |
| `approve` | `artifact_register` (save to depot) |
| `reject` | `artifact_delete` (if was temp) |
| `tweak` | `prompt_execute` → re-run generative chain |

### Example Flow

```
iOS prompt:
  → {"type": "command", "app": "pocket-architect",
     "payload": {
       "prompt": "dark-synth modular sci-fi corridor tilemap with auto-flickering emission panels",
       "mode": "environment",
       "constraints": {"style": "dark-synth", "resolution": "medium"},
       "outputs_requested": ["screenshot", "gdscript"]
     }}

Goliath dispatch (parallel):
  1. ai_generate_gdscript({spec: "auto-flickering emission shader for sci-fi corridor panels"})
  2. workflow_run("scene_setup")  // camera + lighting
  3. artifact_search(query="sci-fi corridor tilemap")
  4. For each tile: godot_import_glb → godot_set_material (emissive)
  5. bridge send("game_eval", {script: generated_gdscript})
  6. godot_export_web(output_path="/tmp/preview_corridor.html")
  7. artifact_register(name="DarkSynth Corridor", type="scene", tags=["sci-fi", "tilemap"])

Response streaming:
  → {"type": "event", "channel": "progress", "data": {"step": "generating_scripts", "pct": 30}}
  → {"type": "event", "channel": "progress", "data": {"step": "importing_assets", "pct": 60}}
  → {"type": "result", "payload": {
       "status": "complete",
       "generation_id": "gen_001",
       "artifacts": [
         {"type": "screenshot", "thumbnail_b64": "..."},
         {"type": "gdscript", "artifact_id": "artifact:emission_shader_01"}
       ],
       "artifact_ids": ["artifact:emission_shader_01", "artifact:dark_corridor_01"]
     }}
```

---

## 5. Godot Bridge Action Map

Reference: all currently available GDScript bridge actions (port 9080 TCP).

| Action | Parameters | Returns |
|---|---|---|
| `status` | — | version, node_count, fps |
| `import_stl` | path, name, scale, position{x,y,z} | imported, name, vertices, aabb |
| `import_glb` | path, name, scale, position{x,y,z} | imported, name, total_nodes, mesh_count |
| `import_obj` | path, name, scale, position{x,y,z} | imported, name |
| `load_velocity_field` | csv_path, name | loaded, name, point_count, bbox |
| `spawn_particles` | count, name, color, spread_{x,y,z} | spawned, name, count |
| `animate_streamlines` | velocity_field, particle_system, speed | animated, particle_system, speed_multiplier |
| `create_camera` | name, position{x,y,z}, look_at{x,y,z}, fov | created, name, fov, position |
| `add_light` | type, name, intensity, position{x,y,z} | created, name, type, intensity |
| `set_material` | node, color, roughness | set, node, color, roughness |
| `export_web` | output_path | exported, message, output_path |
| `read_scene_tree` | — | scene_tree{name, type, path, children[]}, node_count |
| `set_config` | section, key, value | updated, section, key, value |
| `headless_verify` | script | headless, script_path, message |
| `add_node` (bonus) | parent_path, node_type, name | success, node_path |
| `remove_node` (bonus) | path | success |
| `save_scene` (bonus) | path | success, path |

---

## 6. Error Contract

All errors follow this shape:

```json
{
  "success": false,
  "error_code": "ANCHOR_NOT_FOUND | TOOL_FAILED | BRIDGE_DISCONNECTED | INVALID_INTENT | AUTH_EXPIRED",
  "message": "Human-readable description",
  "recovery_hint": "What the user can do to fix it"
}
```

| Error Code | When | Recovery |
|---|---|---|
| `BRIDGE_DISCONNECTED` | Godot engine not running / bridge port 9080 unreachable | Show "Start Godot" prompt on iOS |
| `ANCHOR_NOT_FOUND` | Spatial anchor lost tracking | Re-scan surface, re-place |
| `TOOL_FAILED` | godot-mcp tool returned error | Show tool error message |
| `INVALID_INTENT` | Voice transcription confidence < 0.4 | Ask user to rephrase |
| `AUTH_EXPIRED` | JWT token expired | Re-authenticate |
| `RATE_LIMITED` | Too many rapid commands | Back off and retry |

---

## 7. Versioning & Compatibility

- Contract version in WS handshake query param: `ws://<host>:10993/mobile/v1`
- Breaking changes increment version (v1 → v2)
- Backward-compatible additions are allowed within a version
- iOS client MUST check `server_version` in handshake ack
- If client_version < min_server_version, server rejects with `UPGRADE_REQUIRED`
