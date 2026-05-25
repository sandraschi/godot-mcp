# Little Game Guide — Study Repos, AI Workflow, Distribution

**Last updated:** May 2026  
**Audience:** You are not trying to become an indie studio. You want a small, fun project with AI help and a sane path to share it on Windows or iOS.

**Related:** [Sample games](../samples/README.md) · [Ship to itch.io](ship-to-itch.md) · [AI and indie games](ai-and-indie-games.md) · [Agentic game dev](agentic-game-dev.md) · [AI flows](ai-flows.md) · [Godot reference](godot.md)

---

## 1. What “near AAA” actually means on Godot

Godot has **no true AAA** titles (Elden Ring scale). It **does** have million-copy indies — notably **Slay the Spire 2**, **Buckshot Roulette**, **Brotato**, **Cassette Beasts**, **Halls of Torment**. Those teams are full-time studios.

For a **little game**, aim for:

| Realistic scope | Examples |
|-----------------|----------|
| One mechanic done well | Pong variant, dodge-the-creeps, one-room puzzle |
| One level or endless mode | Platformer with 3–5 screens, survivor wave game |
| Web or desktop first | HTML5 or a single `.exe` folder |
| AI does boilerplate | Scene nodes, materials, export commands — you pick feel and scope |

Official showcase: [godotengine.org/showcase](https://godotengine.org/showcase/)

---

## 2. Study these five repos (mapped to godot-mcp samples)

Clone what you need locally, or use the copies already under `samples/` where noted.

| # | Repository | Study for | godot-mcp shortcut |
|---|------------|-----------|-------------------|
| **1** | [godotengine/godot-demo-projects](https://github.com/godotengine/godot-demo-projects) | Official patterns: 2D platformer, dodge, GUI, audio, networking | `just demo-run platformer` · `just demo-run dodge` · `just demo-run pong` |
| **2** | [uheartbeast/Heart-Platformer-Godot-4](https://github.com/uheartbeast/Heart-Platformer-Godot-4) | Clean 2D movement, camera, game feel (“juice”) | `just demo-run heart` |
| **3** | [gdquest-demos/godot-4-procedural-generation](https://github.com/gdquest-demos/godot-4-procedural-generation) | Procedural maps, random levels, PCG workflows | `just demo-run procedural` |
| **4** | [miskatonicstudio/intrepid](https://github.com/miskatonicstudio/intrepid) | **Full game source** of a shipped title (Godot 3.x — patterns still useful) | Read-only reference; compare folder layout to your project |
| **5** | [KipJM/ACEDIA](https://github.com/KipJM/ACEDIA) | **Full Godot 4.4** project with open code + Creative Commons assets | Modern GDScript + C# mono layout; good “how is a real 4.x repo organized?” |

**Bonus (iPad / multi-platform FOSS):** [adchamberlain/into-the-wild](https://github.com/adchamberlain/into-the-wild) — MIT, procedural camping game with desktop + App Store builds from one Godot 4.5 project.

**Not Godot (common confusion):** [Relic Hunters Zero](https://github.com/mventurelli/relichunterszero) is open source and on Steam, but built in **GameMaker**, not Godot.

### What to skim in each repo

1. **`project.godot`** — input map, autoloads, display settings  
2. **`scenes/`** — how main scene and UI are split  
3. **`scripts/`** — player controller, state, signals (not every line)  
4. **Export presets** — if present, see how Windows/Web/iOS are configured  

After skimming, run the matching sample:

```powershell
just demo-list
just demo-import heart          # first time only
just demo-run heart
just godot-bridge               # separate window — MCP control, not the demo
```

---

## 3. AI-assisted workflow (with godot-mcp)

You do **not** need to memorize the editor. Typical loop:

```
Idea → AI edits GDScript/scenes (or MCP tools) → Play in Godot (F5) → tweak prompt → export
```

### Stack

| Piece | Role |
|-------|------|
| **Cursor / Claude + godot-mcp** | “Add a jump, spawn 10 enemies, set sky color…” via MCP tools or direct file edits |
| **Godot editor** | Play test (F5), inspector tweaks, export presets |
| **`just demo-run`** | Borrow movement/UI from samples instead of writing from zero |
| **`just bridge-test`** | Confirm MCP ↔ engine before batch automation |

### Good AI prompts (small game)

- “Fork Heart Platformer movement; one screen, three platforms, one collectible.”  
- “Use dodge-the-creeps enemy spawn pattern; cap at 50 enemies; export Web.”  
- “Read `godot_read_scene_tree`; list all MeshInstance3D nodes and their materials.”  

### When to use MCP vs editor

| Task | Prefer |
|------|--------|
| Bulk scene build, CFD viz, STL import | MCP tools |
| Jump height, animation timing, UI layout | Editor + human eye |
| Repeatable export | MCP `godot_export_web` or CLI `godot --export-release` |

See [agentic-game-dev.md](agentic-game-dev.md) for the full tool map.

---

## 4. How to distribute your little game

**MCD (detailed):** [platform / Butler](https://github.com/sandraschi/mcp-central-docs/blob/main/docs/gamedev/ITCH_IO_PLATFORM.md) · [itch.io games](https://github.com/sandraschi/mcp-central-docs/blob/main/docs/gamedev/ITCH_IO_GUIDE.md) · [tools/assets](https://github.com/sandraschi/mcp-central-docs/blob/main/docs/gamedev/ITCH_IO_TOOLS_ASSETS.md) · [Steam](https://github.com/sandraschi/mcp-central-docs/blob/main/docs/gamedev/STEAM_PUBLISHING.md)  
Local path: `mcp-central-docs/docs/gamedev/`

### Export with `just` (from godot-mcp repo)

Adds `export_presets.cfg` to the sample on first run if missing. Output under `build/little-game/<game>/`.

```powershell
just install-export-templates          # once per Godot version
just little-game-export web              # default game: dodge
just little-game-export web dodge        # HTML5 → build/little-game/dodge/web/
just little-game-pack web dodge          # zip for itch.io upload

just little-game-export windows dodge    # .exe → build/little-game/dodge/windows/
just little-game-pack windows dodge      # zip for itch.io download
```

Custom output path:

```powershell
just little-game-export web dodge output="D:/builds/my-game/index.html"
```

**First-time requirement:** Godot **export templates** — run `just install-export-templates` (or Editor → **Manage Export Templates**).

### Easiest first: Web (HTML5)

Works on **Windows, macOS, Linux, iOS Safari, Android Chrome** — no store accounts.

```powershell
# Via MCP (bridge + server running)
just godot-export path="D:/builds/my-game/index.html"

# Or Godot CLI from your project folder
godot --headless --export-release "Web" D:/builds/my-game/index.html
```

Host options: **itch.io** (drag `index.html` + `.pck`/`.wasm`), **GitHub Pages**, **Netlify**, or zip and email.

**Caveats:** Large downloads, no App Store presence, some mobile browser limits (audio fullscreen).

---

### Windows desktop

**Path A — Godot export (recommended for a real `.exe`)**

1. In Godot: **Project → Export → Add → Windows Desktop**  
2. Download export templates if prompted (**Editor → Manage Export Templates**)  
3. Export **Debug** (quick share) or **Release** (smaller, faster)

```powershell
godot --headless --export-release "Windows Desktop" D:/builds/my-game/MyGame.exe
```

Ship a **folder** (`.exe` + `.pck` + DLLs) or use **Export → Embed PCK** for a single exe.

**Path B — itch.io (recommended for sharing)**

Full walkthrough: **`mcp-central-docs/docs/gamedev/ITCH_IO_GUIDE.md`**

**Via godot-mcp (Butler + dashboard)**

1. Set env: `BUTLER_API_KEY`, `ITCH_TARGET=user/game` (optional: `GODOT_EXPORT_GAME=dodge`)  
2. Install [Butler](https://itchio.itch.io/butler) or use the itch app (bundled butler)  
3. Dashboard: **`/ship`** — Export → Preview → Push  
4. CLI: `just ship web dodge` or `just little-game-pack web dodge` then `just itch-push …`  

MCP tools: `ship_to_itch`, `godot_export_release`, `itch_push_preview`, `itch_push`, `itch_status`.

**Manual upload**

1. `just little-game-pack web dodge`  
2. Create free account at [itch.io](https://itch.io)  
3. New project → kind **HTML** → upload zip or web folder  
4. Share `https://yourname.itch.io/your-game`  

**Path C — Zip without itch**

- Email/cloud zip of `build/little-game/dodge/windows/`  

**Path D — Steam**

$100 Steam Direct fee, Steamworks, store art, build upload. Only if you want a real store product.  
Guide: **`mcp-central-docs/docs/gamedev/STEAM_PUBLISHING.md`**

**Note:** godot-mcp’s **Tauri** wrapper (`native/`) packages the **MCP dashboard + Python backend**, not your game project. Export the game from **your** Godot project separately.

---

### iOS (iPhone / iPad)

Godot **can** export to iOS, but Apple’s pipeline is stricter than Windows.

| Requirement | Detail |
|-------------|--------|
| **Apple Developer Program** | ~**$99 USD / year** ([developer.apple.com](https://developer.apple.com)) |
| **macOS + Xcode** | iOS builds are **signed on a Mac**. Pure Windows dev machines cannot finish App Store builds locally. |
| **Export templates** | Install iOS templates in Godot (same as other platforms) |
| **Provisioning** | Development + distribution profiles in Apple Developer portal |

**Typical flow**

1. On a Mac: open project in Godot → **Export → iOS**  
2. Godot generates an **Xcode project**  
3. Open in Xcode → sign with your team → **Run on device** or **Archive → TestFlight / App Store**  

**Without a Mac**

- **Cloud Mac** (MacStadium, GitHub Actions macOS runner + fastlane)  
- **Skip native iOS** — ship **Web** or **itch.io HTML**; works in Mobile Safari (good enough for a toy game)  
- Study **[Into the Wild](https://github.com/adchamberlain/into-the-wild)** for a FOSS example that ships iPad + desktop from one repo  

**TestFlight** (beta to friends): upload build from Xcode → add testers by email — no public App Store review for internal testing.

---

### Distribution cheat sheet

| Goal | Easiest path | Store / account |
|------|--------------|-----------------|
| Friends on PC | `Windows Desktop` zip or itch.io | None |
| Play in browser everywhere | Web export + itch.io | None |
| iPhone (serious) | Mac + Xcode + TestFlight | Apple Developer $99/yr |
| iPhone (casual) | Web export, “Add to Home Screen” | None |
| Open source portfolio | GitHub repo + itch “pay what you want” | None |

---

## 5. Suggested first project (90-minute path)

1. `just demo-run dodge` — play Dodge the Creeps  
2. Ask AI: “Duplicate dodge logic; change player to a cat sprite; one enemy type; score label.”  
3. Play (F5), tweak speed in inspector  
4. `just little-game-export web dodge`  
5. `just little-game-pack web dodge` → upload zip to [itch.io](https://itch.io) (see MCD `docs/gamedev/ITCH_IO_GUIDE.md`)  

You now have a shareable link. No indie career required.

---

## 6. Commercial Godot games (motivation, not homework)

Closed-source hits worth knowing exist — you do **not** need to study their code:

| Game | Why it matters |
|------|----------------|
| [Slay the Spire 2](https://store.steampowered.com/app/2868840/) | Proves Godot scales to franchise sequels |
| [Buckshot Roulette](https://store.steampowered.com/app/2835570/) | Small scope, viral |
| [Cassette Beasts](https://store.steampowered.com/app/1321440/) | Team patched Godot engine source for performance |
| [Halls of Torment](https://store.steampowered.com/app/2218750/) | Single-mechanic depth |

For a little AI-assisted game, treat these as **scope inspiration**, not templates.

---

## 7. AI and indie games — is it over?

If AI can scaffold a playable game in an afternoon, did indie die?

**No** — but the floor dropped and the bar for attention rose. AI replaces scaffold + wiring, not months of design, polish, and launch. See **[AI and indie games](ai-and-indie-games.md)** (VibeCode Runner is the worked example).

---

## 8. Links

- Fleet doc mirror: `mcp-central-docs/projects/godot-mcp/LITTLE_GAME_GUIDE.md`  
- **AI and indie (MCD):** `mcp-central-docs/projects/godot-mcp/AI_AND_INDIE_GAMES.md`  
- **itch.io platform (MCD):** `mcp-central-docs/docs/gamedev/ITCH_IO_PLATFORM.md`  
- **itch.io games (MCD):** `mcp-central-docs/docs/gamedev/ITCH_IO_GUIDE.md`  
- **itch.io tools/assets (MCD):** `mcp-central-docs/docs/gamedev/ITCH_IO_TOOLS_ASSETS.md`  
- **Steam (MCD):** `mcp-central-docs/docs/gamedev/STEAM_PUBLISHING.md`  
- Official demos repo: [github.com/godotengine/godot-demo-projects](https://github.com/godotengine/godot-demo-projects)  
- Export docs: [docs.godotengine.org — Exporting projects](https://docs.godotengine.org/en/stable/tutorials/export/index.html)  
- iOS export: [docs.godotengine.org — Exporting for iOS](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_ios.html)
