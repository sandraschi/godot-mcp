"""Demonstrates importing a 3D Gaussian Splatting scene into Godot.

Supports both .ply and .spz (compressed) files. World Labs splats use cm
units — pass pos_scale=0.01 for correct Godot-scale positioning.

Usage:
    uv run python demos/splat_import.py <path/to/scene.ply>
"""
import asyncio
import sys

sys.path.insert(0, "src")

from godot_mcp.services.godot_bridge import get_bridge


async def demo(file_path: str):
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            print(f"Bridge connect failed: {result.get('error')}")
            return

    print(f"=== Splat Import Demo ===")
    print(f"File: {file_path}")

    # Decompress/parse on Python side, send compact binary to bridge
    from godot_mcp.services.splat_import import import_splat_file
    result = import_splat_file(file_path, output_name="demo_splat", max_splats=200000, pos_scale=0.01)
    if not result["success"]:
        print(f"Parse failed: {result.get('error')}")
        return

    print(f"Parsed {result['count']} splats")

    # Send to Godot bridge
    bridge_result = await asyncio.to_thread(
        bridge.send,
        "import_splat",
        {"path": result["binary_path"], "name": "DemoSplatCloud"},
        timeout=60,
    )

    if bridge_result["success"]:
        d = bridge_result["data"]
        print(f"Imported {d['splat_count']} splats as '{d['name']}'")
        print(f"Gaussian shader: {'yes' if d.get('shader') else 'NO — using fallback'}")
        print(f"Per-splat scales: {'yes' if d.get('scales') else 'no'}")
    else:
        print(f"Import failed: {bridge_result.get('error')}")

    print("=== Demo complete ===")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python demos/splat_import.py <path.ply>")
        sys.exit(1)
    asyncio.run(demo(sys.argv[1]))
