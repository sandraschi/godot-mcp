# mcpb/ — MCPB bundle assets

MCPB packing for godot-mcp is done at the **repo root** via the fleet-standard
recipe:

```powershell
just mcpb-pack
```

That runs `scripts/mcpb-pack.ps1`, which packs the repo root (the real
`src/godot_mcp` package, root `manifest.json`, root `run_server.py`,
`.mcpbignore`) with the Anthropic `mcpb` CLI into
`dist/godot-mcp-v<version>.mcpb`.

This directory only holds bundle assets referenced by the root manifest:

- `assets/icon.png` — bundle icon
- `assets/prompts/` — system/user prompt templates and examples

History: this directory previously contained a duplicated flat copy of the
server (`src/server.py`, own `manifest.json`/`pyproject.toml`) that drifted
from the real package and produced broken bundles (tar.gz instead of mcpb zip,
`${PWD}` manifest variables). That copy was removed in 0.3.0 — do not
reintroduce it.
