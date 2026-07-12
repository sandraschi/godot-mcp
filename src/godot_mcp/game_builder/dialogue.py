"""Dialogic timeline and dialogue script generation from GamePlan narrative."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("godot-mcp.dialogue")


def generate_dialogue_manager(project_path: str, npcs: list[dict], narrative: dict | None = None) -> dict[str, Any]:
    """Generate a GDScript dialogue manager from GamePlan NPC + narrative data.

    Creates a self-contained dialogue system that works without Dialogic.
    If Dialogic is installed, also generates .dtl timeline files.

    Returns paths to all generated files.
    """
    project = Path(project_path)
    scripts_dir = project / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    generated = []

    # Generate the DialogueManager.gd script
    lines = [
        "extends Node",
        "",
        "## Auto-generated dialogue manager",
        "",
        "var current_dialogues: Dictionary = {}",
        "",
        "func _ready():",
        "	_register_dialogues()",
        "",
        "func _register_dialogues():",
    ]

    if not npcs:
        lines.append("	pass")

    for npc in npcs:
        name = npc.get("name", "NPC")
        dialogues = npc.get("dialogues", [])
        lines.append(f"	# {name}")
        lines.append(f'	current_dialogues["{name}"] = [')
        for d in dialogues:
            safe = d.replace('"', '\\"').replace("'", "\\'")
            lines.append(f'		"{safe}",')
        lines.append("	]")

    lines += [
        "",
        "func get_dialogue(npc_name: String) -> Array:",
        "	return current_dialogues.get(npc_name, [])",
        "",
        "func show_dialogue(npc_name: String, index: int = 0) -> String:",
        "	var lines = get_dialogue(npc_name)",
        "	if index < lines.size():",
        "		return lines[index]",
        '	return ""',
    ]

    if narrative:
        premise = narrative.get("premise", "").replace('"', '\\"')
        acts = narrative.get("acts", [])
        tone = narrative.get("tone", "neutral")
        lines += [
            "",
            "## Narrative context",
            f'const PREMISE: String = "{premise}"',
            f'const TONE: String = "{tone}"',
            f"const ACTS: Array = [{', '.join(f'"{a}"' for a in acts)}]",
        ]

    manager_path = scripts_dir / "DialogueManager.gd"
    manager_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    generated.append(str(manager_path))

    # Generate .dtl files for Dialogic if installed
    dialogic_dir = project / "addons" / "dialogic"
    if dialogic_dir.is_dir():
        dtl_dir = project / "dialogic" / "timelines"
        dtl_dir.mkdir(parents=True, exist_ok=True)

        for npc in npcs:
            name = npc.get("name", "NPC")
            dialogues = npc.get("dialogues", [])
            if not dialogues:
                continue

            dtl_events = []
            for i, d in enumerate(dialogues):
                safe = d.replace('"', '\\"').replace("\n", "\\n")
                dtl_events.append(f'{{"event_id": "dialogic_001", "character": "{name}", "text": "{safe}"}}')

            dtl_content = f"""[gd_resource type="Resource" load_steps=2 format=3 uid="uid://dtl_{name.lower().replace(" ", "_")}"]

[ext_resource type="Script" path="res://addons/dialogic/Modules/Composer/timeline_resource.gd" id="1_timeline"]

[resource]
resource_script = ExtResource("1_timeline")
events = [{", ".join(dtl_events)}]
"""
            dtl_path = dtl_dir / f"{name.lower().replace(' ', '_')}.dtl"
            dtl_path.write_text(dtl_content, encoding="utf-8")
            generated.append(str(dtl_path))

    return {"success": True, "files": generated, "count": len(generated)}
