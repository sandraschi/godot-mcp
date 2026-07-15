"""Demonstrates performance profiling: snapshot, auto-sample, spike detection.

Requires: godot-mcp server running, Godot bridge connected.

Usage:
    uv run python demos/profile.py
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

    print("=== Profiling Demo ===")

    # 1. One-shot snapshot
    snap = await asyncio.to_thread(bridge.send, "profile_snapshot")
    print("Current metrics:")
    for k, v in snap["data"]["snapshot"].items():
        print(f"  {k}: {v}")

    # 2. Enable auto-sampling
    await asyncio.to_thread(bridge.send, "profile_enable", {"enabled": True})
    print("Auto-sampling enabled (recording 300 frames)")

    # 3. Let some frames pass
    await asyncio.sleep(3)

    # 4. Read history + spikes
    history = await asyncio.to_thread(bridge.send, "profile_history")
    data = history["data"]
    print(f"Recorded {data['frames']} frames")
    if data["spike_count"] > 0:
        print(f"Spikes detected: {data['spike_count']}")
        for s in data["spikes"]:
            print(f"  {s['metric']}: {s['value']:.2f} (mean {s['mean']:.2f}, std {s['std']:.2f})")
    else:
        print("No spikes detected — performance is stable")

    print("=== Demo complete ===")


if __name__ == "__main__":
    asyncio.run(demo())
