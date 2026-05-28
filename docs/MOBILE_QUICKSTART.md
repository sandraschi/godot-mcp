# Mobile Gateway Quickstart

**Connect an iOS app to your Godot engine in 5 minutes.**

```
ws://host:10993/mobile/v1    ← WebSocket (bidirectional, subscriptions)
POST /mobile/v1/command       ← REST fallback (stateless)
GET  /mobile/v1/help          ← Full protocol reference as JSON
```

---

## 1. Start the Server

```bash
just serve
# or: uv run python -m godot_mcp.server --port 10993
```

Look for the startup line:
```
Mobile gateway: ws://0.0.0.0:10993/mobile/v1 | REST: POST /mobile/v1/command | Help: GET /mobile/v1/help
```

---

## 2. Connect via WebSocket

### Swift (iOS 27+)

```swift
import Foundation

let url = URL(string: "ws://goliath.local:10993/mobile/v1")!
let ws = WebSocket(url: url)

// 1. Handshake
ws.send(json: ["app": "spatial-vibe"])

// 2. Subscribe to live data
ws.send(json: [
    "type": "subscribe",
    "payload": ["channels": ["logs", "godot:status"]]
])

// 3. Execute a command
ws.send(json: [
    "type": "command",
    "payload": [
        "tool": "godot_read_scene_tree",
        "arguments": [:]
    ]
])

// 4. Send a high-level intent (App #1)
ws.send(json: [
    "type": "intent",
    "app": "spatial-vibe",
    "payload": [
        "intent_type": "place_asset",
        "transcript": "drop a tower against the wall",
        "parameters": [
            "asset_ref": "artifact:lowpoly_tower_01",
            "material": ["color": "#4488ff", "roughness": 0.3]
        ]
    ]
])
```

### Python (test client)

```python
import asyncio, json
from httpx_ws import aconnect_ws

async def test_client():
    async with aconnect_ws("ws://127.0.0.1:10993/mobile/v1") as ws:
        # Handshake
        await ws.send_text(json.dumps({"app": "spatial-vibe"}))
        ack = await ws.receive_json()
        print("Connected:", ack["payload"]["client_id"])

        # Subscribe
        await ws.send_text(json.dumps({
            "type": "subscribe",
            "payload": {"channels": ["logs", "godot:status"]}
        }))
        print(await ws.receive_json())

        # Query scene
        await ws.send_text(json.dumps({
            "type": "command",
            "payload": {"tool": "godot_read_scene_tree", "arguments": {}}
        }))
        print(await ws.receive_json())

asyncio.run(test_client())
```

---

## 3. REST Fallback (No WebSocket)

```bash
# Query scene tree
curl -X POST http://127.0.0.1:10993/mobile/v1/command \
  -H "Content-Type: application/json" \
  -d '{
    "type": "command",
    "payload": {
      "tool": "godot_read_scene_tree",
      "arguments": {}
    }
  }'

# Get help
curl http://127.0.0.1:10993/mobile/v1/help | jq .protocol.envelope
```

---

## 4. Available Messages

| Type | Purpose | Payload Shape |
|------|---------|--------------|
| `command` | Direct tool call | `{tool: str, arguments: dict}` |
| `intent` | High-level semantic action | App-specific (see `/help`) |
| `subscribe` | Register for push channels | `{channels: [str]}` |
| `unsubscribe` | Unregister from channels | `{channels: [str]}` |
| `help` | Request protocol reference | `{}` (empty) |

---

## 5. All Available Channels

| Channel | What You Get | Frequency |
|---------|-------------|-----------|
| `agent:*` | All test agent state changes | ~2s |
| `agent:{id}` | Specific agent state | ~2s |
| `logs` | Server log entries | ~0.5s |
| `frames:{id}` | Streamed agent screenshots | ~1s |
| `godot:status` | Godot engine metrics | ~2s |
| `progress` | Long-running op progress | on change |

---

## 6. Three Apps, One Protocol

| App | What It Does | Key Intents |
|-----|-------------|------------|
| `spatial-vibe` | ARKit spatial lens → Godot scene | `place_asset`, `anchor_light`, `query_space` |
| `state-surveiller` | Agent test monitoring + hot-fix | `set_param`, `force_restart`, `resume_loop` |
| `pocket-architect` | Prompt-to-asset generative deck | `generate:environment`, `generate:gdscript`, `approve` |

---

## 7. Error Recovery

| Error | What Happened | Fix |
|-------|-------------|-----|
| `BRIDGE_DISCONNECTED` | Godot engine not running | Start Godot with MCP bridge addon |
| `ANCHOR_NOT_FOUND` | ARKit lost tracking | Re-scan surface |
| `TOOL_FAILED` | Bad params or bridge busy | Check error, fix and retry |
| `INVALID_INTENT` | Unknown intent type | Check /help for valid types |
| `AUTH_EXPIRED` | JWT token expired | Re-authenticate |
| `RATE_LIMITED` | >30 commands/min | Back off and retry |

---

## 8. Need More?

```
Live help:
  GET  /mobile/v1/help            ← Full protocol reference (JSON)
  WS   {"type": "help"}            ← Same, over WebSocket

Deep docs (docs/mobile/):
  INDEX.md                          ← Master index of all mobile docs
  ARCHITECTURE.md                   ← System topology, data flow, rationale
  APP_SPATIAL_VIBE.md               ← App #1: XR Blueprinting
  APP_STATE_SURVEILLER.md           ← App #2: Agent monitoring
  APP_POCKET_ARCHITECT.md           ← App #3: Generative deck
  PROTOCOL_REFERENCE.md             ← Comprehensive protocol reference
  EXTENDING.md                      ← How to add tools, intents, apps
  CHANGELOG.md                      ← Version history
```
