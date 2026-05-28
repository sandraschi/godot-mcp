"""REST routes for itch.io / Butler publishing."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from godot_mcp.itch import service

router = APIRouter(prefix="/api/v1/itch", tags=["itch"])


class PushRequest(BaseModel):
    upload_dir: str
    itch_target: str | None = None
    channel: str | None = None
    hidden: bool = False


class ExportRequest(BaseModel):
    target: str = "web"
    game: str = "dodge"
    project_path: str | None = None
    output_path: str | None = None


class ShipRequest(BaseModel):
    target: str = "web"
    game: str = "dodge"
    project_path: str | None = None
    itch_target: str | None = None
    channel: str | None = None
    preview: bool = True
    push: bool = True
    hidden: bool = False


@router.get("/status")
async def itch_status_route():
    return service.itch_status()


@router.post("/export")
async def export_route(body: ExportRequest):
    return service.godot_export_release_tool(
        target=body.target,
        game=body.game,
        project_path=body.project_path,
        output_path=body.output_path,
    )


@router.post("/push-preview")
async def push_preview_route(body: PushRequest):
    return service.itch_push_preview(
        body.upload_dir,
        itch_target=body.itch_target,
        channel=body.channel,
    )


@router.post("/push")
async def push_route(body: PushRequest):
    return service.itch_push(
        body.upload_dir,
        itch_target=body.itch_target,
        channel=body.channel,
        hidden=body.hidden,
    )


@router.post("/ship")
async def ship_route(body: ShipRequest):
    return service.ship_to_itch(
        target=body.target,
        game=body.game,
        project_path=body.project_path,
        itch_target=body.itch_target,
        channel=body.channel,
        preview=body.preview,
        push=body.push,
        hidden=body.hidden,
    )


@router.get("/latest")
async def latest_route(itch_target: str | None = None, channel: str | None = None):
    return service.itch_latest_version(itch_target=itch_target, channel=channel)
