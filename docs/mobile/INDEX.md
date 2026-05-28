# Godot-MCP Mobile Gateway — Documentation

```
Project trajectory:  iOS 27 mobile control deck for Goliath + godot-mcp
Target release:      WWDC June 8, 2026
Protocol version:    0.1.0
```

## Quick Links

| If you want to... | Start here |
|---|---|
| Connect your iOS app in 5 minutes | [Quickstart](../MOBILE_QUICKSTART.md) |
| Understand the full system architecture | [Architecture](./ARCHITECTURE.md) |
| Build the Spatial Vibe-Director (XR blueprinting) | [App Deep-Dive: Spatial Vibe](./APP_SPATIAL_VIBE.md) |
| Build the State-Surveiller (agent monitoring) | [App Deep-Dive: State Surveiller](./APP_STATE_SURVEILLER.md) |
| Build the Pocket Architect (generative deck) | [App Deep-Dive: Pocket Architect](./APP_POCKET_ARCHITECT.md) |
| See every message schema, error code, and tool | [Protocol Reference](./PROTOCOL_REFERENCE.md) |
| Add a new intent, tool, or app | [Extending the Gateway](./EXTENDING.md) |
| See what changed between versions | [Changelog](./CHANGELOG.md) |
| Fetch live help from a running server | `GET /mobile/v1/help` or `WS {"type": "help"}` |

## Documentation Map

```
docs/
├── mobile/
│   ├── INDEX.md                    ← You are here
│   ├── ARCHITECTURE.md             ← Network topology, data flow, rationale
│   ├── APP_SPATIAL_VIBE.md         ← App #1: Spatial Vibe-Director
│   ├── APP_STATE_SURVEILLER.md     ← App #2: State-Surveiller & QA Crucible
│   ├── APP_POCKET_ARCHITECT.md     ← App #3: Pocket Vibe-Architect
│   ├── PROTOCOL_REFERENCE.md       ← Complete protocol reference
│   ├── EXTENDING.md                ← How to add tools, intents, channels, apps
│   └── CHANGELOG.md                ← Version history
│
├── MOBILE_API_CONTRACT.md          ← Original API contract (maintained)
├── MOBILE_QUICKSTART.md            ← 5-minute connection guide
|
├── api.md                          ← REST API docs
├── architecture.md                 ← Backend architecture
└── SPEC_GAME_BUILDER.md            ← Game builder pipeline spec
```

## Source Code Map

```
src/godot_mcp/
├── server.py                       ← FastAPI + WebSocket endpoints
├── services/
│   ├── godot_bridge.py             ← TCP bridge client (port 9080 → Godot)
│   ├── ws_gateway.py               ← WebSocket gateway for iOS clients
│   ├── mobile_command.py           ← Pydantic models + dispatcher
│   └── mobile_help.py              ← Self-documenting help system
│
├── tools/
│   ├── __init__.py                 ← Portmanteau registration (49 tools)
│   ├── core_tools.py               ← 14 Godot bridge tools
│   ├── artifacts/tools.py          ← 5 artifact depot tools
│   ├── fleet/tools.py              ← 6 fleet pipeline tools
│   ├── game_builder/tools.py       ← 6 game generation tools
│   ├── sampling/tools.py           ← 2 LLM sampling tools
│   ├── workflows/tools.py          ← 2 workflow tools
│   ├── prefabs/tools.py            ← 2 prefab tools
│   ├── prompts/tools.py            ← 2 prompt template tools
│   ├── mcp_bridge/tools.py         ← 2 cross-server bridge tools
│   └── mcpb/tools.py               ← 2 MCPB bundle tools
│
├── itch/                           ← itch.io publishing
├── fleet/                          ← Cross-server fleet pipeline
├── game_builder/                   ← AI game-from-prompt pipeline
├── artifacts/                      ← Asset depot
├── sampling/                       ← LLM sampling service
└── workflows/                      ← Workflow engine
```

## Versioning

This documentation tracks `MOBILE_PROTOCOL_VERSION = "0.1.0"`. Breaking changes to
the mobile protocol (WebSocket message shapes, intent types, error codes) increment
the major version. Additions (new intents, new tools, new channels) are backward-compatible
within a version.

See [Changelog](./CHANGELOG.md) for the full version history.
