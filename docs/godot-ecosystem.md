# Godot Ecosystem & Secondary Tools

**Updated:** 2026-07-11

Godot has a rich ecosystem of standalone tools, linters, formatters, and
third-party integrations. Godot MCP integrates them directly into the game
builder pipeline — either as CLI checks (gdlint, godot --check-only), as
MCP bridge tools (blender-mcp asset import), or as auto-installable addons.

---

## 1. Plugin Installation — How It Works

Godot plugins (addons) live in a project's `addons/<name>/` directory.
The MCP server can install them programmatically:

**`install_community_plugin` MCP tool:**
- Downloads the plugin archive from GitHub (latest release or repo zip)
- Extracts to `res://addons/<plugin_name>/`
- Creates/updates `plugin.cfg`
- Returns the addon path

Not every plugin listed here is already wired into `install_community_plugin` —
the tool currently supports the bridge addon. Adding a new one is a
one-line URL addition in `addon_tools.py`.

---

## 2. Curated Plugin Catalog — Power Ranking

Ranked by impact on AI-assisted game development (what's most useful in
a prompt-to-game pipeline).

### Tier 1: Ship with godot-mcp

| Plugin | Repo | What | Pipeline use |
|--------|------|------|-------------|
| **MCP Bridge** | (built-in) `bridge/mcp_bridge.gd` | TCP server in Godot for MCP commands | Core — all engine tools |
| **gdtoolkit** | [Scony/godot-gdscript-toolkit](https://github.com/Scony/godot-gdscript-toolkit) | gdlint + gdformat + gdparse + gdradon | Script validation after generation |

### Tier 2: Highest Value for Generated Games

| Plugin | Repo | Why powerful | When to auto-install |
|--------|------|-------------|---------------------|
| **Dialogic** | [dialogic-godot/dialogic](https://github.com/dialogic-godot/dialogic) | Visual dialogue + timeline system. Write branching conversations from a GamePlan narrative field. GamePlan describes a story → dialogic timeline is generated | GamePlan has `narrative` or `story` field |
| **Godot Behavior Tree** | [viniciusgerevini/godot-behavior-tree](https://github.com/viniciusgerevini/godot-behavior-tree) | BT-based AI for NPCs. GamePlan hazards describe enemy behavior → BT JSON is generated | GamePlan has `hazards` with AI patterns |
| **Terrain3D** | [TokisanGames/Terrain3D](https://github.com/TokisanGames/Terrain3D) | High-performance 3D terrain with painting, holes, LOD. Alternative to Marble worlds for open-world games | GamePlan `viewport == "3d"` and genre is open-world |
| **Godot Voxel** | [Zylann/godot_voxel](https://github.com/Zylann/godot_voxel) | Voxel terrain engine (infinite, editable). Marble worlds are great for fixed scenes — voxel is better for Minecraft-like games | GamePlan genre is survival/building/block |
| **Aseprite Wizard** | [viniciusgerevini/godot-aseprite-wizard](https://github.com/viniciusgerevini/godot-aseprite-wizard) | Import Aseprite sprite sheets with animations. Changes to `.ase` files auto-reimport. Generated 2D games need sprites | GamePlan `viewport == "2d"` |

### Tier 3: Polish + Production Value

| Plugin | Repo | What | When |
|--------|------|------|------|
| **GUT** (Godot Unit Test) | [bitwes/Gut](https://github.com/bitwes/Gut) | GDScript unit test framework. Run tests after `generate_game_logic` to verify script behavior | Always — test-first game gen |
| **Godot Splash** | [frogfrank/Godot_Splash](https://github.com/frogfrank/Godot_Splash) | Screen-space fluid rendering for particle effects | GamePlan has `water` or `fluid` |
| **FMOD Integration** | [svartmann/Godot-FMOD-Integration](https://github.com/svartmann/Godot-FMOD-Integration) | FMOD audio middleware for spatial audio, DSP, snapshots | GamePlan includes `soundtrack` or `sfx` |
| **Godot Steam Audio** | [godotengine/godot-steam-audio](https://github.com/godotengine/godot-steam-audio) | Valve's spatial audio — physics-based sound propagation | 3D games with audio emphasis |
| **Godot XR Tools** | [GodotVR/godot-xr-tools](https://github.com/GodotVR/godot-xr-tools) | AR/VR interaction toolkit (grabbing, teleport, UI) | GamePlan `viewport == "xr"` |

### Tier 4: Publishing

| Plugin | Repo | What | When |
|--------|------|------|------|
| **Godot iOS Plugins** | [godotengine/godot-ios-plugins](https://github.com/godotengine/godot-ios-plugins) | App Store deployment plugins | `ship_target == "ios"` |
| **Godot Android Plugins** | [godotengine/godot-android-plugins](https://github.com/godotengine/godot-android-plugins) | Google Play deployment plugins | `ship_target == "android"` |

---

## 3. gdtoolkit (Linter + Formatter + Parser)

[github.com/Scony/godot-gdscript-toolkit](https://github.com/Scony/godot-gdscript-toolkit)

Standalone Python package (`gdtoolkit>=4.5,<5`) providing four tools that
operate on GDScript files without needing the Godot engine running.

### gdlint — GDScript Linter

Checks GDScript for style violations, naming conventions, and anti-patterns.
Configurable via `gdlintrc` in the project root.

**Rules checked (28):**

| Category | Rules |
|----------|-------|
| **Naming** | class-name, class-variable-name, function-name, constant-name, enum-name, enum-element-name, signal-name, loop-variable-name, function-argument-name, function-variable-name, subclass-name, class-load-variable-name, load-constant-name, function-preload-variable-name |
| **Structure** | class-definitions-order, max-file-lines (1000), max-public-methods (20), max-returns (6), function-arguments-number (10) |
| **Style** | max-line-length (100), tab-characters (tabs required), trailing-whitespace, mixed-tabs-and-spaces, unnecessary-pass |
| **Correctness** | expression-not-assigned, duplicated-load, comparison-with-itself, no-elif-return, no-else-return, unused-argument |

**Usage in pipeline:** `_validate_and_repair_scripts()` runs gdlint as the
first validation pass after `generate_game_logic` (fast, ~50ms per script).
Errors are combined with `godot --check-only` output for LLM repair.

### gdformat — GDScript Formatter

Uncompromising formatter (Black-style, one true way). Configurable options:
max line length, tabs vs spaces. Idempotent.

Usage:
```
gdformat path/to/script.gd
gdformat --check path/to/project/   # CI mode
gdformat --diff path/to/script.gd   # preview changes
```

### gdparse — GDScript Parser

Parses GDScript into an AST (abstract syntax tree). Useful for static
analysis tooling and code generation verification.

### gdradon — Code Complexity

Converts GDScript to Python and runs `radon` to compute cyclomatic
complexity. Identifies functions that are too complex to maintain.

### gd2py — GDScript to Python Converter

Transforms GDScript into syntactically valid (but not runnable) Python.
Enables Python static analysis tools (mypy, pylint, radon) on GDScript
code.

---

## 4. Godot Engine Built-in CLI Tools

The Godot 4 engine itself ships several CLI flags useful in pipelines:

| Flag | Purpose | Used in godot-mcp |
|------|---------|-------------------|
| `--headless --check-only --script <file>` | Compile-check a GDScript file | Yes — validation + repair |
| `--headless --export-release <preset> <path>` | Headless export to HTML5/Windows | Yes — `godot_export_release` |
| `--headless --import` | Import project assets | Yes — `demo-import` |
| `--path <dir>` | Set project root | Yes — bridge launch, export |
| `--verbose` | Detailed console output | Yes — bridge launch |
| `--editor` | Launch editor (vs headless) | No (user opens manually) |
| `--render-method <forward|mobile|gl_compatibility>` | Force renderer | No |

---

## 5. Fleet Cross-Repo Pipeline

These are MCP servers in the fleet that godot-mcp integrates with directly:

| Server | Port | Pipeline role | Tools |
|--------|------|---------------|-------|
| **blender-mcp** | 10849 | GLB/VRM/GLTF mesh export for import | `godot_import_glb` |
| **qcad-mcp** | 10967 | DXF floor plan -> STL extrusion | `godot_import_stl` |
| **freecad-mcp** | 10945 | BIM/IFC -> STL, FluidX3D CFD coupling | `godot_load_velocity_field` |
| **worldlabs-mcp** | 10865 | Marble 3D world generation | `generate_game_worlds`, `fleet_worldlabs_*` |
| **steam-mcp** | 11020 | SteamPipe upload | `ship_to_steam_*` |
| **itch.io** | native | Butler CLI for itch.io publishing | `ship_to_itch`, `itch_push` |

Pipeline flow:
```
blender-mcp -----> godot_import_glb ---------+
qcad-mcp --------> godot_import_stl ---------+---> Godot scene
freecad-mcp -----> godot_load_velocity_field-+
worldlabs-mcp ---> compose_game_scene -------+
                                       generate_game_logic (gdlint + --check-only)
                                                  |
                                                  v
                                          godot_export_release
                                                  |
                                                  v
                                     steam-mcp (Steam)  or  itch.io
```

---

## 6. Extending the Ecosystem

### Adding a new plugin to `install_community_plugin`

In `src/godot_mcp/tools/addon_tools.py`, add a new entry to the `PLUGIN_REGISTRY`:

```python
PLUGIN_REGISTRY = {
    "dialogic": {
        "repo": "dialogic-godot/dialogic",
        "path_in_zip": "addons/dialogic/",
        "description": "Visual dialogue system for Godot",
    },
    ...
}
```

The tool handles: download latest release -> extract -> copy to `addons/` -> enable.

### Adding a new tool to the validation pipeline

1. Install the tool as a dev dependency in `pyproject.toml`
2. Add a `_check_with_<tool>()` function in `game_builder/pipeline.py`
3. Call it from `_validate_and_repair_scripts()` alongside gdlint and godot
4. Error output is automatically combined into the LLM repair prompt

### Adding a new fleet server integration

1. Register the server's port in `mcp-central-docs/operations/WEBAPP_PORTS.md`
2. Add a `fleet_<name>_*` tool module in `src/godot_mcp/fleet/`
3. Expose in `GET /api/capabilities`
4. Wire into `build_game()` pipeline if it's a game builder dependency

### Rules for secondary tool inclusion

- Must be **maintained** (updated in the last 12 months)
- Must work **headless/CLI** (no editor GUI dependency)
- Must be installable via **package manager** (pip, npm, cargo) or **Godot
  Asset Library** with CLI fallback
- Must have **permissive license** (MIT, Apache 2.0, BSD, CC0)
