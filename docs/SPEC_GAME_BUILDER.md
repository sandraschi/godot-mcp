# SPEC: Game Builder Pipeline (v0.2.0)

**Repo**: godot-mcp  
**Status**: Draft → **Phase 1 implemented** (2026-05-25)  
**Last Updated**: 2026-05-25

## Overview

AI-native game creation pipeline: natural language → Marble 1.1 worlds → Godot 4.4 scene → GDScript logic → HTML5 game → itch.io. The user describes a game concept and the AI handles everything from world generation through shipping.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐
│  User Prompt │ →  │  AI Planning  │ →  │ World Gen     │ →  │ Godot     │
│  "cyberpunk  │    │  game plan    │    │ (worldlabs)   │    │ Scene     │
│   platformer"│    │  (JSON)       │    │               │    │ (import)  │
└──────────────┘    └──────────────┘    └──────────────┘    └───────────┘
                                                                  │
┌───────────┐    ┌──────────┐    ┌──────────────┐    ┌────────────┘
│  itch.io  │ ←  │  Export  │ ←  │  GDScript    │ ←  │
│  ship     │    │  HTML5   │    │  generation  │    │
└───────────┘    └──────────┘    └──────────────┘    └───────
```

## What Exists (Building Blocks)

All individual tools already work. This spec defines the orchestration layer.

| Capability | Tool / Module | Status |
|------------|--------------|--------|
| Generate Marble world from text | `bridge_call_tool(server, "generate_world_from_text")` | ✅ |
| Wait for world completion | `bridge_call_tool(server, "wait_for_world")` | ✅ |
| List/fetch Marble worlds | `fleet_worldlabs_get_world` | ✅ |
| Import GLB into Godot | `fleet_worldlabs_import_mesh` | ✅ |
| Create Godot cameras, lights | `godot_create_camera`, `godot_add_light` | ✅ |
| Set materials | `godot_set_material` | ✅ |
| AI code generation | `ai_generate_gdscript` (ctx.sample) | ✅ |
| Export HTML5 | `godot_export_release` | ✅ |
| Ship to itch.io | `ship_to_itch` | ✅ |
| Cross-server calls | `bridge_connect`, `bridge_call_tool` | ✅ |
| Workflow chaining | `workflow_run` (3 built-in) | ✅ |

## What's Missing

### Remaining work (post Phase 1)

| Item | Status |
|------|--------|
| Wire `generate_game_worlds` → `fleet_worldlabs_stage_mesh` | ✅ |
| Map Marble `world_id` into `compose_game_scene` | ✅ |
| Write generated scripts to project disk | ✅ |
| `templates/game-template/` bootstrap project | ✅ |
| Unit tests under `tests/game_builder/` | ✅ partial |
| REST `/api/v1/game-builder/*` + dashboard UI | ❌ Phase 2 |

### Module: `src/godot_mcp/game_builder/` (Phase 1 — done)

| File | Purpose |
|------|---------|
| `__init__.py` | Exports register function |
| `plan.py` | Game plan schema (Pydantic), plan validation |
| `pipeline.py` | Orchestrates the full pipeline |
| `tools.py` | MCP tools exposed to the agent |
| `prompts.py` | LLM system prompts for AI planning |

### New MCP Tools (6)

#### 1. `design_game(game_concept) → GamePlan`

**Input**: Natural language description of a game concept.  
**Uses**: `ctx.sample()` — sends the concept + planning prompt to the LLM.  
**Returns**: A structured `GamePlan` (JSON dict) containing worlds, scenes, scripts, mechanics, and export settings.

```python
# Signature
async def design_game(
    game_concept: Annotated[str, Field(description="Natural language game description.")],
    ctx: Context = None,
) -> dict:
```

**LLM output format** (the LLM populates this):

```json
{
    "title": "Cyberpunk Runner",
    "description": "Endless runner through neon-lit alleys. Dodge enemies, collect data packets.",
    "engine": "godot4",
    "viewport": "2d",
    "resolution": [1280, 720],
    "worlds": [
        {
            "id": "level_background",
            "name": "Neon Alley Background",
            "prompt": "A rain-slicked cyberpunk alley at night. Neon signs in blue, pink, green...",
            "model": "marble-1.1",
            "usage": "parallax_layer_1"
        }
    ],
    "scenes": [
        {"name": "Game", "type": "Node2D", "scripts": ["game.gd"]},
        {"name": "Player", "type": "CharacterBody2D", "scripts": ["player.gd"]},
        {"name": "Spawner", "type": "Node2D", "scripts": ["spawner.gd"]},
        {"name": "HUD", "type": "CanvasLayer", "scripts": ["hud.gd"]}
    ],
    "player": {"type": "runner", "speed": 600, "jump": -500, "gravity": 1200},
    "hazards": [{"name": "drone", "behavior": "sine", "speed": 200, "color": "#ff4444"}],
    "scoring": {"type": "distance", "unit_label": "m"},
    "controls": {"jump": "space", "slide": "down"},
    "scripts": [
        {"name": "game.gd", "description": "Main game loop, score tracking, death handling, restart on enter"},
        {"name": "player.gd", "description": "Auto-running right at 600px/s, jump on space, 3 lives"},
        {"name": "spawner.gd", "description": "Timer-based hazard spawning, increasing difficulty"},
        {"name": "hud.gd", "description": "CanvasLayer with score, lives, game over overlay"}
    ],
    "assets": ["lives_icon.png", "explosion_particle.png"],
    "lighting": {"directional": true, "ambient_color": "#1a1a2e", "intensity": 0.4},
    "camera": {"position": [0, 0, 10], "fov": 75},
    "export": {"target": "web", "resolution": [1280, 720]}
}
```

#### 2. `generate_game_worlds(game_plan_json, worldlabs_url) → dict`

Generates all Marble worlds defined in the game plan. Calls worldlabs-mcp via bridge for each world.

```python
async def generate_game_worlds(
    game_plan: Annotated[str, Field(description="JSON game plan from design_game.")],
    worldlabs_url: Annotated[str, Field(description="worldlabs-mcp bridge URL (default: http://127.0.0.1:10865).")] = "http://127.0.0.1:10865",
):
```

**Pipeline**:
1. Parse game plan JSON
2. For each world in `plan.worlds`:
   - Call `bridge_call_tool(worldlabs_url, "generate_world_from_text", {"text_prompt": world.prompt, "model": world.model})`
   - Store operation_id
3. For each operation: poll `wait_for_world` until all complete
4. Return world_id → asset URL map

#### 3. `compose_game_scene(game_plan_json) → dict`

Assembles the Godot scene from the game plan. Imports worlds, creates scene structure.

```python
async def compose_game_scene(
    game_plan: Annotated[str, Field(description="JSON game plan + world IDs from generate_game_worlds.")],
):
```

**Pipeline**:
1. Import each world's GLB into Godot via `fleet_worldlabs_import_mesh`
2. Position worlds (stack, side-by-side, or as parallax layers)
3. Apply scene setup: camera, lights via `prefab_apply("standard_lighting")`
4. Create scene structure: add node containers for Player, Spawner, HUD
5. Save scene

#### 4. `generate_game_logic(game_plan_json) → dict`

Generates all GDScript files defined in the game plan. Uses `ai_generate_gdscript` which calls `ctx.sample()`.

```python
async def generate_game_logic(
    game_plan: Annotated[str, Field(description="JSON game plan from design_game.")],
    ctx: Context = None,
):
```

**Pipeline**:
1. Parse game plan JSON
2. For each script in `plan.scripts`:
   - Build a prompt from the script description + game context
   - Call `ai_generate_gdscript(specification=prompt)`
   - Store generated code
3. Write .gd files to project (via `_write_gdscript_file`)
4. Return summary of generated scripts

#### 5. `export_and_ship(game_plan_json, game_project_path, itch_target) → dict`

Exports the Godot project to HTML5 and ships to itch.io.

```python
async def export_and_ship(
    game_plan: Annotated[str, Field(description="JSON game plan from design_game.")],
    game_project_path: Annotated[str, Field(description="Godot project directory path.")],
    itch_target: Annotated[str, Field(description="itch.io user/game slug.")] = "",
    channel: Annotated[str, Field(description="Butler channel (default: html).")] = "html",
):
```

**Pipeline**:
1. Parse plan for export settings
2. Call `godot_export_release` with target game
3. If `itch_target` specified: call `ship_to_itch`

#### 6. `build_game(game_concept, worldlabs_url) → dict`

The master tool. Calls design_game → generate_game_worlds → compose_game_scene → generate_game_logic → export_and_ship. A single high-level entry point.

```python
async def build_game(
    game_concept: Annotated[str, Field(description="Natural language game description.")],
    worldlabs_url: Annotated[str, Field(description="worldlabs-mcp bridge URL.")] = "http://127.0.0.1:10865",
    ship: Annotated[bool, Field(description="Also ship to itch.io?")] = False,
    ctx: Context = None,
):
```

**Returns**:  
```json
{
  "success": true,
  "game_plan": {...},
  "worlds": {"level_background": "a7936174-..."},
  "scene": {"nodes": 12, "meshes": 3},
  "scripts": ["game.gd (4.2KB)", "player.gd (2.1KB)", "hud.gd (1.8KB)"],
  "export": {"path": "build/little-game/custom/Web/", "size_kb": 4200},
  "itch_url": "https://sandraschi.itch.io/game-name"  // if ship=true
}
```

## Webapp: Game Builder Page

### New Page: `webapp/src/pages/game-builder.tsx`

Route: `/game-builder`

**Layout**: Two-column design — left panel for prompt input and plan preview, right panel for build status pipeline.

**States**:
1. **Input**: Textarea for game concept + "Design Game" button → calls `design_game`
2. **Plan Review**: Shows the LLM-generated game plan (worlds, scenes, scripts) with edit capability. "Approve & Build" button.
3. **Build Pipeline**: Progress bar with live step status (Generate Worlds → Import → Compose Scene → Generate Logic → Export → Ship). Each step shows logs.
4. **Result**: Link to play the game, share URL, itch.io page.

**Key components**:
- `ConceptInput` — large textarea with examples ("an endless runner...")
- `PlanPreview` — read-only JSON preview of the game plan
- `PipelineProgress` — stepper component showing 6 steps with status dots
- `StepLog` — expandable log viewer for each pipeline step
- `GameResult` — play button, itch.io link, share button

## Integration Points

### worldlabs-mcp Requirements

worldlabs-mcp must expose these tools via its REST bridge (`POST /api/v1/control/tool`):

| Tool | Status |
|------|--------|
| `generate_world_from_text` | ✅ Already available |
| `generate_world_from_image` | ✅ Already available |
| `wait_for_world` | ✅ Already available |
| `list_worlds` | ✅ Already available |
| `get_world` | ✅ Already available |

### godot-mcp Requirements

godot-mcp must have Godot running with the bridge active (port 9080). The custom game project must exist on disk. A template project (`templates/game-template/`) provides the baseline project.godot + MCPBridge autoload.

### Environment Variables

| Variable | Default | Required For |
|----------|---------|-------------|
| `WORLDLABS_BRIDGE_URL` | `http://127.0.0.1:10865` | World gen |
| `GODOT_PATH` | auto-detect | Export |
| `BUTLER_API_KEY` | — | Ship to itch.io |
| `ITCH_TARGET` | — | Ship to itch.io |

## Implementation Order

### Phase 1: Core Pipeline (this sprint)
1. Create `src/godot_mcp/game_builder/` module
2. `plan.py` — GamePlan Pydantic model + validation
3. `prompts.py` — System prompts for LLM planning
4. `pipeline.py` — Full pipeline orchestration
5. `tools.py` — Register all 6 MCP tools
6. Wire into `server.py` registration

### Phase 2: Webapp (next sprint)
1. `webapp/src/pages/game-builder.tsx` — UI page
2. REST routes at `POST /api/v1/game-builder/design`, etc.
3. Live SSE progress streaming

### Phase 3: Templates & Bundles
1. `templates/game-template/` — baseline Godot project with MCPBridge autoload
2. Extend MCPB bundles to include actual .gd/.tscn/.asset files (not just tool sequences)
3. Pre-built game genre templates (platformer, runner, top-down, FPS)

## Error Handling & Recovery

| Error | Recovery |
|-------|----------|
| worldlabs-mcp unreachable | Retry 3x with exponential backoff. Return partial result with `worlds_pending`. |
| Marble world generation fails (402 credits) | Skip world, use fallback dark background. Log warning. |
| Godot bridge disconnected | Auto-connect. Retry 2x. |
| `ctx.sample()` unavailable | Return `[sampling_unavailable: true]`, let caller handle fallback (use offline prompt templates). |
| itch.io push fails (auth) | Return success for export, error details for ship. |
| Export fails (missing Godot path) | Return error with actionable message: "Set GODOT_PATH env var". |

## Tests

### Unit Tests
- `tests/game_builder/test_plan.py` — GamePlan validation, defaults
- `tests/game_builder/test_prompts.py` — System prompt formatting
- `tests/game_builder/test_pipeline.py` — Pipeline step execution with mocked bridge

### Integration Test (manual)
1. Start worldlabs-mcp on port 10865
2. Start godot-mcp with Godot on port 9080
3. Run: `build_game(game_concept="A simple 2D platformer with one level and jumping")`
4. Verify: HTML5 game opens in browser with working player controller

## Open Questions

1. **Project bootstrap**: Should `compose_game_scene` create the Godot project from scratch, or require an existing project? Proposal: ship a `templates/game-template/` project that has MCPBridge autoload + empty main.tscn. The pipeline writes scripts into that project.
2. **Visual quality**: SPZ splats can't render in Godot. Should we use collider GLBs (low-poly but walkable) or panoramas (2D but photorealistic)? Proposal: collider GLB for 3D games, panorama for 2D parallax backgrounds.
3. **LLM sampling dependency**: What if the MCP client doesn't support sampling? Proposal: fallback to pre-written game templates that the user can customize via parameters.
