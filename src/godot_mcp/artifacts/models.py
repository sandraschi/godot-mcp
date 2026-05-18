from enum import StrEnum

from pydantic import BaseModel


class ArtifactType(StrEnum):
    SCENE = "scene"
    MESH = "mesh"
    MATERIAL = "material"
    PARTICLE_SYSTEM = "particle_system"
    SCRIPT = "script"
    PROJECT = "project"
    PREFAB = "prefab"


class Artifact(BaseModel):
    id: str = ""
    name: str
    description: str = ""
    artifact_type: ArtifactType
    version: str = "0.1.0"
    author: str = ""
    tags: list[str] = []
    file_path: str = ""
    file_size: int = 0
    thumbnail_url: str = ""
    download_url: str = ""
    created_at: str = ""
    updated_at: str = ""
    metadata: dict = {}


class ArtifactSearchResult(BaseModel):
    total: int = 0
    results: list[Artifact] = []
