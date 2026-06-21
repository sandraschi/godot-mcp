"""
Godot MCP — Godot 4.0 engine control via FastMCP 3.2 Unified Gateway.

Provides programmatic access to Godot for STL import, GPU particles,
animation, material assignment, camera control, and scene export.

Exports (12 tools):
    godot_status — engine availability, version, node count, FPS
    godot_import_stl — import STL mesh from qcad-mcp/freecad-mcp pipeline
    godot_load_velocity_field — load FluidX3D CSV velocity field data
    godot_spawn_particles — GPU particle system with velocity fields
    godot_animate_streamlines — animate particles along streamlines
    godot_create_camera — create camera with orbit controls
    godot_add_light — add directional/ambient/omni lights
    godot_set_material — assign PBR materials to mesh surfaces
    godot_export_web — export scene to Web (HTML5)
    godot_read_scene_tree — dump scene hierarchy as JSON tree
    godot_set_config — write to project.godot config file
    godot_headless_verify — check headless mode + suggest CLI command
"""

from __future__ import annotations

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("godot-mcp")
