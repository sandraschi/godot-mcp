# Extending the Mobile Gateway

How to add new tools, intents, subscription channels, or entirely new apps.

---

## 1. Add a New Tool (to an Existing App)

The simplest extension — add a tool to the gateway without touching any
app-specific code.

### Step 1: Implement the tool (if it's new)

If it's a Godot bridge tool, add a handler in `mcp_bridge.gd` (GDScript side).
If it's a Python-side tool, create a function in the appropriate module.

### Step 2: Expose via REST (if not already)

In `server.py`, add to the `action_map` dict in `execute_tool()`:

```python
action_map = {
    ...
    "godot_my_new_tool": (None, "my_new_tool"),
}
```

And add to the `PYTHON_TOOLS` set if it's a Python-side tool:

```python
PYTHON_TOOLS = {
    ...
    "my_python_tool",
}
```

### Step 3: Register in mobile_help.py

Add to `BRIDGE_ACTIONS` or `PYTHON_TOOLS` list so it appears in `GET /mobile/v1/help`.

```python
BridgeAction("my_new_tool", "Description of my new tool",
    ["param1", "param2"], ["return1", "return2"])
```

### Step 4: Done

The tool is now available via:
- `WS {"type": "command", "payload": {"tool": "godot_my_new_tool", "arguments": {...}}}`
- `POST /mobile/v1/command`

---

## 2. Add a New Intent Type (to an Existing App)

For example, adding a `rotate_node` intent to the Spatial Vibe app.

### Step 1: Add to Enum

In `mobile_command.py`:

```python
class IntentType(str, Enum):
    place_asset = "place_asset"
    rotate_node = "rotate_node"     # ← add
    ...
```

### Step 2: Add Handler

In `ws_gateway.py:_handle_spatial_intent()`:

```python
if intent_type == "rotate_node":
    node_path = params.get("node_path", "")
    rotation = params.get("rotation", {"x": 0, "y": 0, "z": 0, "w": 1})
    result = bridge.send("modify-node", {
        "node": node_path,
        "property": "rotation",
        "value": rotation,
    })
    return _make_response(msg.get("id"), "result", {
        "success": result.get("success", False),
        "data": result.get("data", {}),
        "intent_type": intent_type,
    })
```

### Step 3: Add to Dispatch (if needed)

If the intent needs non-trivial decomposition (multiple tool calls, LLM sampling,
cross-server calls), add a method to `MobileDispatcher` in `mobile_command.py`.

### Step 4: Document

Add the intent to:
- `docs/mobile/APP_SPATIAL_VIBE.md` — Intent Catalog table
- `mobile_help.py` — `TOOL_CHAINS` list
- `mobile_help.py` — `PROTOCOL_SCHEMAS["apps"]["spatial-vibe"]["intent_types"]` list

### Step 5: Done

iOS clients can now send:
```json
{"type": "intent", "app": "spatial-vibe",
 "payload": {"intent_type": "rotate_node",
             "parameters": {"node_path": "/root/Tower", "rotation": {"x": 0, "y": 45, "z": 0, "w": 1}}}}
```

---

## 3. Add a New Subscription Channel

For example, a `memory:usage` channel that pushes RAM/VRAM metrics.

### Step 1: Create the push task

In `ws_gateway.py`:

```python
async def _push_memory_usage():
    """Periodically push memory metrics to subscribed clients."""
    while True:
        await asyncio.sleep(5.0)
        import psutil
        mem = psutil.virtual_memory()
        await clients.broadcast(
            {"id": str(uuid.uuid4()), "type": "event",
             "correlation_id": None,
             "payload": {"channel": "memory:usage", "data": {
                 "ram_pct": mem.percent,
                 "ram_gb": round(mem.used / 1e9, 1),
                 "vram_pct": None,  # GPU-dependent
             }}},
            channel="memory:usage",
        )
```

### Step 2: Register in startup

In `start_background_tasks()`:

```python
_background_tasks.append(loop.create_task(_push_memory_usage()))
```

### Step 3: Document

- Add to `mobile_help.py` CHANNELS list
- Add to `docs/mobile/PROTOCOL_REFERENCE.md` §5

### Step 4: Done

iOS clients can now subscribe with:
```json
{"type": "subscribe", "payload": {"channels": ["memory:usage"]}}
```

---

## 4. Add an Entirely New App

For example, adding a "Soundscape Designer" app.

### Step 1: Define the app

In `mobile_command.py`:
```python
class AppType(str, Enum):
    spatial_vibe = "spatial-vibe"
    state_surveiller = "state-surveiller"
    pocket_architect = "pocket-architect"
    soundscape_designer = "soundscape-designer"    # ← add
```

### Step 2: Create payload model

```python
class SoundscapePayload(BaseModel):
    intent_type: IntentType
    bpm: int = 120
    genre: str = "ambient"
    parameters: dict[str, Any] = Field(default_factory=dict)
```

Add validation in `MobileCommand.validate_payload()`:
```python
elif app == AppType.soundscape_designer:
    SoundscapePayload.model_validate(v)
```

### Step 3: Create handler in ws_gateway.py

```python
async def _handle_soundscape_intent(client: WSClient, msg: dict) -> dict:
    payload = msg.get("payload", {})
    intent_type = payload.get("intent_type", "")
    # ... implement audio routing logic

async def _dispatch_intent(client, msg):
    ...
    if app == "soundscape-designer":
        return await _handle_soundscape_intent(client, msg)
```

### Step 4: Create deep-dive doc

`docs/mobile/APP_SOUNDSCAPE.md`

### Step 5: Document in help

Add to `mobile_help.py`:
```python
PROTOCOL_SCHEMAS["apps"]["soundscape-designer"] = {
    "description": "Mobile audio spatializer — place sound sources in 3D space",
    "intent_types": ["place_source", "set_reverb", "route_to_deck"],
    ...
}
```

### Step 6: Done

iOS clients connect with `{"app": "soundscape-designer"}` and send
app-specific intents.

---

## 5. Architecture Checklist

When extending the gateway, touch these files in order:

| # | File | What to Change |
|---|------|---------------|
| 1 | `mcp_bridge.gd` | Add new GDScript handler (if Godot-side) |
| 2 | `tools/core_tools.py` | Add MCP tool function (if new Godot tool) |
| 3 | `tools/__init__.py` | Register new tool module (if new module) |
| 4 | `server.py` | Add to action_map + PYTHON_TOOLS |
| 5 | `services/mobile_command.py` | Add Enum variant + Pydantic model + dispatch |
| 6 | `services/ws_gateway.py` | Add handler + background task (if channel) |
| 7 | `services/mobile_help.py` | Add to BRIDGE_ACTIONS / TOOL_CHAINS / CHANNELS |
| 8 | `docs/mobile/APP_*.md` | Add deep-dive doc |
| 9 | `docs/mobile/PROTOCOL_REFERENCE.md` | Update tool/channel tables |
| 10 | `docs/mobile/INDEX.md` | Add link |

---

## 6. Testing Your Extension

```bash
# Start server
just serve

# Verify help includes your addition
curl http://127.0.0.1:10993/mobile/v1/help | jq '.bridge_actions[] | select(.action == "my_new_tool")'

# Test via example client
python examples/mobile_client.py ws://127.0.0.1:10993/mobile/v1 spatial-vibe

# Direct curl test
curl -X POST http://127.0.0.1:10993/mobile/v1/command \
  -H "Content-Type: application/json" \
  -d '{"type": "command", "payload": {"tool": "godot_my_new_tool", "arguments": {}}}'
```
