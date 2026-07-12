# Game Builder Tutorial — Build Your First Game

**Goal:** Go from "I have an idea" to a playable HTML5 game in 5 minutes.

This tutorial uses the Game Builder pipeline: natural language prompt ->
AI game plan -> GDScript -> export. All you need is Ollama running with
`gemma4:12b` (or any LLM configured via `GODOT_MCP_LLM_BASE_URL`).

---

## Step 1: Verify the pipeline works

```powershell
cd D:\Dev\repos\godot-mcp
just gb-smoke
```

Expected output:
```
  Result: 4/4 passed
```

This confirms: LLM is reachable, GamePlan parsing works, GDScript generation
works, and basic script validation passes. If this fails, check Ollama is
running (`ollama list`) and a model is available.

---

## Step 2: Design a game from a prompt

```powershell
uv run python -c "
import asyncio, json
from godot_mcp.game_builder.pipeline import design_game

concept = 'A 2D runner where you collect stars and avoid spikes. Arrow keys to move, space to jump.'
plan = asyncio.run(design_game(concept))
print(plan.to_json())
" > game_plan.json
```

This sends your concept to the LLM, which returns a structured GamePlan
with title, genre, scenes, scripts, hazards, scoring, and controls.

Open `game_plan.json` to see the AI's game design.

---

## Step 3: Generate the game scripts

```powershell
uv run python -c "
import asyncio, json
from godot_mcp.game_builder.pipeline import generate_game_logic
from godot_mcp.game_builder.plan import GamePlan

plan = GamePlan.from_json(open('game_plan.json').read())
result = asyncio.run(generate_game_logic(plan))
for name, data in result.get('scripts', {}).items():
    if data.get('generated'):
        print(f'Generated: {name} ({data[\"size_bytes\"]} bytes)')
    else:
        print(f'Failed: {name}: {data.get(\"error\", \"unknown\")}')
"
```

Each listed script is a complete GDScript file for Godot 4. The pipeline
automatically validates scripts with `gdlint` + `godot --check-only` and
repairs any errors via the LLM.

---

## Step 4: Create a Godot project

```powershell
# Create a new Godot project
mkdir my_first_game
cd my_first_game
```

Create `project.godot`:

```ini
[application]
config/name="My First Game"
run/main_scene="res://MainScene.tscn"

[display]
window/size/viewport_width=1024
window/size/viewport_height=600
```

Copy the generated scripts into `scripts/` and create the main scene.

---

## Step 5: Export to HTML5

```powershell
# If Godot 4 is installed and the bridge project is set up:
uv run python -c "
import asyncio
from godot_mcp.itch.service import godot_export_release_tool

result = godot_export_release_tool(target='web', game='custom', project_path='my_first_game')
print('Export:', 'OK' if result.get('success') else result.get('error'))
"
```

---

## Step 6: Preview in browser

```powershell
just gb-preview build_dir=build/little-game/custom/web
```

Opens the exported game in your default browser.

---

## Step 7: Ship to itch.io (optional)

```powershell
$env:BUTLER_API_KEY = "your_butler_key"
$env:ITCH_TARGET = "your_username/your-game"

uv run python -c "
import asyncio
from godot_mcp.itch.service import ship_to_itch

result = ship_to_itch(target='web', game='custom', project_path='my_first_game')
print('Shipped:', result.get('page_url', 'OK'))
"
```

---

## Full pipeline in one command

```powershell
just gb-smoke && echo "Pipeline verified"
```

Or use the game builder dashboard at `http://localhost:10992/game-builder`
for a visual step-by-step interface with live pipeline status.

---

## What to try next

| Concept | Genre | What it tests |
|---------|-------|---------------|
| "2D platformer with moving platforms" | platformer | Physics, hazard generation |
| "3D collect-a-thon with rotating coins" | 3D collect | 3D scenes, camera, lighting |
| "A story game where you talk to an old sage" | narrative | NPCs, dialogue generation |
| "Tower defense with 3 enemy types" | strategy | Multiple hazards, scoring |
