# App #1 — Spatial Vibe-Director (XR Blueprinting)

```
Intent type:  "spatial-vibe"
Endpoints:    WS /mobile/v1  |  POST /mobile/v1/command
Key pattern:  ARKit frame + voice → spatial anchor → Godot scene manipulation
```

## Concept

Treat the iPhone as a **spatial lens** into your Godot engine. Walk around a
physical space (living room, outdoor area), speak natural language commands,
and watch the Godot scene on your server update in real time.

The phone captures ARKit spatial anchors and voice transcripts, packages them
into structured intents, and fires them to Goliath. Goliath decomposes each
intent into a sequence of godot-mcp tool calls — importing assets, placing
lights, wiring trigger zones — all against the live Godot engine.

This is **not** a mobile game editor. It's a spatial input device for a
headless engine running on dual 4090s.

## User Experience

```
1. User opens the app, points phone at a room
2. ARKit maps surfaces: walls, floor, ceiling
3. User speaks: "drop a low-poly asset tower right against that wall"
4. Phone tracks spatial anchor "wall_001" + voice transcript
5. Intent fires to Goliath
6. Godot scene updates: tower appears at the wall's position
7. Phone streams back a screenshot or scene tree snapshot
8. User speaks: "anchor a floating light above it"
9. Light appears above the tower
```

## Data Models

### Spatial Anchor (from ARKit)

```json
{
  "anchor_id": "wall_001",
  "transform": {
    "position": {"x": 1.23, "y": 0.0, "z": -4.56},
    "rotation": {"x": 0.0, "y": 0.707, "z": 0.0, "w": 0.707},
    "scale":    {"x": 1.0, "y": 1.0, "z": 1.0}
  },
  "physical_space": {
    "room_shape": "rectangle",
    "floor_level": 0.0,
    "dimensions": {"width": 6.0, "length": 8.0, "height": 3.0}
  },
  "tracking_state": "normal"
}
```

### Spatial Intent (iOS → Goliath)

```json
{
  "type": "intent",
  "app": "spatial-vibe",
  "payload": {
    "intent_type": "place_asset",
    "transcript": "drop a low-poly asset tower right against that wall",
    "confidence": 0.92,
    "target_anchor": "wall_001",
    "parameters": {
      "asset_ref": "artifact:lowpoly_tower_01",
      "position": {"x": 1.23, "y": 0.0, "z": -4.56},
      "scale": 1.0,
      "material": {"color": "#4488ff", "roughness": 0.3}
    }
  }
}
```

### Response (Goliath → iOS)

```json
{
  "id": "uuid",
  "type": "result",
  "correlation_id": "msg-001",
  "payload": {
    "success": true,
    "data": {
      "imported": true,
      "name": "LowPolyTower_01",
      "total_nodes": 14,
      "mesh_count": 3
    },
    "intent_type": "place_asset",
    "scene_tree_path": "/root/Main/LowPolyTower_01"
  }
}
```

## Intent Catalog

| Intent | What it Does | Tool Chain | Critical Params |
|--------|-------------|------------|-----------------|
| `place_asset` | Import & position 3D asset at a spatial anchor | `godot_import_glb` → `godot_set_material` | `asset_ref`, `position`, `material` |
| `anchor_light` | Place dynamic light at a spatial position | `godot_add_light` | `light_type`, `position`, `intensity` |
| `wire_trigger` | Create proximity trigger between two anchors | `godot_read_scene_tree` → `workflow_run` | `paired_anchor`, `trigger_condition` |
| `move_node` | Reposition an existing scene node | `godot_read_scene_tree` → `modify-node` | `node_path`, `new_position` |
| `delete_node` | Remove a node from the scene tree | `remove_node` | `node_path` |
| `query_space` | Get full scene hierarchy as JSON | `godot_read_scene_tree` | (none) |

## ARKit Integration (iOS 27)

The iOS 27 beta is expected to introduce:

1. **Deeper ARKit intent parsing** — on-device spatial understanding that maps
   natural language ("right against that wall") to structured anchor references
2. **Zero-latency model offloading** — local Neural Engine processes the spatial
   frame before sending the semantic payload to the server
3. **System automation hooks** — trigger intents from Shortcuts or focus modes

The mobile gateway's intent schema is designed to absorb these directly:
the `transcript` and `confidence` fields accept iOS 27's speech-to-intent output,
and the `target_anchor` field maps to ARKit anchor UUIDs.

```
iOS 27                         This Gateway
─────────                      ────────────
SpatialTrigger  ──► intent_type: "wire_trigger"
SpatialAnchor   ──► target_anchor: "wall_001"
VoiceIntent     ──► transcript + confidence
```

## Server-Side Dispatch

Found in `ws_gateway.py:_handle_spatial_intent()` and
`mobile_command.py:MobileDispatcher._dispatch_spatial()`.

The dispatch logic:

1. Validates the intent payload against `SpatialIntentPayload` Pydantic model
2. Matches `intent_type` to a handler method
3. For `place_asset`: calls `GodotBridge.send("import_glb", ...)` followed by
   `GodotBridge.send("set_material", ...)` if a material is specified
4. For `anchor_light`: calls `GodotBridge.send("add_light", ...)` with the
   spatial position mapped to Godot coordinates
5. For `query_space`: calls `GodotBridge.send("read_scene_tree")` and returns
   the full tree

### Adding a New Spatial Intent

```python
# 1. Add to IntentType enum in mobile_command.py
class IntentType(str, Enum):
    place_asset = "place_asset"
    my_new_intent = "my_new_intent"     # ← add here

# 2. Add handler in ws_gateway.py:_handle_spatial_intent()
if intent_type == "my_new_intent":
    # your logic here
    return _make_response(...)

# 3. Add tool chain to mobile_help.py TOOL_CHAINS
ToolChain("spatial-vibe", "my_new_intent",
    "Description", ["tool1", "tool2"])
```

## Testing

```bash
# Using the example client:
python examples/mobile_client.py ws://127.0.0.1:10993/mobile/v1 spatial-vibe

# Direct curl (REST):
curl -X POST http://127.0.0.1:10993/mobile/v1/command \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-001",
    "type": "intent",
    "app": "spatial-vibe",
    "payload": {
      "intent_type": "query_space",
      "parameters": {}
    }
  }'
```
