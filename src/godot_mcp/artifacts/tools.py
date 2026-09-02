"""MCP tools for artifact marketplace and depot management."""

from pathlib import Path
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
        str, Field(description="Type: scene, mesh, material, particle_system, script, project, prefab, texture.")
    ],
    description: Annotated[str, Field(description="Description of the artifact.", default="")] = "",
    author: Annotated[str, Field(description="Author/creator name.", default="")] = "",
    tags: Annotated[list[str], Field(description="Search tags.", default=[])] = [],
    source_path: Annotated[
        str | None,
        Field(
            description=(
                "Local file path to copy into the depot (2026-09-03 - previously this "
                "parameter didn't exist and depot.put()'s file-copy capability was "
                "unreachable from any tool). Must already exist on disk; not a URL."
            ),
            default=None,
        ),
    ] = None,
    ctx: Context = None,
) -> dict:
    """Register a new artifact in the depot, optionally attaching a file.

    ## Return Format
    {"success": bool, "artifact": {...}}

    ## Examples
    await artifact_register(name="River Scene", artifact_type="scene", tags=["water", "cfd"])
    await artifact_register(name="Oak Tree", artifact_type="mesh", source_path="C:/models/oak.glb")
    """
    depot = get_depot()
    try:
        at = ArtifactType(artifact_type)
    except ValueError:
        return {"success": False, "error": f"Invalid type: {artifact_type}"}

    src: Path | None = None
    if source_path is not None:
        src = Path(source_path)
        if not src.exists():
            return {"success": False, "error": f"source_path not found: {source_path}"}

    artifact = Artifact(
        name=name,
        description=description,
        artifact_type=at,
        author=author,
        tags=tags,
    )
    result = depot.put(artifact, source_path=src)
    return {"success": True, "artifact": result.model_dump()}


async def artifact_update(
    artifact_id: Annotated[str, Field(description="Artifact ID to edit.")],
    name: Annotated[str | None, Field(description="New name.", default=None)] = None,
    description: Annotated[str | None, Field(description="New description.", default=None)] = None,
    tags: Annotated[list[str] | None, Field(description="Replacement tag list.", default=None)] = None,
    author: Annotated[str | None, Field(description="New author/creator name.", default=None)] = None,
    ctx: Context = None,
) -> dict:
    """Edit an artifact's metadata (name/description/tags/author). The attached file, if any,
    is untouched - only fields explicitly given are changed.

    Added 2026-09-03: no metadata-edit tool existed before this, only register+delete.

    ## Return Format
    {"success": bool, "artifact": {...}}

    ## Examples
    await artifact_update(artifact_id="abc12345", description="Updated river scene")
    """
    depot = get_depot()
    artifact = depot.update(artifact_id, name=name, description=description, tags=tags, author=author)
    if artifact is None:
        return {"success": False, "error": f"Artifact '{artifact_id}' not found"}
    return {"success": True, "artifact": artifact.model_dump()}


async def artifact_backup(ctx: Context = None) -> dict:
    """Zip-snapshot the depot's files/thumbs/index.json into a timestamped backup archive.

    Added 2026-09-03 - no backup/restore existed before this (same gap overte-mcp/resonite-mcp
    had before their own depot backup features were added earlier this session).

    ## Return Format
    {"success": bool, "name": str, "size": int}

    ## Examples
    await artifact_backup()
    """
    depot = get_depot()
    result = depot.backup()
    return {"success": True, **result}


async def artifact_list_backups(ctx: Context = None) -> dict:
    """List available depot backup archives, newest first.

    ## Return Format
    {"success": bool, "backups": [{"name","size","created_at"}], "count": int}

    ## Examples
    await artifact_list_backups()
    """
    depot = get_depot()
    backups = depot.list_backups()
    return {"success": True, "backups": backups, "count": len(backups)}


async def artifact_restore_backup(
    name: Annotated[str, Field(description="Backup archive filename, from artifact_list_backups.")],
    ctx: Context = None,
) -> dict:
    """Restore a depot backup archive, OVERWRITING current files/thumbs/index.json (matching
    names only - does not delete entries the backup doesn't mention).

    ## Return Format
    {"success": bool, "count": int}

    ## Examples
    await artifact_restore_backup(name="godot-mcp-depot-backup-20260903T000000Z.zip")
    """
    depot = get_depot()
    result = depot.restore_backup(name)
    if not result.get("restored"):
        return {"success": False, "error": result.get("error", "Restore failed")}
    return {"success": True, "count": result["count"]}


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
    mcp.tool(annotations=_MUTATING, version="0.1.0")(artifact_update)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(artifact_delete)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(artifact_backup)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(artifact_list_backups)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(artifact_restore_backup)
