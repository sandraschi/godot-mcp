"""REST routes for game_builder pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter

from godot_mcp.game_builder import service

router = APIRouter(prefix="/api/v1/game-builder", tags=["game-builder"])


class DesignRequest(BaseModel):
    game_concept: str


class PlanRequest(BaseModel):
    game_plan_json: str
    worldlabs_url: str = "http://127.0.0.1:10865"


class ComposeRequest(BaseModel):
    game_plan_json: str
    worlds_result_json: str = ""


class LogicRequest(BaseModel):
    game_plan_json: str
    game_project_path: str = ""


class ExportRequest(BaseModel):
    game_plan_json: str
    game_project_path: str
    itch_target: str = ""
    channel: str = "html"


class BuildRequest(BaseModel):
    game_concept: str
    worldlabs_url: str = "http://127.0.0.1:10865"
    game_project_path: str = ""
    ship: bool = False
    itch_target: str = ""


@router.post("/design")
async def design_route(body: DesignRequest):
    return await service.service_design_game(body.game_concept)


@router.post("/worlds")
async def worlds_route(body: PlanRequest):
    return await service.service_generate_worlds(body.game_plan_json, body.worldlabs_url)


@router.post("/compose")
async def compose_route(body: ComposeRequest):
    return await service.service_compose_scene(body.game_plan_json, body.worlds_result_json)


@router.post("/logic")
async def logic_route(body: LogicRequest):
    return await service.service_generate_logic(body.game_plan_json, body.game_project_path)


@router.post("/export")
async def export_route(body: ExportRequest):
    return await service.service_export_and_ship(
        body.game_plan_json,
        body.game_project_path,
        body.itch_target,
        body.channel,
    )


@router.post("/build")
async def build_route(body: BuildRequest):
    return await service.service_build_game(
        body.game_concept,
        body.worldlabs_url,
        body.game_project_path,
        body.ship,
        body.itch_target,
    )
