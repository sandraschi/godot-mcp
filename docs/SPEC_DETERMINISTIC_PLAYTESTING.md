# Deterministic Playtesting — Implementation Plan

**Source inspiration:** satelliteoflove/godot-mcp
**Status:** All phases implemented (2026-07-15)
**Current gap (closed):** Our agent now has frozen clock, step-until, rich input, and structured state digest.

---

## Phase 1: Rich Game Input ✅

**Goal:** Move beyond basic key press/release to full game controller input.

### Current state (`mcp_bridge.gd` lines 795-821)

```gdscript
# Only key press/release via InputEventKey
var event := InputEventKey.new()
event.keycode = OS.find_keycode(key_name)
event.pressed = pressed
Input.parse_input_event(event)
```

### What to add

**New action types in `simulate_input` command:**

```gdscript
# Action press with analog strength
{"action": "jump", "strength": 0.5}  # Input.action_press("jump", 0.5)

# Joypad axis
{"joypad": {"device": 0, "axis": 0, "value": -0.8}}  # InputEventJoypadMotion

# Joypad button
{"joypad": {"device": 0, "button": 0, "pressed": true}}  # InputEventJoypadButton

# Mouse-look (relative)
{"mouse_look": {"dx": 15, "dy": -3}}  # InputEventMouseMotion

# Mouse button
{"mouse_button": {"button": 1, "pressed": true, "position": {"x": 960, "y": 540}}}

# Raw text
{"type": "text", "text": "hello"}
```

### Files to change

| File | Change |
|------|--------|
| `src/godot_mcp/bridge/mcp_bridge.gd` | Extend `_cmd_simulate_input` to handle 6 input types (action, joypad_motion, joypad_button, mouse_motion, mouse_button, text) |
| `src/godot_mcp/tools/core_tools.py` | Update `godot_simulate_input` docstring and types. Deprecate flat key-only format. |

### Verification

```python
await godot_simulate_input([
    {"action": "move_left", "strength": 1.0},
    {"action": "jump", "strength": 0.5},
    {"mouse_look": {"dx": 45, "dy": -10}},
    {"type": "text", "text": "hello world"},
])
```

### Risk

Low. No state changes, just widening the input format. Backward-compatible (old `{"key":...}` format still works).

---

## Phase 2: Structured Runtime State (Digest) ✅

**Goal:** Let agents read live game state as structured JSON without dumping the full scene tree.

### Current state

- `read_scene_tree` returns **everything** recursively — expensive, noisy, wastes tokens
- No opt-in lightweight observation mechanism
- Agent has to scrape full tree + guess what's instrumented

### What to add

**GDScript conventions** (in `mcp_bridge.gd`):

1. **`mcp_watch` group:** Nodes added to this group return the union of public property values:
   - `position`, `rotation`, `scale` (if Spatial)
   - `visible` (if CanvasItem)
   - `velocity` (if CharacterBody/RigidBody)
   - `health`, `current_state` — if the node has these custom properties

2. **`_mcp_state() -> Dictionary` method:** If a node defines this method, the bridge calls it instead of the default property collection. This lets game-specific scripts expose exactly what matters:
   ```gdscript
   func _mcp_state() -> Dictionary:
       return {
           "health": health,
           "ammo": ammo,
           "current_weapon": weapon_name,
           "ai_state": fsm.current_state.name,
       }
   ```

**New GDScript bridge actions:**

| Action | Description |
|--------|-------------|
| `state_digest` | Return structured state for all nodes in `mcp_watch` group (or a named subset) |
| `state_watch_add` | Add a node to `mcp_watch` group by path |
| `state_watch_remove` | Remove a node from `mcp_watch` group |

**New Python tool:**

```python
async def godot_state_digest(
    node_names: list[str] | None = None,  # filter to specific nodes
    ctx: Context = None,
) -> dict:
    """Read structured runtime state from instrumented game nodes.

    Returns lightweight JSON for nodes in the mcp_watch group that define
    _mcp_state() or expose readable properties. Cheaper than read_scene_tree.
    """
```

### Files to change

| File | Change |
|------|--------|
| `src/godot_mcp/bridge/mcp_bridge.gd` | Add `state_digest`, `state_watch_add`, `state_watch_remove` commands. Implement `_collect_node_state(node)` helper |
| `src/godot_mcp/tools/core_tools.py` | Add `godot_state_digest` tool. Annotate `_READ_ONLY` |
| `src/godot_mcp/tools/__init__.py` | Auto-registered via `reg_core` — no change needed |

### Verification

```python
# After setting up: add Enemy to mcp_watch group, define _mcp_state()
await godot_state_digest()
# → {"nodes": {"Enemy": {"health": 75, "ammo": 12, "ai_state": "patrol"}}}
```

### Risk

Low-medium. New convention, no existing code broken. Need to document the `_mcp_state()` pattern clearly so game devs know to opt in.

---

## Phase 3: Frozen Clock + Step-Until ✅

**Goal:** Deterministic playtesting — freeze the game clock, advance frame-by-frame or until a condition is true.

### Current state

- No clock control in the bridge at all
- Agent must `await asyncio.sleep(2)` for real-time elapse — non-deterministic, slow, races the renderer
- No way to verify game state at a specific frame boundary

### What to add

**GDScript bridge state machine:** Add a `_stepping` state variable that controls the game loop:

```gdscript
enum PlaytestState { RUNNING, FROZEN, STEPPING }
var _playtest_state := PlaytestState.RUNNING
var _step_queue: Array[Dictionary] = []  # deferred step operations
var _step_pending := 0  # frames remaining to step
```

**Mechanism in `_process(delta)`:**

```gdscript
func _process(delta):
    if _playtest_state == PlaytestState.FROZEN:
        return  # Engine.time_scale = 0, skip everything
    elif _playtest_state == PlaytestState.STEPPING:
        _step_pending -= 1
        if _step_pending <= 0:
            _playtest_state = PlaytestState.FROZEN
            _send_event("step_complete", {"frame": Engine.get_frames_drawn()})
            return
    # normal processing continues
```

**New GDScript bridge actions:**

| Action | Params | Description |
|--------|--------|-------------|
| `game_time_freeze` | none | `Engine.time_scale = 0`, mark FROZEN |
| `game_time_unfreeze` | none | `Engine.time_scale = 1`, mark RUNNING |
| `game_time_step` | `frames: int` (default 1) | Step N frames then re-freeze. Returns post-step state |
| `game_time_step_until` | `condition: str` (GDScript expression), `timeout_frames: int` (max 3600) | Step one frame at a time, evaluate `condition` each frame. When truthy, re-freeze and return. If timeout, return error |

**`step_until` implementation:**

```gdscript
func _cmd_game_time_step_until(request_id: String, params: Dictionary):
    var condition := params.get("condition", "")
    var timeout_frames := params.get("timeout_frames", 3600)
    if condition.is_empty():
        _send_error("step_until requires 'condition' GDScript expression", request_id)
        return
    _step_until_request_id = request_id
    _step_until_condition = condition
    _step_until_timeout = timeout_frames
    _step_until_counter = 0
    _playtest_state = PlaytestState.STEPPING
    _step_pending = timeout_frames  # will stop early when condition met
    # response will be sent from _process when condition hits or timeout
```

**New Python tools:**

```python
async def godot_game_time(
    action: Literal["freeze", "unfreeze", "step"],
    frames: int = 1,
    ctx: Context = None,
) -> dict:
    """Control the game clock for deterministic playtesting.
    - freeze: pause the game loop (time_scale = 0)
    - unfreeze: resume normal game speed
    - step: advance N frames then re-freeze (requires frozen state)
    """

async def godot_step_until(
    condition: str,
    timeout_frames: int = 3600,
    ctx: Context = None,
) -> dict:
    """Step the game frame-by-frame until a GDScript expression is true.

    Example:
    await godot_step_until(condition="get_node('Player').position.y < -10")
    # → Player fell off the map — agent can now screenshot, verify, react
    """
```

### New bridge events

To support the polling-free step-until flow, the bridge sends **events** (non-response messages):

```json
{"type": "event", "event": "step_complete", "data": {"frame": 12345, "condition_met": true}}
```

The Python side reads these from the socket between requests (already possible with the `_recv_line` buffering pattern). This avoids blocking the MCP tool call for potentially hundreds of frames.

### Files to change

| File | Change |
|------|--------|
| `src/godot_mcp/bridge/mcp_bridge.gd` | Add `PlaytestState` enum, `_process` clock control, `game_time_freeze`, `game_time_unfreeze`, `game_time_step`, `game_time_step_until`, event sending |
| `src/godot_mcp/services/godot_bridge.py` | Add `event_callbacks` dict to `GodotBridge` so the Python side can subscribe to bridge events. Expose `poll_event()` or callback registration |
| `src/godot_mcp/tools/core_tools.py` | Add `godot_game_time` and `godot_step_until` tools |
| `src/godot_mcp/tools/__init__.py` | Auto-registered — no change needed |

### Verification

```python
await godot_game_time(action="freeze")
# → clock stopped

await godot_simulate_input([{"action": "jump", "strength": 1.0}])
# → input queued in the frozen frame

await godot_step_until(condition="get_node('Player').is_on_floor()")
# → advances frame-by-frame until Player lands, then re-freezes

await godot_capture_viewport()
# → screenshot at the exact landing frame
```

### Risk

Medium. The stepping loop in `_process` is straightforward but edge cases exist:
- Physics may need `_physics_process` calls too — wrap both
- `step_until` with a never-true condition must timeout gracefully
- Input events queued during freeze must survive the step boundary (use `Input.parse_input_event` which queues them)
- Event channel between GDScript and Python needs careful threading (Python reads events during idle periods between tool calls)

---

## Rollout Order

| Phase | Effort | Value | Risk | Status |
|-------|--------|-------|------|--------|
| 1 — Rich Input | 1-2 days | Medium | Low | ✅ Done 2026-07-15 |
| 2 — State Digest | 2-3 days | Medium | Low | ✅ Done 2026-07-15 |
| 3 — Deterministic Playtesting | 4-5 days | High | Medium | ✅ Done 2026-07-15 |

Each phase is independently shippable and adds value on its own. Phase 2 builds naturally on Phase 1 (the state digest reads what input changed). Phase 3 is the capstone that makes the first two phases deterministic.

---

## Reference Architecture (satelliteoflove/godot-mcp)

Their tool names and concepts for cross-reference:

| Their tool | Our equivalent | Gap |
|------------|----------------|-----|
| `godot_input` (action, joypad, raw keys, mouse-look, text) | `godot_simulate_input` (keys only) | Phase 1 |
| `godot_runtime_state` (digest, watch, signal timelines) | `godot_read_scene_tree` (full dump, no opt-in) | Phase 2 |
| `godot_game_time` (freeze, step, step-until) | None | Phase 3 |

Their deterministic playtesting flow:

```
godot_editor_edit   run frozen=true           # boot frozen at frame 0
godot_exec          GameState.wave = 3        # set up scenario
godot_game_time     step_until "boss_count > 0"  # advance until spawn
godot_runtime_state digest                    # read positions (no tokens)
godot_game_time     step 500ms + dodge input  # play the moment
godot_editor_read   screenshot_game           # screenshot only when needed
```

We will match this exact flow.
