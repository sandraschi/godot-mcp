"""GamePlan schema — what the LLM outputs from a natural-language game concept."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class WorldSpec(BaseModel):
    """One Marble-generated world in the game."""

    id: str = Field(description="Short identifier (e.g. 'level_background').")
    name: str = Field(default="", description="Display name for the world.")
    prompt: str = Field(description="Marble text prompt for world generation.")
    model: str = Field(default="marble-1.1", description="Marble model.")
    usage: str = Field(
        default="environment",
        description="Role: 'background', 'level_blockout', 'parallax_layer', 'skybox', or 'environment'.",
    )


class SceneSpec(BaseModel):
    """One node in the Godot scene tree. Can have nested children."""

    name: str = Field(description="Node name (e.g. 'Player', 'Camera', 'HUD').")
    type: str = Field(default="Node2D", description="Node type: Node2D, Node3D, Control, CharacterBody2D, etc.")
    scripts: list[str] = Field(default_factory=list, description="GDScript filenames attached to this node.")
    children: list[SceneSpec] = Field(default_factory=list, description="Child nodes — nested scene hierarchy.")


# Resolve forward ref for recursive SceneSpec.children
SceneSpec.model_rebuild()


class ScriptSpec(BaseModel):
    """One GDScript file the LLM will generate."""

    name: str = Field(description="Filename (e.g. 'player.gd').")
    description: str = Field(description="What this script should do. Used as LLM prompt.")


class AssetSpec(BaseModel):
    """An external asset needed by the game."""

    name: str = Field(description="Asset filename (e.g. 'player_icon.png').")
    description: str = Field(default="", description="What the asset depicts (for generation).")


class PlayerSpec(BaseModel):
    """Player controller configuration."""

    type: str = Field(default="runner", description="'runner', 'platformer', 'topdown', or 'fps'.")
    speed: float = Field(default=600.0, description="Movement speed in pixels/sec or units/sec.")
    jump: float = Field(default=-500.0, description="Jump velocity (negative for upward).")
    gravity: float = Field(default=1200.0, description="Gravity acceleration.")


class HazardSpec(BaseModel):
    """One enemy or obstacle type."""

    name: str = Field(description="Enemy name (e.g. 'drone').")
    behavior: str = Field(default="sine", description="Movement pattern: 'sine', 'linear', 'chase', 'static'.")
    speed: float = Field(default=200.0)
    color: str = Field(default="#ff4444", description="Hex color for procedural visuals.")


class NPCSpec(BaseModel):
    """A non-player character with dialogue."""

    name: str = Field(description="NPC name (e.g. 'Old Sage', 'Shopkeeper').")
    role: str = Field(
        default="", description="Role in the game: 'quest_giver', 'merchant', 'enemy', 'ally', 'background'."
    )
    dialogues: list[str] = Field(
        default_factory=list, description="Lines of dialogue this NPC says during interactions."
    )
    position: list[float] = Field(default_factory=lambda: [0.0, 0.0], description="2D or 3D position in the scene.")


class NarrativeArc(BaseModel):
    """Story structure for the game."""

    premise: str = Field(default="", description="One-sentence premise / high concept.")
    acts: list[str] = Field(default_factory=list, description="Major story beats (2-4 acts).")
    tone: str = Field(default="neutral", description="Story tone: 'heroic', 'dark', 'comedy', 'mystery', 'neutral'.")


class ScoringSpec(BaseModel):
    """Scoring / progression system."""

    type: str = Field(default="distance", description="'distance', 'score', 'time', or 'kills'.")
    unit_label: str = Field(default="m", description="Unit label (e.g. 'm', 'pts', 's').")


class LightingSpec(BaseModel):
    """Lighting configuration."""

    directional_enabled: bool = Field(default=True)
    directional_intensity: float = Field(default=0.4)
    ambient_color: str = Field(default="#1a1a2e")
    ambient_intensity: float = Field(default=0.3)


class CameraSpec(BaseModel):
    """Camera configuration."""

    position: list[float] = Field(default_factory=lambda: [0.0, 0.0, 10.0])
    fov: float = Field(default=75.0)


class ExportSpec(BaseModel):
    """Export target settings."""

    target: Literal["web", "windows"] = Field(default="web")
    resolution: list[int] = Field(default_factory=lambda: [1280, 720])
    itch_target: str = Field(default="", description="itch.io user/game slug.")


class GamePlan(BaseModel):
    """Complete AI-generated game plan."""

    title: str = Field(description="Game title.")
    description: str = Field(default="", description="Short game description.")
    genre: str = Field(default="arcade", description="Game genre.")
    engine: str = Field(default="godot4", description="Target engine.")
    viewport: Literal["2d", "3d"] = Field(default="2d", description="2D or 3D viewport.")

    worlds: list[WorldSpec] = Field(default_factory=list, description="Marble worlds to generate.")
    scenes: list[SceneSpec] = Field(default_factory=list, description="Godot scene structure.")
    scripts: list[ScriptSpec] = Field(default_factory=list, description="GDScript files to generate.")
    assets: list[AssetSpec] = Field(default_factory=list, description="External assets needed.")

    player: PlayerSpec | None = Field(default=None, description="Player controller config.")
    hazards: list[HazardSpec] = Field(default_factory=list, description="Enemy/obstacle types.")
    scoring: ScoringSpec | None = Field(default=None, description="Scoring system.")

    npcs: list[NPCSpec] = Field(default_factory=list, description="Non-player characters with dialogue.")
    narrative: NarrativeArc | None = Field(default=None, description="Story arc / narrative structure.")

    lighting: LightingSpec | None = Field(default=None, description="Lighting config (3D only).")
    camera: CameraSpec | None = Field(default=None, description="Camera config.")

    export: ExportSpec | None = Field(default=None, description="Export / shipping settings.")

    controls: dict[str, str] = Field(
        default_factory=lambda: {"jump": "space", "slide": "down", "shoot": "left_click"},
        description="Input map (action -> key).",
    )

    procedural_visuals: dict[str, Any] = Field(
        default_factory=lambda: {"palette": ["#ff4444", "#4444ff", "#44ff44"], "style": "flat"},
        description="Procedural visual style: palette (list of hex colors), style (flat, gradient, outline, neon).",
    )

    plugins: list[str] = Field(
        default_factory=list,
        description="Godot plugins to auto-install: 'dialogic' (dialogue), 'godot-behavior-tree' (AI), 'gut' (testing), 'aseprite-wizard' (sprites), 'terrain3d', 'godot-voxel', 'godot-xr-tools'.",
    )

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, raw: str | bytes) -> GamePlan:
        import json

        data = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
        if not isinstance(data, dict):
            raise ValueError("GamePlan must be a JSON object")

        # Strip null values so pydantic defaults apply
        for key in list(data.keys()):
            if data[key] is None:
                if cls.model_fields.get(key) and cls.model_fields[key].get_default() is not None:
                    del data[key]
                continue
            if isinstance(data[key], dict):
                data[key] = {k: v for k, v in data[key].items() if v is not None}
                if key == "controls" and not data[key]:
                    del data[key]

        # Fix common LLM output issues with Literal fields
        export = data.get("export")
        if isinstance(export, dict) and "target" in export:
            t = str(export["target"])
            if t and t not in ("web", "windows"):
                export["target"] = t.split("|")[0].strip() if "|" in t else "web"

        return cls.model_validate(data)
