# App #3 — Pocket Vibe-Architect (Procedural Generative Deck)

```
Intent type:  "pocket-architect"
Endpoints:    WS /mobile/v1  |  POST /mobile/v1/command
Key pattern:  Prompt → Generate → Review → Approve/Reject/Tweak
```

## Concept

A **minimalist, prompt-driven mobile interface** for steering Goliath's
generative pipeline. You type (or speak) a high-level creative direction —
"generate a dark-synth modular sci-fi corridor tilemap" — and the Pocket
Architect decomposes it into a multi-stage generation pipeline on Goliath.

This is the purest expression of the **mobile as adjudicator** pattern:
the heavy lifting (asset generation, scene composition, GDScript writing,
syntax validation) happens on Goliath's dual 4090s. The phone serves as
a high-bandwidth approval interface — presenting generated results as
screenshots or video clips, accepting thumbs-up/down, and feeding
refinement prompts back into the generation loop.

## User Experience

```
1. User opens the app, sees a clean text input at the bottom
2. User types: "generate a dark-synth sci-fi corridor with flickering panels"
3. App sends generation intent to Goliath
4. Goliath:
   a. Calls ai_generate_gdscript() for the flickering emission shader
   b. Searches the artifact depot for sci-fi corridor tiles
   c. Imports and positions tiles in a new Godot scene
   d. Applies the generated shader to emission panels
   e. Exports a Web build for preview
   f. Register the result as a new artifact
5. iOS receives progress events: 30% → 60% → 90% → 100%
6. iOS shows a screenshot thumbnail + GDScript preview
7. User swipes: approve (save to depot) or reject (discard)
   or types refinement: "make the corridor wider, add neon strips"
8. Cycle repeats at step 3 with the feedback incorporated
```

## Data Models

### Generation Intent (iOS → Goliath)

```json
{
  "type": "intent",
  "app": "pocket-architect",
  "payload": {
    "prompt": "dark-synth modular sci-fi corridor tilemap with auto-flickering emission panels",
    "mode": "environment",
    "constraints": {
      "style": "dark-synth",
      "poly_count_target": 50000,
      "resolution": "medium",
      "reference_assets": ["artifact:corridor_tile_01", "artifact:panel_emissive"]
    },
    "outputs_requested": ["screenshot", "gdscript"]
  }
}
```

### Progress Event (Server → iOS, via subscription)

```json
{
  "type": "event",
  "payload": {
    "channel": "progress",
    "data": {
      "generation_id": "gen_001",
      "step": "generating_scripts",
      "pct": 30,
      "message": "Writing emission shader GDScript..."
    }
  }
}
```

### Generation Result (Goliath → iOS)

```json
{
  "type": "result",
  "correlation_id": "msg-002",
  "payload": {
    "generation_id": "gen_001",
    "status": "complete",
    "mode": "environment",
    "artifacts": [
      {
        "type": "screenshot",
        "url": "artifact:dark_corridor_screenshot_01",
        "thumbnail_b64": "iVBORw0KGgo..."
      },
      {
        "type": "gdscript",
        "artifact_id": "artifact:emission_shader_01",
        "size_bytes": 2847
      }
    ],
    "artifact_ids": ["artifact:emission_shader_01", "artifact:dark_corridor_01"],
    "summary": "Corridor tilemap generated: 12 tiles, 3 emission shaders, 2 light fixtures"
  }
}
```

### Approval Action (iOS → Goliath)

```json
{
  "type": "intent",
  "app": "pocket-architect",
  "payload": {
    "intent_type": "approve",
    "generation_id": "gen_001",
    "feedback": null
  }
}
```

## Intent Catalog

| Intent | Purpose | Backend Action |
|--------|---------|----------------|
| `generate:environment` | Full scene generation from prompt | `design_game` → `generate_game_worlds` → `compose_game_scene` |
| `generate:asset` | Single asset generation/import | `artifact_search` → `godot_import_glb` → `godot_set_material` |
| `generate:ui_theme` | UI theme generation | `godot_set_config` → `prompt_execute("material_advisor")` |
| `generate:behavior` | GDScript behavior generation | `ai_generate_gdscript` → bridge `game_eval` |
| `generate:gdscript` | Quick GDScript generation (no scene) | `sampling.service.sample_text()` |
| `approve` | Save generation as permanent artifact | `artifact_register` |
| `reject` | Discard generation (delete temp artifact) | `artifact_delete` |
| `tweak` | Re-run with modified constraints | `prompt_execute` → re-run generative chain |

## Output Types

| Type | Format | Size | When |
|------|--------|------|------|
| `screenshot` | base64 PNG thumbnail | ~5-50 KB | Always (fastest to produce) |
| `video_clip` | base64 MP4 clip | ~200-500 KB | Optional (needs Godot export) |
| `scene_file` | `.tscn` artifact in depot | ~10-100 KB | On approve |
| `gdscript` | `.gd` artifact in depot | ~1-10 KB | When scripts are requested |

## Mode-Specific Behavior

### `mode: "environment"`

The full game generation pipeline:
1. `design_game(prompt)` — LLM decomposes the prompt into a structured `GamePlan`
   with worlds, scenes, scripts, lighting, camera, and player configuration
2. Settings are returned to the iOS client for preview before committing
3. On confirm: `generate_game_worlds` → `compose_game_scene` → `generate_game_logic`

### `mode: "gdscript"`

Lightweight code generation without scene setup:
1. Calls `sampling.service.sample_text()` with the prompt
2. Returns the generated GDScript directly
3. Useful for quick prototyping: "write a smooth follow camera script"

### `mode: "asset"`

Asset search and import:
1. Searches the artifact depot with `artifact_search(query)`
2. If found: imports the asset into the current scene via `godot_import_glb`
3. If not found: returns "no matching assets" with suggestions

## Server-Side Dispatch

Found in `ws_gateway.py:_handle_generation_intent()` and
`mobile_command.py:MobileDispatcher._dispatch_generation()`.

The dispatch:

1. Validates against `GenerationIntentPayload` Pydantic model
2. For `mode: "gdscript"`: calls `sample_text()` directly — this is the fastest
   path (no Godot interaction needed)
3. For `mode: "environment"`: calls `pipeline.design_game()` which uses LLM
   sampling to create a structured game plan

```python
# mobile_command.py:_dispatch_generation()
if intent.mode == "gdscript":
    code = await sample_text(None, prompt=f"Write GDScript: {intent.prompt}")
    return MobileDispatchResult(success=True, data={"code": code, "mode": "gdscript"})

if intent.mode == "environment":
    plan = await pipeline.design_game(intent.prompt)
    return MobileDispatchResult(
        success=True,
        data={"plan": json.loads(plan.to_json()), "mode": "environment"},
        message=f"Game: {plan.title} ({plan.genre or 'arcade'})"
    )
```

## The Approve/Reject/Tweak Loop

The Pocket Architect's core interaction is a **human-in-the-loop approval cycle**:

```
┌─────────┐    prompt     ┌──────────┐  progress events  ┌────────────┐
│  iOS     │──────────────►│  Goliath  │─────────────────►│  iOS shows  │
│  Client  │               │  Generator│                  │  preview    │
│          │◄──────────────┤           │◄─────────────────┤             │
│          │  result       │           │  subscribe      │             │
├─────────┤               └──────────┘                  └─────────────┤
│ approve │──► artifact_register → artifact is saved to depot         │
│ reject  │──► artifact_delete  → temp artifacts are cleaned up       │
│ tweak   │──► prompt_execute + re-run pipeline with modified params  │
└─────────┘                                                            │
```

The `tweak` action accepts optional `feedback` text and `tweak_params` to
guide the next generation cycle. This creates a convergent loop where each
iteration gets closer to the user's intent.

## Testing

```bash
# Quick GDScript generation:
python examples/mobile_client.py ws://127.0.0.1:10993/mobile/v1 pocket-architect

# REST fallback (gdscript mode):
curl -X POST http://127.0.0.1:10993/mobile/v1/command \
  -H "Content-Type: application/json" \
  -d '{
    "type": "intent",
    "app": "pocket-architect",
    "payload": {
      "prompt": "smooth follow camera for 3D platformer",
      "mode": "gdscript",
      "outputs_requested": ["gdscript"]
    }
  }'
```
