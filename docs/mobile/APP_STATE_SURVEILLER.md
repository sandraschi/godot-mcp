# App #2 — Agentic State-Surveiller & QA Crucible

```
Intent type:  "state-surveiller"
Endpoints:    WS /mobile/v1  (required — this app needs subscriptions)
Key pattern:  Subscribe → Monitor → Intervene → Resume
```

## Concept

Treat the iPhone as a **real-time ops dashboard** for automated agent testing
loops running on Goliath. Multiple AI agents stress-test a Godot build
simultaneously — running through game levels, triggering physics, checking
collisions, verifying game logic.

The State-Surveiller app subscribes to agent state changes, log streams, and
frame captures. When an agent gets stuck or encounters an exception, the phone
buzzes with a push notification. The user opens the app, sees the serialized
scene state and a streamed frame, and issues a **hot-fix intervention** —
reparenting a node, tweaking a physics parameter, or killing and restarting
the agent.

This is **operational command** for a multi-agent factory floor.

## User Experience

```
1. Background: agents are running on Goliath, stress-testing a Godot build
2. Phone buzzes: agent "test_bot_03" stuck at wave 14
3. User opens app → dashboard shows:
   - agent_01: running (fps: 58)
   - agent_02: running (fps: 61)
   - agent_03: STUCK (duration: 120s, error: RigidBody clipping)
4. User taps agent_03 → sees streamed frame + scene state snapshot
5. User dictates: "drop that rigid body's mass to 0.5, clear its velocity,
   and force-restart the agent"
6. App fires intervention command to Goliath
7. Goliath hot-fixes the live simulation:
   - modify-node("debris_07", "mass", 0.5)
   - game_eval("clear_linear_velocity('debris_07')")
   - workflow_run("resume_test_agent")
8. Agent restarts, testing continues
9. User never sits down at a terminal
```

## Data Models

### Agent State Snapshot (Server → iOS, via subscription)

```json
{
  "type": "event",
  "payload": {
    "channel": "agent:test_bot_03",
    "event": "stuck",
    "data": {
      "agent_id": "test_bot_03",
      "status": "stuck",
      "current_action": "navigating_platform_wave_14",
      "duration_sec": 120.5,
      "scene_state": {
        "node_count": 142,
        "fps": 58.2,
        "physics_bodies": 7
      },
      "last_error": "RigidBody 'debris_07' clipping through floor at z=-3.2",
      "lddo_score": 0.87
    }
  }
}
```

### Intervention Command (iOS → Goliath)

```json
{
  "type": "intent",
  "app": "state-surveiller",
  "payload": {
    "intervention_type": "set_param",
    "target_agent": "test_bot_03",
    "parameters": {
      "node_path": "/root/World/Debris/debris_07",
      "property": "mass",
      "value": 0.5
    }
  }
}
```

## Intervention Catalog

| Intervention | Purpose | Backend Action |
|-------------|---------|----------------|
| `reparent` | Move a node to a different parent in the scene tree | `modify-node(node, parent_path)` |
| `set_param` | Modify any property on any node | `modify-node(node, property, value)` |
| `force_restart` | Kill and restart a stuck agent | `workflow_run("test_agent_restart")` |
| `kill_agent` | Terminate a running agent immediately | `bridge_call_tool("kill_agent")` |
| `resume_loop` | Resume the automated testing loop after fix | `workflow_run("resume_test_agent")` |

## Subscription Channels

| Channel | Content | Frequency | Bandwidth |
|---------|---------|-----------|-----------|
| `agent:*` | All agents' state changes | ~2s | Low (100B/event) |
| `agent:{id}` | Single agent state | ~2s | Low (100B/event) |
| `logs` | All server log entries | ~0.5s | Medium (200B/event) |
| `frames:{id}` | Streamed PNG frames from agent's POV | ~1s | High (50KB/frame) |
| `godot:status` | Godot engine FPS, node count, bridge health | ~2s | Low (200B/event) |

**Tip:** Subscribe to `agent:*` and `logs` by default. Subscribe to `frames:{id}`
only when inspecting a specific stuck agent — frames are bandwidth-heavy.

## LDDO Score

**Low-Density Derivative Output (LDDO)** is a 0.0–1.0 metric indicating how
much novel output the agent is producing. A score approaching 1.0 means the
agent is exploring new states. A score trending toward 0.0 means the agent
is in a loop, stuck, or producing repetitive output.

```python
lddo = 1.0 - (unique_states_last_N / total_steps_last_N)
```

The State-Surveiller app can use LDDO to highlight agents that need attention
before they officially crash.

## Server-Side Dispatch

Found in `ws_gateway.py:_handle_intervention_intent()` and
`mobile_command.py:MobileDispatcher._dispatch_intervention()`.

The dispatch:

1. Validates against `InterventionPayload` Pydantic model
2. For `set_param`: calls `GodotBridge.send("modify-node", ...)` to hot-fix
   the live simulation
3. For `force_restart`: checks for a `test_agent_restart` workflow and executes
   it via the workflow engine

```
intervention_type="set_param"
  → mobile_command.py:_dispatch_intervention()
    → GodotBridge.send("modify-node", {node, property, value})
      → TCP :9080 → Godot mcp_bridge.gd
        → get_node(node).set(property, value)
      ← TCP response → success/failure
    → MobileDispatchResult
```

## Design Notes

### Why WebSocket is Required (not just REST)

The State-Surveiller app fundamentally needs server push. REST polling would:
- Waste bandwidth (most of the time, nothing has changed)
- Introduce latency (a stuck agent would be detected only on the next poll)
- Miss events (agent stuck → unstuck → stuck again between polls)

The subscription model solves this: the iOS client declares what it cares about,
and the server pushes only when something changes.

### Why Frames are Optional

Streaming rendered frames from Godot is expensive. A single 720p PNG is ~50KB.
At 30 agents × 1 frame/s = 1.5 MB/s. The `frames:{id}` channel is designed for
on-demand inspection only — subscribe to a specific agent's frame stream when
investigating a stuck state, then unsubscribe.

### Hot-Fix vs Cold-Restart

Interventions (`set_param`, `reparent`) modify the live simulation in-place
without restarting it. This is important because:
- Restarting the Godot scene might lose state that's hard to reproduce
- The other agents continue running unaffected
- The fix can be tested immediately

If the hot-fix doesn't work, `force_restart` kills and restarts the agent
from a known checkpoint.

## Testing

```bash
python examples/mobile_client.py ws://127.0.0.1:10993/mobile/v1 state-surveiller
```
