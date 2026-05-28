# Protocol Reference — Mobile Gateway v0.1.0

Comprehensive reference for the WebSocket/REST protocol between iOS clients
and the godot-mcp gateway. Machine-readable version available at `GET /mobile/v1/help`.

---

## 1. Transport

### WebSocket (Primary)

```
ws://<host>:10993/mobile/v1
```

- Full-duplex, persistent connection
- Supports subscriptions (server push) and streaming (frames, progress)
- Handshake required within 5s of connect

### REST (Fallback)

```
POST <host>:10993/mobile/v1/command
GET  <host>:10993/mobile/v1/help
```

- Stateless: no subscriptions, no streaming
- Same request/response envelope as WebSocket
- Useful for testing, single-shot commands, or when WS is unavailable

---

## 2. Message Envelope

### Inbound (iOS → Server)

```json
{
  "id": "8-char-uuid",
  "type": "command | intent | subscribe | unsubscribe | help",
  "app": "spatial-vibe | state-surveiller | pocket-architect | null",
  "timestamp": "ISO-8601 | null",
  "payload": {}
}
```

Fields:
- `id` — Client-generated idempotency key. Server echoes as `correlation_id`.
  Optional — server generates one if omitted.
- `type` — Message category (see section 3).
- `app` — Required for `intent` messages. Optional for `command` (tools
  are the same regardless of app). Omit for `help`.
- `payload` — Varies by type and app (see sections 4-7).

### Outbound (Server → iOS)

```json
{
  "id": "8-char-uuid",
  "type": "ack | result | error | event | frame",
  "correlation_id": "msg-id-being-replied-to | null",
  "payload": {}
}
```

Fields:
- `id` — Server-generated message identifier.
- `type` — Response category.
  - `ack`: Confirmation (subscribe, unsubscribe, handshake).
  - `result`: Synchronous command/intent completion.
  - `error`: Error with error_code, message, recovery_hint.
  - `event`: Server-pushed event for subscribed channels.
  - `frame`: Server-pushed base64-encoded image frame.
- `correlation_id`: Echo of the inbound message `id`. `null` for push events.

---

## 3. Message Types

### `type: "command"` — Direct Tool Invocation

Execute any godot-mcp tool by name. Tools prefixed with `godot_` route to the
Godot TCP bridge (port 9080). All other tools run as Python-side operations.

```json
{
  "type": "command",
  "payload": {
    "tool": "godot_read_scene_tree",
    "arguments": {}
  }
}
```

```json
{
  "type": "command",
  "payload": {
    "tool": "godot_import_glb",
    "arguments": {
      "path": "C:/models/tower.glb",
      "name": "MyTower",
      "scale": 1.0,
      "position": {"x": 0, "y": 0, "z": -5}
    }
  }
}
```

### `type: "intent"` — High-Level Semantic Action

Decomposed into tool chains by the dispatcher. Requires `app` field.

```json
{
  "type": "intent",
  "app": "spatial-vibe",
  "payload": {
    "intent_type": "place_asset",
    "transcript": "drop a tower against the wall",
    "parameters": {"asset_ref": "...", "material": {...}}
  }
}
```

### `type: "subscribe"` / `"unsubscribe"` — Channel Management

```json
{
  "type": "subscribe",
  "payload": {"channels": ["logs", "godot:status", "agent:*"]}
}
```

Channels support wildcard suffix: `agent:*` matches `agent:test_bot_01`,
`agent:test_bot_02`, etc.

### `type: "help"` — Request Protocol Reference

```json
{"type": "help", "payload": {}}
```

Returns the full protocol document as a single result message. Also available
via `GET /mobile/v1/help`.

---

## 4. App-Specific Payloads

### Spatial Vibe (`app: "spatial-vibe"`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `intent_type` | string | yes | `place_asset`, `anchor_light`, `wire_trigger`, `move_node`, `delete_node`, `query_space` |
| `transcript` | string | no | Raw voice transcription |
| `confidence` | float | no | Speech confidence 0.0–1.0 |
| `target_anchor` | string | no | ARKit anchor UUID |
| `parameters` | dict | yes | Intent-specific params |

Parameter schemas by intent:

| Intent | Parameters |
|--------|-----------|
| `place_asset` | `asset_ref`, `position{x,y,z}`, `scale`, `material{color,roughness}` |
| `anchor_light` | `light_type`, `position{x,y,z}`, `intensity`, `color` |
| `wire_trigger` | `paired_anchor`, `trigger_condition`, `action` |
| `move_node` | `node_path`, `new_position{x,y,z}` |
| `delete_node` | `node_path` |
| `query_space` | (none) |

### State Surveiller (`app: "state-surveiller"`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `intervention_type` | string | yes | `reparent`, `set_param`, `force_restart`, `kill_agent`, `resume_loop` |
| `target_agent` | string | yes | Agent ID (uuid) |
| `parameters` | dict | yes | Intervention-specific params |

| Intervention | Parameters |
|-------------|-----------|
| `set_param` | `node_path`, `property`, `value` |
| `reparent` | `node_path`, `new_parent` |
| `force_restart` | (none — kills and restarts target agent) |
| `kill_agent` | (none — terminates agent) |
| `resume_loop` | (none — resumes the testing orchestrator) |

### Pocket Architect (`app: "pocket-architect"`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | yes | Natural language generation description |
| `mode` | string | yes | `environment`, `asset`, `ui_theme`, `behavior`, `gdscript` |
| `constraints` | dict | no | `style`, `poly_count_target`, `resolution`, `reference_assets[]` |
| `outputs_requested` | [string] | no | `screenshot`, `video_clip`, `scene_file`, `gdscript` |

Constraint fields:

| Field | Type | Values |
|-------|------|--------|
| `style` | string | `dark-synth`, `cyberpunk`, `minimalist`, `organic`, `neon`, `industrial` |
| `poly_count_target` | int | Target polygon count (e.g. 50000) |
| `resolution` | string | `low`, `medium`, `high` |
| `reference_assets` | [string] | Artifact UUIDs to use as style reference |

---

## 5. Subscription Channels

| Channel | Payload | Frequency |
|---------|---------|-----------|
| `agent:*` | `{"agent_id", "status", "current_action", "scene_state", "last_error", "lddo_score"}` | ~2s |
| `agent:{id}` | Same as above, filtered to one agent | ~2s |
| `logs` | `{"channel": "logs", "data": "timestamp - level - message"}` | ~0.5s |
| `frames:{id}` | `{"channel": "frames:{id}", "data": "base64 PNG"}` | ~1s |
| `godot:status` | `{"channel": "godot:status", "data": {"version", "node_count", "fps", "bridge_connected"}}` | ~2s |
| `progress` | `{"channel": "progress", "data": {"generation_id", "step", "pct", "message"}}` | on change |

---

## 6. All Available Tools

### Godot Bridge Tools (route to TCP :9080)

| Tool | Description | Parameters |
|------|-------------|-----------|
| `godot_status` | Engine version, node count, FPS | (none) |
| `godot_import_stl` | Import STL mesh | `path`, `name`, `scale`, `position{x,y,z}` |
| `godot_import_glb` | Import GLB/GLTF | `path`, `name`, `scale`, `position{x,y,z}` |
| `godot_import_obj` | Import OBJ | `path`, `name`, `scale`, `position{x,y,z}` |
| `godot_load_velocity_field` | Load CFD CSV | `csv_path`, `name` |
| `godot_spawn_particles` | GPU particle system | `count`, `name`, `color`, `spread_{x,y,z}` |
| `godot_animate_streamlines` | Animate particles along velocity field | `velocity_field`, `particle_system`, `speed` |
| `godot_create_camera` | Camera3D with orbit | `name`, `position{x,y,z}`, `look_at{x,y,z}`, `fov` |
| `godot_add_light` | Light source | `type`, `name`, `intensity`, `position{x,y,z}` |
| `godot_set_material` | PBR material on mesh | `node`, `color`, `roughness` |
| `godot_export_web` | Export to HTML5 | `output_path`, `resolution_x`, `resolution_y` |
| `godot_read_scene_tree` | Scene hierarchy JSON | (none) |
| `godot_set_config` | Config file update | `section`, `key`, `value` |
| `godot_headless_verify` | Headless mode check | `script` |

### Python Tools (server-side, no Godot bridge)

| Tool | Domain | Version |
|------|--------|---------|
| `itch_status` | itch.io | 0.2.1 |
| `godot_export_release` | itch.io | 0.2.1 |
| `itch_push_preview` | itch.io | 0.2.1 |
| `itch_push` | itch.io | 0.2.1 |
| `itch_latest_version` | itch.io | 0.2.1 |
| `ship_to_itch` | itch.io | 0.2.1 |
| `fleet_exchange_status` | fleet | 0.2.1 |
| `fleet_import_from_exchange` | fleet | 0.2.1 |
| `fleet_worldlabs_get_world` | fleet | 0.2.1 |
| `fleet_worldlabs_stage_mesh` | fleet | 0.2.1 |
| `fleet_worldlabs_stage_splat` | fleet | 0.2.1 |
| `fleet_worldlabs_import_mesh` | fleet | 0.2.1 |
| `workflow_list` | workflows | 0.1.0 |
| `workflow_run` | workflows | 0.1.0 |

---

## 7. Error Codes

| Code | HTTP | Meaning | Recovery |
|------|------|---------|----------|
| `BRIDGE_DISCONNECTED` | 503 | Godot engine not running | Start Godot with MCP bridge addon |
| `ANCHOR_NOT_FOUND` | 404 | ARKit anchor lost tracking | Re-scan surface |
| `TOOL_FAILED` | 400 | Tool execution error | Check params, retry |
| `INVALID_INTENT` | 400 | Unknown intent type | Check /help for valid types |
| `AUTH_EXPIRED` | 401 | JWT token expired | Re-authenticate |
| `RATE_LIMITED` | 429 | >30 commands/minute | Back off, retry with backoff |
| `HANDSHAKE_FAILED` | 400 | WS handshake invalid | Send valid JSON with app field |
| `UPGRADE_REQUIRED` | 426 | Protocol version mismatch | Update iOS app |

Error response shape:
```json
{
  "type": "error",
  "correlation_id": "msg-001",
  "payload": {
    "success": false,
    "error_code": "BRIDGE_DISCONNECTED",
    "message": "Connection refused at 127.0.0.1:9080. Is Godot running?",
    "recovery_hint": "Ensure Godot engine is running with MCP bridge addon"
  }
}
```

---

## 8. Limits

| Limit | Value | Notes |
|-------|-------|-------|
| Max WebSocket connections | 50 | Per gateway instance |
| Max subscriptions per client | 20 | Beyond this, server responds with RATE_LIMITED |
| Command rate limit | 30/min per client | Rolling window |
| Max payload size | 256 KB | Per WebSocket message |
| Max frame size | 2 MB | Per frame message (base64 PNG) |
| Handshake timeout | 5s | Client must send initial JSON within 5s |
| Tool timeout | 10s | Godot bridge operations timeout after 10s |
| Frame push rate | 1 fps | Maximum frame push frequency per channel |
