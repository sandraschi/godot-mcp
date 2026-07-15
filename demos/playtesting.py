"""Demonstrates deterministic playtesting: freeze, inject input, step-until, capture.

Requires: godot-mcp server running, Godot bridge connected, a Godot project loaded
with a CharacterBody3D named 'Player' that responds to 'jump' action.

Usage:
    uv run python demos/playtesting.py
"""
import asyncio
import json
import sys

sys.path.insert(0, "src")

from godot_mcp.services.godot_bridge import get_bridge


async def demo():
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            print(f"Bridge connect failed: {result.get('error')}")
            return

    print("=== Deterministic Playtesting Demo ===")

    # 1. Read initial state
    status = await asyncio.to_thread(bridge.send, "status")
    print(f"Godot {status['data']['godot_version']} @ {status['data']['fps']} FPS")

    # 2. Freeze the game clock
    await asyncio.to_thread(bridge.send, "game_time_freeze")
    print("Clock frozen")

    # 3. Add Player to watch group (if not already)
    await asyncio.to_thread(bridge.send, "state_watch_add", {"node": "Player"})

    # 4. Queue a jump input
    await asyncio.to_thread(bridge.send, "simulate_input", {
        "actions": [{"action": "jump", "strength": 1.0}]
    })
    print("Jump input queued")

    # 5. Step until Player lands
    result = await asyncio.to_thread(bridge.send, "game_time_step_until", {
        "condition": "get_node('Player').is_on_floor()",
        "timeout_frames": 600,
    })
    frames = result["data"]["frames_elapsed"]
    print(f"Player landed after {frames} frames")

    # 6. Read post-landing state
    state = await asyncio.to_thread(bridge.send, "state_digest", {"nodes": ["Player"]})
    print(f"Player state: {json.dumps(state['data']['nodes'], indent=2)}")

    # 7. Capture viewport
    cap = await asyncio.to_thread(bridge.send, "capture_viewport", {"output_path": "user://demo_jump.png"})
    print(f"Screenshot: {cap['data']['path']}")

    print("=== Demo complete ===")


if __name__ == "__main__":
    asyncio.run(demo())
