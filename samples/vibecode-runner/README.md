# Vibecoder Runner

A 2D side-scrolling runner where you fight AI-themed enemies as a vibecoder
(headphones on, energy drink in hand, 12 terminals open).

**Theme:** Dark terminal green-on-black, procedural visuals, tech satire.

## Enemies

| Enemy | Behavior | Inspired by |
|-------|----------|-------------|
| **Hallucinator** | Teleports randomly, spawns fake power-ups | LLM hallucination |
| **Prompt Injector** | Hacks your key bindings every 5s | Prompt injection attacks |
| **Tokenmaxxer** | Drains your score (tokens) on contact | Token-based pricing |
| **Context Overflow** | `]` brackets close in from both edges | Context window limits |
| **Claude Desktop** | Immobile desk, apology stun, CoT beam | Claude desktop app |
| **Techbro** | Drops jargon mines, splits on death | Startup culture |
| **Legacy Code** | COBOL floor strip, GOTO teleport | Enterprise legacy |
| **TheVC** | Takes 50% equity when score > 100 | Venture capital |
| **TheMeeting** | Calendar invite swarm, 45-min stun | Meeting culture |
| **TheDatacenter** | Carbon meter rises, fan blast, pipes | AI datacenter能耗 |

## Controls

| Key | Action |
|-----|--------|
| Arrow Left/Right | Move |
| Space | Jump |
| Ship It! button | Clears all enemies (3 charges) |

## Systems

- **Score** — LOC (Lines of Code), ticks up continuously
- **Multiplier** — 2x for 5s (future: energy drink pickup)
- **Carbon Meter** — rises from datacenter heat. 100% = EPA fines, game over
- **Ship It!** — ultimate ability, clears all enemies, 3 charges
- **Stun** — some enemies stun you (Claude apology, Meeting status update)

## Technical

- Built for Godot 4.4+
- 11 GDScript files, 329 total lines
- All scripts pass `gdlint` (0 errors, 0 warnings)
- Procedural visuals only — no external image assets
- Fully compatible with Godot headless export (`--export-release web`)

## Run

```powershell
just demo-run vibecode
# or
godot --path samples/vibecode-runner
```
