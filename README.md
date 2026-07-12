# Godot MCP

<p align="center">
  <img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square" alt="Just">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/FastMCP-3.4-7c5cfc?style=flat-square" alt="FastMCP">
  <img src="https://img.shields.io/badge/tier-T3--desktop-7c5cfc?style=flat-square" alt="Release Tier">
</p>

AI-driven Godot 4 control via MCP — scene manipulation, 3D import, GPU particles,
procedural textures, HTML5 export. **Game Builder**: describe a game in natural
language and get playable GDScript + export. Publish to itch.io and Steam.
80+ tools, 73 tests, NSIS desktop installer.

---

## Quick Install

```powershell
git clone https://github.com/sandraschi/godot-mcp
cd godot-mcp
just bootstrap       # install deps
just serve           # start server (10993)
just web             # open dashboard (10992)
```

See [INSTALL.md](INSTALL.md) for all options (MCPB, dev setup, naked PC).

---

## Features

- **Game Builder** — `design_game` -> `generate_game_logic` -> `generate_game_tests` -> `generate_dialogue` -> export. Validated with gdlint + godot --check-only, auto-repaired by LLM. [Tutorial](docs/game-builder-tutorial.md)
- **Procedural textures** — `godot_generate_procedural_texture`: gradient, noise, checker, solid. No external assets needed.
- **Engine control** — 20 bridge tools: import STL/GLB/OBJ, particles, cameras, lighting, animation, viewport capture, input simulation, scene node management.
- **Publishing** — `itch_ops` and `steam_ops` portmanteaus for itch.io Butler and SteamPipe. Cross-repo fleet pipeline.
- **GDScript validation** — two-pass (gdlint style + godot compile) with LLM repair. 
- **Plugin ecosystem** — 7 community plugins installable from the `/plugins` page.
- **LLM detection** — auto GPU probe, model recommendation by VRAM tier. Default `gemma4:12b`.
- **Sample game** — [Vibecoder Runner](samples/vibecode-runner/) with 10 AI-themed enemy types.

## What You Can Do

```powershell
just gb-demo "A 2D runner where you collect stars and avoid spikes"
just bridge-test                          # check engine connection
just demo-run vibecode                    # play sample game
just gb-preview                           # preview latest HTML5 export
```

## Documentation

| Doc | Contents |
|-----|----------|
| [Installation](INSTALL.md) | All install methods |
| [Configuration](docs/CONFIGURATION.md) | Env vars, settings |
| [Tool Reference](docs/TOOLS.md) | All 80+ MCP tools |
| [Game Builder Tutorial](docs/game-builder-tutorial.md) | Prompt-to-game walkthrough |
| [Godot Ecosystem](docs/godot-ecosystem.md) | Plugins, gdtoolkit, fleet pipeline |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |
| [API Reference](docs/api.md) | REST endpoints |
| [Development](docs/DEVELOPMENT.md) | Contributing, local setup |

## Requirements

- **Godot 4.4+** (for engine bridge tools) — `just install-godot` or [godotengine.org](https://godotengine.org)
- **Python 3.13+** + **uv** — `winget install astral-sh.uv`
- **Bun** — `winget install oven-sh.bun`
- **Ollama** (optional, for game builder) — `winget install Ollama.Ollama` then `ollama pull gemma4:12b`
- **Rust** (optional, for NSIS build) — `rustup.rs`

## License

MIT — see [LICENSE](LICENSE).
