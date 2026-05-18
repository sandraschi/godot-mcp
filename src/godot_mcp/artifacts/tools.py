"""MCP tools for artifact marketplace and depot management."""

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from godot_mcp.artifacts.depot.store import get_depot
from godot_mcp.artifacts.models import Artifact, ArtifactType

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


async def artifact_list(
    ctx: Context = None,
    artifact_type: Annotated[
        str | None,
        Field(
            description="Filter by type: scene, mesh, material, particle_system, script, project, prefab.", default=None
        ),
    ] = None,
    skip: Annotated[int, Field(description="Number of results to skip.", default=0, ge=0)] = 0,
    limit: Annotated[int, Field(description="Max results to return.", default=20, ge=1, le=100)] = 20,
) -> dict:
    """List artifacts in the local depot. Optionally filter by type.

    ## Return Format
    {"success": bool, "total": int, "artifacts": [...]}

    ## Examples
    await artifact_list()
    await artifact_list(artifact_type="mesh", limit=10)
    """
    depot = get_depot()
    at = None
    if artifact_type:
        try:
            at = ArtifactType(artifact_type)
        except ValueError:
            return {"success": False, "error": f"Invalid type: {artifact_type}"}
    result = depot.list(artifact_type=at, skip=skip, limit=limit)
    return {"success": True, "total": result.total, "artifacts": [a.model_dump() for a in result.results]}


async def artifact_search(
    query: Annotated[str, Field(description="Search query (matches name, description, tags).")],
    artifact_type: Annotated[str | None, Field(description="Optional type filter.", default=None)] = None,
    ctx: Context = None,
) -> dict:
    """Search artifacts in the local depot by name, description, or tags.

    ## Return Format
    {"success": bool, "total": int, "artifacts": [...]}

    ## Examples
    await artifact_search(query="river")
    await artifact_search(query="particle", artifact_type="particle_system")
    """
    depot = get_depot()
    at = None
    if artifact_type:
        try:
            at = ArtifactType(artifact_type)
        except ValueError:
            return {"success": False, "error": f"Invalid type: {artifact_type}"}
    result = depot.search(query, artifact_type=at)
    return {"success": True, "total": result.total, "artifacts": [a.model_dump() for a in result.results]}


async def artifact_get(
    artifact_id: Annotated[str, Field(description="Artifact ID to retrieve.")],
    ctx: Context = None,
) -> dict:
    """Get a single artifact's details by ID.

    ## Return Format
    {"success": bool, "artifact": {...}}

    ## Examples
    await artifact_get(artifact_id="abc12345")
    """
    depot = get_depot()
    artifact = depot.get(artifact_id)
    if not artifact:
        return {"success": False, "error": f"Artifact '{artifact_id}' not found"}
    return {"success": True, "artifact": artifact.model_dump()}


async def artifact_register(
    name: Annotated[str, Field(description="Artifact name.")],
    artifact_type: Annotated[
        str, Field(description="Type: scene, mesh, material, particle_system, script, project, prefab.")
    ],
    description: Annotated[str, Field(description="Description of the artifact.", default="")] = "",
    author: Annotated[str, Field(description="Author/creator name.", default="")] = "",
    tags: Annotated[list[str], Field(description="Search tags.", default=[])] = [],
    ctx: Context = None,
) -> dict:
    """Register a new artifact in the depot (metadata only, no file).

    ## Return Format
    {"success": bool, "artifact": {...}}

    ## Examples
    await artifact_register(name="River Scene", artifact_type="scene", tags=["water", "cfd"])
    """
    depot = get_depot()
    try:
        at = ArtifactType(artifact_type)
    except ValueError:
        return {"success": False, "error": f"Invalid type: {artifact_type}"}
    artifact = Artifact(
        name=name,
        description=description,
        artifact_type=at,
        author=author,
        tags=tags,
    )
    result = depot.put(artifact)
    return {"success": True, "artifact": result.model_dump()}


async def artifact_delete(
    artifact_id: Annotated[str, Field(description="Artifact ID to delete.")],
    ctx: Context = None,
) -> dict:
    """Delete an artifact from the depot.

    ## Return Format
    {"success": bool}

    ## Examples
    await artifact_delete(artifact_id="abc12345")
    """
    depot = get_depot()
    ok = depot.delete(artifact_id)
    return {"success": ok, "message": "Deleted" if ok else "Not found"}


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(artifact_list)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(artifact_search)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(artifact_get)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(artifact_register)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(artifact_delete)
