"""REST API routes for the artifact marketplace and depot."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from godot_mcp.artifacts.depot.store import get_depot
from godot_mcp.artifacts.models import Artifact, ArtifactType

router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])


@router.get("")
async def list_artifacts(
    type: str | None = None,
    skip: int = 0,
    limit: int = 50,
):
    depot = get_depot()
    at = None
    if type:
        try:
            at = ArtifactType(type)
        except ValueError:
            raise HTTPException(400, f"Invalid type: {type}")
    result = depot.list(artifact_type=at, skip=skip, limit=limit)
    return {"success": True, "total": result.total, "artifacts": [a.model_dump() for a in result.results]}


@router.get("/search")
async def search_artifacts(q: str, type: str | None = None):
    depot = get_depot()
    at = None
    if type:
        try:
            at = ArtifactType(type)
        except ValueError:
            raise HTTPException(400, f"Invalid type: {type}")
    result = depot.search(q, artifact_type=at)
    return {"success": True, "total": result.total, "artifacts": [a.model_dump() for a in result.results]}


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: str):
    depot = get_depot()
    artifact = depot.get(artifact_id)
    if not artifact:
        raise HTTPException(404, f"Artifact '{artifact_id}' not found")
    return {"success": True, "artifact": artifact.model_dump()}


@router.get("/{artifact_id}/download")
async def download_artifact(artifact_id: str):
    depot = get_depot()
    artifact = depot.get(artifact_id)
    if not artifact or not artifact.file_path:
        raise HTTPException(404, "Artifact or file not found")
    path = Path(artifact.file_path)
    if not path.exists():
        raise HTTPException(404, "File not found on disk")
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@router.post("")
async def register_artifact(
    name: str,
    artifact_type: str,
    description: str = "",
    author: str = "",
    tags: str = "",
):
    depot = get_depot()
    try:
        at = ArtifactType(artifact_type)
    except ValueError:
        raise HTTPException(400, f"Invalid type: {artifact_type}")
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    artifact = Artifact(name=name, description=description, artifact_type=at, author=author, tags=tag_list)
    result = depot.put(artifact)
    return {"success": True, "artifact": result.model_dump()}


@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: str):
    depot = get_depot()
    ok = depot.delete(artifact_id)
    if not ok:
        raise HTTPException(404, f"Artifact '{artifact_id}' not found")
    return {"success": True, "message": "Deleted"}
