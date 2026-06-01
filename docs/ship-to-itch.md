# Ship to itch.io (godot-mcp)

**Version:** 0.2.1  
**Module:** `godot_mcp/itch/`  
**Dashboard:** `http://127.0.0.1:10992/ship`

Export a sample Godot game and upload to itch.io via [Butler](https://itchio.itch.io/butler). No separate `butler-mcp` repo — shipping lives in **godot-mcp**.

---

## Prerequisites

1. **Godot 4.4+** with export templates: `just install-export-templates`
2. **Butler** — install from itch.io or use the itch desktop app (bundled butler under `%APPDATA%\itch\broth\butler\`)
3. **itch.io API key** — Account → API keys → set `BUTLER_API_KEY` (never commit)
4. **Project slug** — create a draft game on itch.io, set `ITCH_TARGET=user/game`

Optional env:

| Variable | Default | Purpose |
|----------|---------|---------|
| `BUTLER_PATH` | auto | Path to `butler.exe` |
| `ITCH_TARGET` | — | Default `user/game` slug |
| `ITCH_CHANNEL_WEB` | `html` | Butler channel for web builds |
| `ITCH_CHANNEL_WIN` | `win` | Butler channel for Windows builds |
| `GODOT_EXPORT_GAME` | `dodge` | Sample key for export |

---

## Dashboard (`/ship`)

1. `just serve` + `just web`
2. Open **Marketplace → Ship**
3. Check Butler + API key status cards
4. **Export** → **Preview push** → **Push**, or **Ship all**

Secrets are never stored in the UI — only read from environment.

---

## Just recipes

```powershell
just itch-status
just little-game-export web dodge
just itch-push-preview build/little-game/dodge/web
just itch-push build/little-game/dodge/web
just ship web dodge                           # export + preview + push
just ship web dodge itch_target=you/my-game channel=html
```

Server must be running for HTTP recipes (`just serve`). `just itch-status` falls back to inline Python if the server is down.

---

## MCP tools

| Tool | Access | Description |
|------|--------|-------------|
| `itch_status` | READ_ONLY | Butler install, API key set, defaults, last ship |
| `godot_export_release` | MUTATING | Export `web` or `windows` for a sample or custom project |
| `itch_push_preview` | READ_ONLY | Butler `push-preview` diff |
| `itch_push` | MUTATING | Butler `push` to channel |
| `itch_latest_version` | READ_ONLY | Query `api.itch.io/wharf/latest` |
| `ship_to_itch` | MUTATING | Export → optional preview → optional push |

Workflow: `workflow_run(workflow_name="ship_web_itch", game="dodge", itch_target="you/game", channel="html")`

---

## REST API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/itch/status` | Same as `itch_status` |
| `POST` | `/api/v1/itch/export` | Body: `{target, game, project_path?, output_path?}` |
| `POST` | `/api/v1/itch/push-preview` | Body: `{upload_dir, itch_target?, channel?}` |
| `POST` | `/api/v1/itch/push` | Body: `{upload_dir, itch_target?, channel?, hidden?}` |
| `POST` | `/api/v1/itch/ship` | Body: `{target, game, itch_target?, channel?, preview?, push?, hidden?}` |
| `GET` | `/api/v1/itch/latest` | Query: `itch_target`, `channel` |

Also via unified bridge:

```json
POST /api/v1/control/tool
{"tool": "ship_to_itch", "arguments": {"target": "web", "game": "dodge"}}
```

`GET /api/v1/status` includes an `itch` object when the server is up.

---

## Output paths

| Target | Directory | Upload root |
|--------|-----------|-------------|
| `web` | `build/little-game/<game>/web/` | Folder containing `index.html` |
| `windows` | `build/little-game/<game>/windows/` | Folder with `.exe` + `.pck` |

Zip for manual upload: `just little-game-pack web dodge` → `build/little-game/dodge/web-dodge.zip`

---

## Security

- API keys only via environment (`BUTLER_API_KEY`)
- Butler stderr/stdout redacted in logs (`redact_secrets`)
- `upload_dir` must be under repo `build/` or `samples/`

---

## Fleet docs

- [MCD itch.io platform](https://github.com/sandraschi/mcp-central-docs/blob/main/docs/gamedev/ITCH_IO_PLATFORM.md) — web vs app vs Butler vs API
- [MCD itch.io games guide](https://github.com/sandraschi/mcp-central-docs/blob/main/docs/gamedev/ITCH_IO_GUIDE.md) — manual upload
- [Little game guide](./little-game-guide.md) — study repos + distribution overview
- [Marble Adventure (worldlabs-mcp)](https://github.com/sandraschi/mcp-central-docs/blob/main/docs/games/MARBLE_ADVENTURE.md) — separate ship script (`worldlabs-mcp/competition/ship-itch.ps1`); `upload_dir` under `godot-mcp/build/` does not apply
