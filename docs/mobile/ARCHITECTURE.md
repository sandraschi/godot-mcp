# Architecture — Mobile Gateway

## System Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GOLIATH (Server)                             │
│                                                                     │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐  │
│  │  iOS Client   │◄──►│   WS Gateway      │    │   FastMCP 3.2     │  │
│  │  (iPhone)     │ WS │   ws://:10993/    │    │   (MCP Tools)     │  │
│  │               │     │   /mobile/v1      │    │                   │  │
│  │  WebSocket    │     │                   │    │   49 tools        │  │
│  │  or REST      │     │  ┌─────────────┐  │    │                   │  │
│  └──────────────┘     │  │ ClientManager│  │    └────────┬──────────┘  │
│                       │  │ Subscriptions│  │             │             │
│                       │  │ Broadcast    │  │             │             │
│                       │  └──────┬───────┘  │             │             │
│                       └─────────┼──────────┘             │             │
│                                 │                        │             │
│                       ┌─────────▼────────────────────────▼──────────┐  │
│                       │           MobileDispatcher                   │  │
│                       │  (mobile_command.py — Pydantic validation)  │  │
│                       │                                            │  │
│                       │  command → _dispatch_command()              │  │
│                       │  intent  → _dispatch_intent()               │  │
│                       │           → _dispatch_spatial()             │  │
│                       │           → _dispatch_intervention()        │  │
│                       │           → _dispatch_generation()          │  │
│                       └────────────────────┬───────────────────────┘  │
│                                            │                         │
│              ┌─────────────────────────────┼────────────────┐        │
│              ▼                             ▼                ▼        │
│  ┌────────────────────┐    ┌──────────────────────┐  ┌───────────┐  │
│  │  GodotBridge       │    │  Python Tool Runners  │  │ MCPBridge │  │
│  │  (TCP :9080)       │    │  (itch, fleet, etc.)  │  │ (cross-   │  │
│  │                    │    │                      │  │  server)  │  │
│  │  send("import_glb",│    │  _run_python_tool()   │  │           │  │
│  │  {...})            │    │  workflow_run()        │  │ :10865    │  │
│  └────────┬───────────┘    └──────────────────────┘  └───────────┘  │
│           │                                                         │
└───────────┼─────────────────────────────────────────────────────────┘
            │ TCP :9080
            ▼
┌──────────────────────┐
│    Godot 4 Engine     │
│  (editor or headless) │
│                       │
│  mcp_bridge.gd        │
│  (GDScript autoload)  │
│                       │
│  Actions:             │
│  - import_glb         │
│  - add_light          │
│  - read_scene_tree    │
│  - set_material       │
│  - spawn_particles    │
│  - export_web         │
│  ... (18 total)       │
└───────────────────────┘
```

## Data Flow

### Synchronous Command (e.g., query scene tree)

```
iOS ──WS──► ws_gateway.py ──► _dispatch_command()
                                  │
                                  ▼
                           GodotBridge.send("read_scene_tree")
                                  │
                                  ▼  TCP :9080
                           Godot Engine (mcp_bridge.gd)
                                  │
                                  ▼  TCP response
                           GodotBridge ← JSON result
                                  │
                                  ▼
                           _make_response("result", {...})
                                  │
iOS ◄──WS── ws_gateway.py ◄──────┘
```

### Asynchronous Subscription (e.g., live logs)

```
iOS ──WS──► {"type": "subscribe", channels: ["logs"]}
                  │
                  ▼
           client.subscriptions.add("logs")
                  │
                  ▼
           _make_response("ack", {subscribed: ["logs"]})
iOS ◄──WS──┘

           [background task: _push_log_entries]
                  │  every 0.5s
                  ▼
           clients.broadcast({event}, channel="logs")
                  │
                  ▼  only to subscribed clients
iOS ◄──WS── {"type": "event", payload: {channel: "logs", data: "..."}}
```

### High-Level Intent (e.g., place asset)

```
iOS ──WS──► {"type": "intent", app: "spatial-vibe",
              payload: {intent_type: "place_asset", ...}}
                  │
                  ▼
           _handle_spatial_intent()
                  │
                  ├──► GodotBridge.send("import_glb", {...})
                  │       └── TCP :9080 → Godot
                  │
                  ├──► if material:
                  │      GodotBridge.send("set_material", {...})
                  │       └── TCP :9080 → Godot
                  │
                  ▼
           _make_response("result", {success, data, intent_type})
iOS ◄──WS──┘
```

## Network Ports

| Port | Service | Protocol | Direction |
|------|---------|----------|-----------|
| `10993` | FastAPI + FastMCP (gateway) | HTTP/WS/SSE | Client → Server |
| `9080` | Godot engine bridge | TCP (JSON) | Server → Godot |
| `10865` | worldlabs-mcp (fleet pipeline) | HTTP | Server → Server |
| `10992` | Vite React dashboard | HTTP | Browser → Server |

## Rationale — Design Decisions

### Why a WebSocket Gateway instead of direct REST?

The three iOS apps all need **real-time push** (agent state changes, log streaming,
progress updates). REST is request-response only — the iOS client would have to
poll. WebSocket gives us:

- **Server push**: agents get stuck, logs get written, status changes — the server
  tells the iOS client immediately
- **Subscription model**: clients opt in to specific channels, reducing bandwidth
- **Single connection**: one TCP socket for all command/response/event traffic,
  no connection per-request overhead

### Why wrap the TCP bridge instead of talking to Godot directly?

Godot's `mcp_bridge.gd` speaks raw TCP with newline-delimited JSON. iOS's
`Network.framework` (NWConnection) *can* do TCP, but:

- **NAT traversal**: TCP direct to Godot's port 9080 fails if Godot is on a
  different subnet. The WebSocket gateway runs on the same machine as Godot,
  so the TCP connection is always localhost
- **Authentication**: the WebSocket gateway can require JWT auth. Raw TCP has
  no auth layer
- **Subscription multiplexing**: one TCP connection to Godot serves many iOS clients,
  rather than each iOS client needing its own TCP connection to Godot
- **Resilience**: if Godot restarts, the gateway reconnects transparently.
  iOS clients stay connected to the gateway

### Why Pydantic validation (MobileCommand)?

Every message from iOS is validated through `mobile_command.py`'s Pydantic models
before hitting any tool logic. This means:

- Malformed messages are rejected with specific error codes before they reach Godot
- The schema is the single source of truth — the same models used for validation
  are dumped into the `/mobile/v1/help` response
- Adding a new intent type is just adding a new enum variant + payload model

### Why three separate apps instead of one unified interface?

Each app has a fundamentally different interaction pattern:

| App | Interaction Pattern | Primary Input |
|-----|-------------------|---------------|
| Spatial Vibe-Director | Sporadic high-bandwidth commands | Spatial anchors + voice |
| State-Surveiller | Continuous monitoring + rare intervention | Subscriptions + commands |
| Pocket Architect | Burst generation + approval workflow | Text prompts + approval actions |

Trying to unify them would force the iOS client to carry all three interaction
modes simultaneously. Separate apps keep the attack surface narrow and the
iOS client lightweight.

## Component Inventory

### `ws_gateway.py` — WebSocket Gateway

```
Purpose:     Accept WebSocket connections from iOS clients
Pattern:     Single FastAPI endpoint, one handler per client
State:       ClientManager tracks all connected clients + subscriptions
Background:  _push_log_entries (0.5s), _push_godot_status (2s)
```

### `mobile_command.py` — Message Validation + Dispatch

```
Purpose:     Validate incoming iOS messages, route to correct handler
Exports:     MobileCommand (Pydantic model), MobileDispatcher (dispatch logic)
Validation:  Envelope → MessageType check → Payload model validation
Dispatch:    command → _run_python_tool or GodotBridge.send()
             intent → app-specific handler (spatial/intervention/generation)
```

### `mobile_help.py` — Self-Documenting Help

```
Purpose:     Generate the machine-readable protocol reference
Exports:     get_mobile_help() → MobileHelp dataclass
             generate_help_dict() → JSON-serializable dict
Data:        Bridge actions, Python tools, tool chains, channels,
             error codes, protocol schemas, examples
```

### `godot_bridge.py` — TCP Bridge Client

```
Purpose:     Communicate with Godot over TCP port 9080
Exists:      Pre-dates the iOS gateway
Interface:   connect(), disconnect(), send(action, params)
Protocol:    Newline-delimited JSON requests → newline-delimited JSON responses
```

## Error Handling Philosophy

Errors cascade through three layers:

```
Layer 1: WebSocket transport
  → Connection lost, timeout, malformed JSON
  → Handled in mobile_ws_handler() with WebSocketDisconnect catch

Layer 2: Message validation (MobileCommand Pydantic models)
  → Invalid type, missing fields, unknown app
  → Returns error response with error_code + recovery_hint

Layer 3: Tool execution
  → Bridge disconnected, Godot error, tool not found
  → Returns error response from the tool or bridge

Error codes: BRIDGE_DISCONNECTED, ANCHOR_NOT_FOUND, TOOL_FAILED,
             INVALID_INTENT, AUTH_EXPIRED, RATE_LIMITED
```

Every error includes a `recovery_hint` field so the iOS client
can show actionable guidance to the user.
