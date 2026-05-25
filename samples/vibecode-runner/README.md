# VibeCode Runner

Endless side-scroller for the **vibecoding** era. Ship LOC, jump the IDEs, don’t leak tokens, survive the **Bulerite Jihad**.

## Run

```powershell
just demo-run vibecode
```

**Controls:** `SPACE` / `W` / `↑` — jump · `SPACE` — start / restart

## Hazards

| Type | What | When |
|------|------|------|
| **IDE obstacles** | VS Code, Windsurf, Cursor | Always — jump over |
| **PowerShell** | `\| &&` + `$env:` | Ground |
| **Agent loop** | `while(true):` | Ground |
| **API token** | `sk-live…` | Ground |
| **Trumpler** | Orange flyer, `POST!!!` swoops | After ~1200 LOC |
| **Elonsky** | Rocket dive bomber | After ~1200 LOC |
| **GEN. BUTLER** | Final boss — `butler push --force` projectiles | Every **2200 LOC** |

Defeat the boss by **surviving ~18s** (HP bar drains while you dodge). Bonus **+500 vibe** on win.

## Export / itch

```powershell
just little-game-export web vibecode
just ship web vibecode
```

No external art — ColorRect + Label + Polygon2D primitives (Godot 4.4).

Built in one AI-assisted session; see [AI and indie games](../../docs/ai-and-indie-games.md) for what that does and does not mean.
