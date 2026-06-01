# Ship to Steam

Export a Godot Windows build, stage it in the fleet exchange, and upload via **steam-mcp** (SteamPipe VDF + steamcmd).

> **Canonical partner guide:** [STEAM_PUBLISHING.md](../../mcp-central-docs/docs/gamedev/STEAM_PUBLISHING.md) — Steam Direct, credentials, testing, “playground” FAQ.

## Is there a Steam playground?

**No free sandbox** like itch.io. Options for a small / runt game:

1. **itch.io** — free, instant (`/ship`, `just ship web dodge`).
2. **Your Steam app + beta branch** — costs **$100 Steam Direct**; upload with `ship_to_steam_prerelease` / `just steam-ship-beta`; testers opt into **beta** in Steam.
3. **Developer comp keys** — free keys for your App ID from Steamworks.
4. **Fleet dry run** — `dry_run=true` (default) shows the steamcmd command without uploading.
5. **Spacewar (480)** — SDK sample only; **do not** use for your game’s depot or `steam_appid.txt`.

## Two credential types

| Type | Env vars | Purpose |
|------|----------|---------|
| **Steam Web API** | `STEAM_API_KEY`, `STEAM_ID` on **steam-mcp** | Profile, library, store research — **not** uploads |
| **Steamworks partner** | `STEAM_APP_ID`, `STEAM_DEPOT_ID`, `STEAM_USERNAME`, `STEAMCMD_PATH` | steamcmd / SteamPipe uploads |

Partner credentials come from [partner.steamgames.com](https://partner.steamgames.com) after onboarding + Steam Direct payment. There is **no upload API key** — steamcmd logs in with your partner account.

### Where to find App ID and Depot ID

1. **App ID** — Steamworks → Apps & Packages → your game → number in App Admin URL.
2. **Depot ID** — App Admin → **Depots** → create Windows depot → separate numeric ID.

## Prerequisites

| Variable | Purpose |
|----------|---------|
| `STEAM_MCP_URL` | steam-mcp REST base (default `http://127.0.0.1:11020`) |
| `STEAM_APP_ID` | Steamworks application ID (**yours**, not 480) |
| `STEAM_DEPOT_ID` | Depot ID for your Windows build |
| `STEAM_USERNAME` | Partner account for steamcmd login |
| `STEAMCMD_PATH` | Path to `steamcmd.exe` |
| `STEAMCMD_PASSWORD` | Optional; omit to use steamcmd guard / interactive login |
| `FLEET_EXCHANGE_ROOT` | Default `D:/Dev/repos/_exchange` |

Start **steam-mcp** on port **11020** and **godot-mcp** on **10993** before shipping.

## Quick start (after partner setup)

```powershell
# Terminal 1
cd D:\Dev\repos\steam-mcp; just serve

# Terminal 2
cd D:\Dev\repos\godot-mcp
$env:STEAM_MCP_URL = "http://127.0.0.1:11020"
$env:STEAM_APP_ID = "1234560"
$env:STEAM_DEPOT_ID = "1234561"
$env:STEAM_USERNAME = "your_partner_login"
$env:STEAMCMD_PATH = "D:\Tools\steamcmd\steamcmd.exe"
just serve

# Dry run (safe default)
just steam-ship-beta game=dodge dry_run=true
```

Open **`http://127.0.0.1:10992/ship-steam`** for the dashboard.

When ready for a real beta upload: `dry_run=false`, then set the build live on branch **beta** in Steamworks → Builds.

## MCP tools

| Tool | Description |
|------|-------------|
| `steam_status` | Connectivity + env summary |
| `steam_checklist` | Steam Direct / release checklist |
| `steam_monetization_guide` | Pricing guidance (manual Steamworks) |
| `steam_stage_build` | Export Windows + copy to `_exchange/steam-builds/<app_id>/content` |
| `ship_to_steam_prerelease` | VDF + upload to **beta** branch |
| `ship_to_steam_release` | VDF + upload to **default** branch |
| `ship_to_steam` | Stage + upload in one call |

Upload tools default **`dry_run=True`** — they return the steamcmd command without running it.

## REST

- `GET /api/v1/steam/status`
- `GET /api/v1/steam/checklist?content_root=…`
- `POST /api/v1/steam/stage`
- `POST /api/v1/steam/upload/prerelease`
- `POST /api/v1/steam/upload/release`
- `POST /api/v1/steam/ship`

## Just recipes

```powershell
just steam-status
just steam-stage game=dodge
just steam-ship-beta game=dodge dry_run=true
just steam-ship-release game=dodge dry_run=true
```

## Workflows

- `ship_windows_steam_beta` — export → stage → prerelease upload
- `ship_windows_steam_release` — export → stage → release upload

## Manual steps automation cannot replace

Store capsules, screenshots, content survey, pricing, review, and switching **default** branch live — see [STEAM_PUBLISHING.md](../../mcp-central-docs/docs/gamedev/STEAM_PUBLISHING.md).
