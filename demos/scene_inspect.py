"""Demonstrates scene inspection: read_node, state_digest, tilemap, inspect_resource.

Requires: godot-mcp server running, Godot bridge connected.

Usage:
    uv run python demos/scene_inspect.py
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

    print("=== Scene Inspection Demo ===")

    # 1. Read a single node by name
    player = await asyncio.to_thread(bridge.send, "read_node", {"node": "Player"})
    if player["success"]:
        pdata = player["data"]["node"]
        print(f"Player: type={pdata['type']}, path={pdata.get('path')}")
        if "position" in pdata:
            pos = pdata["position"]
            print(f"  Position: ({pos['x']:.2f}, {pos['y']:.2f}, {pos['z']:.2f})")
        if "velocity" in pdata:
            vel = pdata["velocity"]
            print(f"  Velocity: ({vel.get('x', 0):.2f}, {vel.get('y', 0):.2f})")
        children = pdata.get("children", [])
        if children:
            print(f"  Children: {len(children)}")
            for c in children[:5]:
                print(f"    - {c['name']} ({c['type']})")
    else:
        print("Player node not found — read_scene_tree instead")
        tree = await asyncio.to_thread(bridge.send, "read_scene_tree")
        print(f"Scene tree: {tree['data']['node_count']} nodes")

    # 2. Try tilemap read if any TileMapLayer exists
    # (find tilemap nodes by scanning the tree — simplified: try a common name)
    tilemap = await asyncio.to_thread(bridge.send, "tilemap_read", {"node": "GroundLayer"})
    if tilemap["success"]:
        data = tilemap["data"]
        print(f"TileMapLayer '{data['node']}': {data['cell_count']} cells")
        if data["cell_count"] > 0:
            print(f"  First cell: {json.dumps(data['cells'][0])}")
    else:
        print("No GroundLayer TileMapLayer found")

    # 3. Try inspect_resource if a known resource exists
    # (demonstrates the tool even if the resource doesn't exist)
    res = await asyncio.to_thread(bridge.send, "inspect_resource", {"path": "res://characters/player.tres"})
    if res["success"]:
        r = res["data"]["resource"]
        print(f"Resource: {r['type']}")
        if "animations" in r:
            print(f"  Animations: {r['animation_count']}")
        if "material" in r:
            print(f"  Material params: {json.dumps(r['material'], indent=2)}")
    else:
        print("Resource not found (expected — no player.tres in default project)")

    print("=== Demo complete ===")


if __name__ == "__main__":
    asyncio.run(demo())
