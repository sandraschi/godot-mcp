# Godot MCP — Community Resources

**Last Updated**: May 2026

---

## Official Godot Channels

### Godot Engine Website

**https://godotengine.org** — The central hub. Download the engine, read the docs, browse the asset library, find community news.

- Documentation: https://docs.godotengine.org
- Asset Library: https://godotengine.org/asset-library
- Blog: https://godotengine.org/news
- Download: https://godotengine.org/download

### Godot Discord

**https://discord.gg/godotengine** — The largest Godot community space. 200,000+ members.

Channels of interest:
- `#general` — Engine questions and discussion
- `#beginner` — Safe space for new users
- `#gdscript` — Scripting help
- `#3d` — 3D rendering, materials, lighting
- `#2d` — 2D-specific topics
- `#plugins` — Add-on development
- `#assets` — Asset creation and sharing
- `#showcase` — Share your projects
- `#csharp` — C#/.NET binding questions
- `#web` — HTML5/Web export
- `#xr` — VR/AR development
- `#jobs` — Contract and employment postings

### Reddit

**r/godot** — https://reddit.com/r/godot — 400,000+ subscribers. Active daily with:
- Showcase posts (games made with Godot)
- Technical Q&A
- Tutorials and resources
- News and release announcements

**r/godot4** — Focused specifically on Godot 4.x (smaller but more technical).

### Godot Forum

**https://forum.godotengine.org** — Official Q&A and discussion forum. Tagged by category:
- Engine development
- Tutorials
- Showcase
- Class reference
- Contributing

### Bluesky

**@godotengine.org** on Bluesky — Official social media for release announcements, contributor highlights, and community events.

### GitHub

**https://github.com/godotengine/godot** — 95,000+ stars, 1,800+ contributors.

- **Issues**: Bug reports and feature requests. `master` branch for Godot 4.x.
- **Pull Requests**: Contributions to the engine itself.
- **Discussions**: RFCs and design proposals.

---

## Godot Foundation

The Godot Foundation is a non-profit organization based in the Netherlands that oversees engine development and community infrastructure.

**Structure**:
- **Board**: Juan Linietsky, Rémi Verschelde, and community-elected members
- **Core Developers**: ~10 paid full-time developers funded by donations
- **Contributors**: 1,800+ volunteer contributors on GitHub

**Funding sources**:
- Open Collective: https://opencollective.com/godotengine
- GitHub Sponsors: https://github.com/sponsors/godotengine
- Direct donations via the website
- Major sponsors: Google, Meta, Microsoft, Re-Logic (Terraria), W4 Games

**How funds are used**:
- Developer salaries (primary expense)
- Server infrastructure
- Conference organization
- Bug bounty programs

---

## Godot Development Fund

The **Godot Development Fund** is a recurring donation program for individuals and companies who want to ensure Godot's long-term sustainability.

**Tiers** (monthly):
- **Bronze**: €1-9
- **Silver**: €10-49
- **Gold**: €50-249
- **Platinum**: €250+

**Benefits**: Listed on the Godot website, priority feature voting for higher tiers, early access to development meetings.

**Why donate**: Godot has no corporate parent. The Foundation relies entirely on donations. Every euro goes to developer salaries and infrastructure.

---

## W4 Games

**https://w4games.com** — A commercial entity founded by Godot's original creators (Juan Linietsky, Rémi Verschelde) to provide enterprise services.

**Services**:
- **Console Porting**: Nintendo Switch, PlayStation 5, Xbox Series X/S
- **W4 Cloud**: Backend-as-a-Service for Godot games (multiplayer, leaderboards, analytics)
- **Enterprise Support**: SLAs, priority bug fixes, custom development
- **Mobile Optimization**: Fine-tuned iOS/Android builds with platform-specific optimizations

**Relationship to Godot Foundation**: W4 Games is a separate for-profit entity. Revenue from W4 Games directly funds Godot development through donations and shared resources. W4 Games employees also contribute to the engine.

---

## GodotCon

**GodotCon** is the official Godot community conference. Annual event with talks, workshops, and networking.

| Event | Location | Date | Theme |
|-------|----------|------|-------|
| GodotCon 2023 | Munich, Germany | May 2023 | First in-person post-pandemic |
| GodotCon 2024 | Tokyo, Japan | August 2024 | Asian developer outreach |
| GodotCon 2025 | Amsterdam, Netherlands | June 2025 | Godot 4.5 launch, W4 Games showcase |
| **GodotCon 2026** | **Boston, USA** | **July 2026** | *Upcoming — Jolt physics deep-dive, 4.7 preview* |

**Call for Proposals**: Opens 3-4 months before the event. Talks are 20-40 minutes on any Godot-related topic: rendering, gameplay, tooling, education, porting.

**Workshops**: Half-day hands-on sessions on GDScript, shader programming, and 2D/3D art pipelines.

---

## Asset Library

**https://godotengine.org/asset-library** — Community-contributed free assets for Godot.

**Categories**:
- **Scripts**: GDScript utilities, editor plugins, autoloads
- **Materials**: PBR materials, shaders, particle effects
- **Scenes**: Pre-built scenes (character controllers, UI components)
- **Models**: 3D models, characters, environments
- **Audio**: Sound effects, music tracks
- **Tiles and Sprites**: 2D tile sets, character sprites
- **Templates**: Complete project templates (platformer, FPS, point-and-click)

**All assets are free**. No paid asset store. The library is curated by volunteers.

---

## Contributing to godot-mcp

**Repository**: https://github.com/your-org/godot-mcp *(or fleet internal)*

### Ways to Contribute

**Code**:
- Python backend: FastMCP tools, FastAPI endpoints, bridge service
- GDScript: mcp_bridge.gd improvements, new action handlers
- Webapp: TypeScript/React frontend
- Testing: pytest unit tests, integration tests
- Docs: Documentation improvements, new examples

**Bug Reports**:
Submit via GitHub Issues. Include:
- Python server version
- Godot engine version
- Full error output
- Steps to reproduce
- Whether the bug is in the TCP bridge, REST API, or webapp

**Feature Requests**:
Open a GitHub Discussion or Issue with:
- What the feature does
- Use case / pipeline context
- Example MCP tool signature (if applicable)

### Development Setup

```powershell
# Clone, bootstrap, and verify
git clone <repo-url>
cd godot-mcp
just bootstrap
just check
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`feature/your-feature`)
3. Make changes (follow existing patterns)
4. Run `just check` (lint + tests must pass)
5. Write or update tests
6. Open PR with description

### Code Standards

- Python: Ruff linting (`just lint`), Pydantic v2 models, type hints everywhere
- TypeScript: Biome linting, React 19 functional components, Tailwind CSS
- GDScript: Static typing, kebab-case file names, snake_case variables
- Git: Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)

### Where to Start

Good first contributions:
- Write a new example in `docs/examples.md` (like this document)
- Add a new MCP tool (e.g., `godot_load_animation`, `godot_bake_lightmap`)
- Improve error messages in `mcp_bridge.gd`
- Add a pytest test case
- Create a tutorial video for the community

---

## Related Fleet Projects

These projects integrate with godot-mcp in the cross-repo pipeline:

| Project | Port | Description |
|---------|------|-------------|
| **qcad-mcp** | 10966 | CAD geometry generation, STL/DXF export |
| **freecad-mcp** | 10944 | BIM model conversion, STEP/STL validation |
| **resonite-mcp** | 10978 | XR world deployment from Godot exports |

For cross-repo integration, see [architecture.md](./architecture.md).

---

## Learning Resources

### Official Documentation

- **Godot Docs**: https://docs.godotengine.org — Complete engine reference
- **Godot 4 Class Reference**: https://docs.godotengine.org/en/stable/classes/
- **GDScript Reference**: https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/
- **Shading Reference**: https://docs.godotengine.org/en/stable/tutorials/shaders/

### Books

- *Godot 4 Game Development Cookbook* by J. F. C. Willems (Packt, 2024)
- *Godot 4: The Complete Guide* by Chris Bradfield (Leanpub, 2025)
- *GDQuest's Godot 4 Course* (online, free)
- *Your First 2D Game* in the Godot docs (free, built-in tutorial)

### YouTube Channels

- **GDQuest**: High-quality Godot tutorials (free + paid)
- **Bastiaan Olij**: XR and AR development
- **PlayWithFurcifer**: Particle effects and VFX
- **MisterTaftCreates**: GDScript tutorials and best practices
- **Godot Tutorials** (by Jesus Zúñiga): Comprehensive beginner series

### godot-mcp Specific

- This documentation directory (`docs/`)
- `README.md` at project root
- Python server inline docstrings (FastMCP tool descriptions)
- GDScript comments in `mcp_bridge.gd`
