"""REST routes for fleet maker pipelines."""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter

from godot_mcp.fleet import service

router = APIRouter(prefix="/api/v1/fleet", tags=["fleet"])


class ExchangeImportRequest(BaseModel):
    path: str
    name: str = "FleetImport"
    scale: float = 1.0


class WorldLabsImportRequest(BaseModel):
    world_id: str
    node_name: str | None = None
    scale: float = 1.0


class WorldLabsSplatRequest(BaseModel):
    world_id: str
    resolution: str = "500k"


@router.get("/status")
async def fleet_status_route():
    return service.fleet_exchange_status()


@router.post("/exchange/import")
async def exchange_import_route(body: ExchangeImportRequest):
    return service.fleet_import_from_exchange(body.path, name=body.name, scale=body.scale)


@router.get("/worldlabs/{world_id}")
async def worldlabs_world_route(world_id: str):
    return service.fleet_worldlabs_get_world(world_id)


@router.post("/worldlabs/stage-mesh")
async def worldlabs_stage_mesh_route(body: WorldLabsImportRequest):
    return service.fleet_worldlabs_stage_mesh(body.world_id)


@router.post("/worldlabs/stage-splat")
async def worldlabs_stage_splat_route(body: WorldLabsSplatRequest):
    return service.fleet_worldlabs_stage_splat(body.world_id, resolution=body.resolution)


@router.post("/worldlabs/import-mesh")
async def worldlabs_import_mesh_route(body: WorldLabsImportRequest):
    return service.fleet_worldlabs_import_mesh(body.world_id, node_name=body.node_name, scale=body.scale)
