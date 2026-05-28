"""Example iOS mobile client for godot-mcp gateway.

Usage:
  python examples/mobile_client.py ws://127.0.0.1:10993/mobile/v1 [app]

  app: spatial-vibe | state-surveiller | pocket-architect  (default: all three)
"""

import asyncio
import json
import sys
import uuid

try:
    from httpx_ws import aconnect_ws
except ImportError:
    print("Install httpx-ws: pip install httpx-ws")
    sys.exit(1)


def make_msg(msg_type: str, payload: dict, app: str | None = None) -> str:
    msg = {"id": str(uuid.uuid4())[:8], "type": msg_type, "payload": payload}
    if app:
        msg["app"] = app
    return json.dumps(msg)


async def demo_spatial_vibe(ws) -> None:
    print("\n=== App #1: Spatial Vibe-Director ===")

    # Handshake
    await ws.send_text(json.dumps({"app": "spatial-vibe"}))
    resp = await ws.receive_json()
    print(f"  Handshake: {resp['type']} — client_id={resp['payload']['client_id']}")

    # Subscribe to godot status
    await ws.send_text(make_msg("subscribe", {"channels": ["godot:status"]}, "spatial-vibe"))
    resp = await ws.receive_json()
    print(f"  Subscribe: {resp['type']} — channels={resp['payload']['subscribed']}")

    # Query scene tree
    await ws.send_text(make_msg("command", {"tool": "godot_read_scene_tree", "arguments": {}}))
    resp = await ws.receive_json()
    if resp["type"] == "result":
        data = resp["payload"]
        print(f"  Scene tree: success={data['success']}, data keys={list(data.get('data', {}).keys())}")

    # Place asset
    await ws.send_text(make_msg("intent", {
        "intent_type": "place_asset",
        "transcript": "drop a low-poly tower against the wall",
        "parameters": {
            "asset_ref": "artifact:lowpoly_tower_01",
            "position": {"x": 2.0, "y": 0.0, "z": 5.0},
            "material": {"color": "#4488ff", "roughness": 0.3},
        },
    }, "spatial-vibe"))
    resp = await ws.receive_json()
    print(f"  Place asset: {resp['type']} — intent={resp['payload'].get('intent_type')}")

    # Anchor light
    await ws.send_text(make_msg("intent", {
        "intent_type": "anchor_light",
        "transcript": "add a floating light above the tower",
        "parameters": {
            "light_type": "omni",
            "position": {"x": 2.0, "y": 5.0, "z": 5.0},
            "intensity": 1.5,
        },
    }, "spatial-vibe"))
    resp = await ws.receive_json()
    print(f"  Anchor light: {resp['type']} — intent={resp['payload'].get('intent_type')}")


async def demo_state_surveiller(ws) -> None:
    print("\n=== App #2: State-Surveiller ===")

    await ws.send_text(json.dumps({"app": "state-surveiller"}))
    resp = await ws.receive_json()
    print(f"  Handshake: {resp['type']} — client_id={resp['payload']['client_id']}")

    # Subscribe to all agent channels + logs
    await ws.send_text(make_msg("subscribe", {"channels": ["agent:*", "logs"]}, "state-surveiller"))
    resp = await ws.receive_json()
    print(f"  Subscribe: {resp['type']} — channels={resp['payload']['subscribed']}")

    # Query scene tree (same as command tool call)
    await ws.send_text(make_msg("command", {"tool": "godot_read_scene_tree", "arguments": {}}))
    resp = await ws.receive_json()
    if resp["type"] == "result":
        print(f"  Scene query: success={resp['payload']['success']}")


async def demo_pocket_architect(ws) -> None:
    print("\n=== App #3: Pocket Vibe-Architect ===")

    await ws.send_text(json.dumps({"app": "pocket-architect"}))
    resp = await ws.receive_json()
    print(f"  Handshake: {resp['type']} — client_id={resp['payload']['client_id']}")

    # Subscribe to progress
    await ws.send_text(make_msg("subscribe", {"channels": ["progress"]}, "pocket-architect"))
    resp = await ws.receive_json()
    print(f"  Subscribe: {resp['type']} — channels={resp['payload']['subscribed']}")

    # Generate GDScript
    await ws.send_text(make_msg("intent", {
        "prompt": "auto-flickering emission shader for sci-fi corridor panels",
        "mode": "gdscript",
        "outputs_requested": ["gdscript"],
    }, "pocket-architect"))
    resp = await ws.receive_json()
    if resp["type"] == "result":
        code = resp["payload"].get("data", {}).get("code", "")
        preview = code[:200] + "..." if len(code) > 200 else code
        print(f"  Generated GDScript ({len(code)} chars):\n{preview}")


async def get_help(ws) -> None:
    """Request the full protocol reference."""
    await ws.send_text(json.dumps({"type": "help"}))
    resp = await ws.receive_json()
    if resp["type"] == "result":
        help_data = resp["payload"]["help"]
        print("\n=== Protocol Help ===")
        print(f"  Version: {help_data['version']}")
        print(f"  Endpoints: {list(help_data['endpoints'].keys())}")
        print(f"  Bridge actions: {len(help_data['bridge_actions'])}")
        print(f"  Python tools: {len(help_data['python_tools'])}")
        print(f"  Tool chains: {len(help_data['tool_chains'])}")
        print(f"  Channels: {len(help_data['channels'])}")
        print(f"  Error codes: {len(help_data['error_codes'])}")
        print(f"  Examples: {len(help_data['examples'])}")


async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:10993/mobile/v1"
    app_filter = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Connecting to {url}...")
    async with aconnect_ws(url) as ws:
        if app_filter and app_filter != "help":
            demos = {
                "spatial-vibe": demo_spatial_vibe,
                "state-surveiller": demo_state_surveiller,
                "pocket-architect": demo_pocket_architect,
            }
            demo_fn = demos.get(app_filter)
            if demo_fn:
                await demo_fn(ws)
            else:
                print(f"Unknown app: {app_filter}. Use: spatial-vibe, state-surveiller, pocket-architect, help")
                return
        else:
            # Run all demos in sequence (disconnect and reconnect for each app)
            await demo_spatial_vibe(ws)
            await demo_state_surveiller(ws)
            await demo_pocket_architect(ws)

        if app_filter == "help" or not app_filter:
            await get_help(ws)


if __name__ == "__main__":
    asyncio.run(main())
