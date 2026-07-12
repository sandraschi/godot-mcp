#!/usr/bin/env python3
"""Game Builder E2E smoke test - design -> logic -> validate, no bridge/worldlabs needed.

Usage:
    uv run python scripts/gb-smoke.py
    GODOT_MCP_OLLAMA_MODEL=llama3.2:3b uv run python scripts/gb-smoke.py

Requires: Ollama or OpenAI-compatible API at GODOT_MCP_LLM_BASE_URL.
Skips gracefully if no LLM is available.
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

START = time.time()

_OK = "\N{CHECK MARK}" if sys.platform != "win32" else "PASS"
_FAIL = "\N{CROSS MARK}" if sys.platform != "win32" else "FAIL"


def log(step: str, status: str, detail: str = ""):
    elapsed = time.time() - START
    icon = {"PASS": _OK, "FAIL": _FAIL, "SKIP": "SKIP"}.get(status, "INFO")
    print(f"  [{elapsed:5.1f}s] [{icon}] {step}  {detail}", flush=True)


def check_llm() -> bool:
    """Quick probe: is Ollama or GODOT_MCP_LLM_BASE_URL reachable?"""
    import urllib.request

    base = os.environ.get("GODOT_MCP_LLM_BASE_URL", "").rstrip("/")
    if base:
        url = base + "/models"
    else:
        url = "http://localhost:11434/api/tags"
    try:
        urllib.request.urlopen(url, timeout=3)
        return True
    except Exception:
        return False


def main():
    print("=" * 60, flush=True)
    print("  Godot MCP - Game Builder Smoke Test", flush=True)
    print("=" * 60, flush=True)

    if not check_llm():
        log("LLM probe", "SKIP", "No Ollama or GODOT_MCP_LLM_BASE_URL reachable")
        print("\n  Install Ollama (ollama.com) or set GODOT_MCP_LLM_BASE_URL.", flush=True)
        return 0

    from godot_mcp.game_builder.pipeline import design_game, generate_game_logic
    from godot_mcp.game_builder.plan import GamePlan

    passed = 0
    failed = 0

    log("design_game", "RUN", "Designing 'dodge the creeps' ...")
    try:
        import asyncio

        plan: GamePlan = asyncio.run(
            design_game("A 2D dodge game where the player avoids falling obstacles. Arrow keys to move.")
        )
        assert plan.title, "GamePlan has no title"
        assert plan.genre, "GamePlan has no genre"
        assert plan.viewport in ("2d", "3d"), f"Unexpected viewport: {plan.viewport}"
        assert plan.scenes, "GamePlan has no scenes"
        assert plan.scripts, "GamePlan has no scripts"
        assert plan.controls, "GamePlan has no controls"
        log(
            "design_game",
            "PASS",
            f"'{plan.title}' ({plan.genre}), {len(plan.scenes)} scenes, {len(plan.scripts)} scripts, {len(plan.worlds)} worlds",
        )
        passed += 1
    except Exception as e:
        log("design_game", "FAIL", str(e))
        return 1

    log("plan round-trip", "RUN", "Plan -> JSON -> Plan ...")
    try:
        raw = plan.to_json()
        reloaded = GamePlan.from_json(raw)
        assert reloaded.title == plan.title
        assert len(reloaded.scenes) == len(plan.scenes)
        assert len(reloaded.scripts) == len(plan.scripts)
        log("plan round-trip", "PASS", f"GamePlan JSON round-trip OK ({len(raw)} bytes)")
        passed += 1
    except Exception as e:
        log("plan round-trip", "FAIL", str(e))
        failed += 1

    log("generate_game_logic", "RUN", "Generating GDScript files ...")
    try:
        result = asyncio.run(generate_game_logic(plan, ctx=None))
        scripts = result.get("scripts", {})
        assert scripts, "No scripts generated"
        generated = sum(1 for s in scripts.values() if s.get("generated"))
        assert generated > 0, f"No successfully generated scripts (got {len(scripts)} total)"
        log("generate_game_logic", "PASS", f"{generated}/{len(scripts)} scripts generated")
        passed += 1
    except Exception as e:
        log("generate_game_logic", "FAIL", str(e))
        failed += 1

    script_names = list(result.get("scripts", {}).keys())
    log("gdscript validate", "RUN", f"Checking {len(script_names)} scripts ...")
    try:
        for name, data in result.get("scripts", {}).items():
            code = data.get("code", "")
            if "extends " not in code:
                log("gdscript validate", "FAIL", f"Script '{name}' missing 'extends'")
                failed += 1
                continue
            if "func " not in code and "signal " not in code and "var " not in code:
                log("gdscript validate", "FAIL", f"Script '{name}' has no functions, signals, or vars")
                failed += 1
                continue
            for bad in ("def ", "import ", "class ", "if __name__"):
                if bad in code:
                    log("gdscript validate", "FAIL", f"Script '{name}' contains Python pattern '{bad}'")
                    failed += 1
                    continue
        log("gdscript validate", "PASS", f"{len(script_names)} scripts pass basic GDScript checks")
        passed += 1
    except Exception as e:
        log("gdscript validate", "FAIL", str(e))
        failed += 1

    total = passed + failed
    print("=" * 60, flush=True)
    print(f"  Result: {passed}/{total} passed", flush=True)
    if failed:
        print(f"  {failed} step(s) failed", flush=True)
        return 1
    print("  All steps passed.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
