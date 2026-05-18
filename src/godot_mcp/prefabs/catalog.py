"""Prefab catalog — reusable Godot component templates."""

from pydantic import BaseModel


class PrefabParameter(BaseModel):
    name: str
    type: str = "string"
    description: str = ""
    default: str | int | float | bool | None = None


class Prefab(BaseModel):
    id: str
    name: str
    description: str
    category: str = "general"
    tools: list[dict]
    parameters: list[PrefabParameter] = []
    tags: list[str] = []


PREFABS: dict[str, Prefab] = {
    "standard_lighting": Prefab(
        id="standard_lighting",
        name="Standard Lighting Setup",
        description="Adds a directional light + ambient fill for scene illumination.",
        category="lighting",
        tools=[
            {"tool": "godot_add_light", "params": {"light_type": "directional", "intensity": "{intensity}"}},
            {"tool": "godot_add_light", "params": {"light_type": "ambient", "intensity": 0.3}},
        ],
        parameters=[PrefabParameter(name="intensity", type="float", description="Light intensity", default=1.5)],
        tags=["lighting", "scene"],
    ),
    "orbit_camera": Prefab(
        id="orbit_camera",
        name="Orbit Camera",
        description="Creates a camera with orbit controls positioned above the scene.",
        category="camera",
        tools=[
            {
                "tool": "godot_create_camera",
                "params": {"name": "OrbitCam", "position_y": "{height}", "position_z": "{distance}", "fov": "{fov}"},
            },
        ],
        parameters=[
            PrefabParameter(name="height", type="float", description="Camera height", default=5.0),
            PrefabParameter(name="distance", type="float", description="Camera distance", default=10.0),
            PrefabParameter(name="fov", type="float", description="Field of view", default=75.0),
        ],
        tags=["camera", "orbit"],
    ),
    "cfd_particles": Prefab(
        id="cfd_particles",
        name="CFD Particle System",
        description="GPU particle system configured for velocity field visualization.",
        category="particles",
        tools=[
            {
                "tool": "godot_spawn_particles",
                "params": {"count": "{count}", "color": "{color}", "spread_x": 10, "spread_y": 10, "spread_z": 10},
            },
            {"tool": "godot_animate_streamlines", "params": {"speed": "{speed}"}},
        ],
        parameters=[
            PrefabParameter(name="count", type="int", description="Particle count", default=5000),
            PrefabParameter(name="color", type="string", description="Hex color", default="#00aaff"),
            PrefabParameter(name="speed", type="float", description="Animation speed", default=1.0),
        ],
        tags=["cfd", "particles", "fluid"],
    ),
    "pbr_material": Prefab(
        id="pbr_material",
        name="PBR Material",
        description="Assigns a StandardMaterial3D with configurable color and roughness.",
        category="materials",
        tools=[
            {
                "tool": "godot_set_material",
                "params": {"node": "{node}", "color": "{color}", "roughness": "{roughness}"},
            },
        ],
        parameters=[
            PrefabParameter(name="node", type="string", description="Target mesh node name"),
            PrefabParameter(name="color", type="string", description="Albedo hex color", default="#ffffff"),
            PrefabParameter(name="roughness", type="float", description="PBR roughness (0-1)", default=0.5),
        ],
        tags=["material", "pbr"],
    ),
}


def get_prefab(prefab_id: str) -> Prefab | None:
    return PREFABS.get(prefab_id)


def list_prefabs(category: str | None = None) -> list[Prefab]:
    if category:
        return [p for p in PREFABS.values() if p.category == category]
    return list(PREFABS.values())
