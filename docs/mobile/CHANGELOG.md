# Changelog — Mobile Gateway Protocol

## 0.1.0 (2026-05-27)

```
Status:     Pre-WWDC preview
Trajectory: iOS 27 beta launch target
```

### Initial Release

**Protocol**

- WebSocket gateway at `ws://<host>:10993/mobile/v1`
- REST fallback at `POST /mobile/v1/command`
- Message envelope: `{id, type, app, payload}`
- Response types: `ack`, `result`, `error`, `event`, `frame`
- Subscription model with wildcard channel matching
- Full payload validation via Pydantic models

**App #1: Spatial Vibe-Director**

- 6 intent types: `place_asset`, `anchor_light`, `wire_trigger`, `move_node`,
  `delete_node`, `query_space`
- Spatial anchor model with transform, physical space, tracking state
- Voice transcription support (`transcript` + `confidence` fields)
- Tool chains: `import_glb` → `set_material`, `add_light`, `read_scene_tree`

**App #2: State-Surveiller & QA Crucible**

- 5 intervention types: `reparent`, `set_param`, `force_restart`, `kill_agent`,
  `resume_loop`
- 4 subscription channels: `agent:*`, `logs`, `frames:{id}`, `godot:status`
- Push-based agent state monitoring
- LDDO score for agent output quality assessment
- Hot-fix capability via `modify-node` bridge action

**App #3: Pocket Vibe-Architect**

- 6 intent types: `generate:environment`, `generate:asset`, `generate:ui_theme`,
  `generate:behavior`, `generate:gdscript`, `approve`, `reject`, `tweak`
- 4 output types: `screenshot`, `video_clip`, `scene_file`, `gdscript`
- 4 generation modes: `environment`, `asset`, `ui_theme`, `behavior`, `gdscript`
- Human-in-the-loop approve/reject/tweak cycle
- Progress events via subscription channel

**Infrastructure**

- `ClientManager` with multi-client support (50 concurrent connections)
- `MobileDispatcher` singleton for validated command routing
- Background push tasks for logs (0.5s) and Godot status (2s)
- Self-documenting help via `GET /mobile/v1/help` and `WS {"type": "help"}`
- 8 error codes with recovery hints

**Documentation**

- `docs/mobile/INDEX.md` — documentation hub
- `docs/mobile/ARCHITECTURE.md` — system topology, data flow, rationale
- `docs/mobile/APP_SPATIAL_VIBE.md` — App #1 deep dive
- `docs/mobile/APP_STATE_SURVEILLER.md` — App #2 deep dive
- `docs/mobile/APP_POCKET_ARCHITECT.md` — App #3 deep dive
- `docs/mobile/PROTOCOL_REFERENCE.md` — comprehensive reference
- `docs/mobile/EXTENDING.md` — extension guide
- `docs/MOBILE_QUICKSTART.md` — 5-minute connect guide
- `examples/mobile_client.py` — runnable Python test client

### Known Limitations

- No JWT auth yet (gateway accepts all connections)
- No TLS/WSS (WebSocket over HTTPS) — plain WS only
- `wire_trigger` intent has no dedicated workflow yet (requires custom workflow)
- `kill_agent` intervention delegates to `bridge_call_tool` — no native agent
  management service yet
- No multi-instance gateway (horizontal scaling not supported)
- Frame streaming from Godot not yet implemented (channel defined, no push task)

### Planned for 0.2.0

- JWT auth with per-app scoping
- WSS support (WebSocket over TLS)
- Agent management service (native kill/restart/spawn)
- Frame streaming from Godot via scene capture
- Multi-instance gateway with Redis-backed ClientManager
- iOS 27 intent framework integration (post-WWDC)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-05-27 | Initial pre-WWDC release |
