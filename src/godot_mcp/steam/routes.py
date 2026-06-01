"""REST routes for Steam publishing via steam-mcp."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from godot_mcp.steam import service

router = APIRouter(prefix="/api/v1/steam", tags=["steam"])


class StageRequest(BaseModel):
    game: str = "dodge"
    project_path: str | None = None
    app_id: int | None = None


class UploadRequest(BaseModel):
    content_root: str = ""
    dry_run: bool = True


class ShipRequest(BaseModel):
    game: str = "dodge"
    project_path: str | None = None
    phase: str = "prerelease"
    dry_run: bool = True


@router.get("/status")
async def steam_status_route():
    return service.steam_status()


@router.get("/checklist")
async def steam_checklist_route(content_root: str = ""):
    return service.steam_checklist(content_root)


@router.get("/monetization")
async def steam_monetization_route():
    return service.steam_monetization_guide()


@router.post("/stage")
async def steam_stage_route(body: StageRequest):
    return service.stage_windows_build(
        game=body.game,
        project_path=body.project_path,
        app_id=body.app_id,
    )


@router.post("/upload/prerelease")
async def steam_upload_prerelease_route(body: UploadRequest):
    return service.steam_upload_prerelease(body.content_root, dry_run=body.dry_run)


@router.post("/upload/release")
async def steam_upload_release_route(body: UploadRequest):
    return service.steam_upload_release(body.content_root, dry_run=body.dry_run)


@router.post("/ship")
async def steam_ship_route(body: ShipRequest):
    return service.ship_to_steam(
        game=body.game,
        project_path=body.project_path,
        phase=body.phase,
        dry_run=body.dry_run,
    )
