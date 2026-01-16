from fastapi import APIRouter, Query
from app.services.tmdb import tmdb_service

router = APIRouter()

@router.get("/trending")
async def get_trending_tv(time_window: str = Query("week", regex="^(day|week)$")):
    return await tmdb_service.get_trending_tv(time_window)

@router.get("/popular")
async def get_popular_tv():
    return await tmdb_service.get_popular_tv()

@router.get("/search")
async def search_tv(query: str = Query(..., min_length=1)):
    return await tmdb_service.search_tv(query)

@router.get("/{tv_id}")
async def get_tv_details(tv_id: int):
    return await tmdb_service.get_tv_details(tv_id)

@router.get("/{tv_id}/credits")
async def get_tv_credits(tv_id: int):
    return await tmdb_service.get_tv_credits(tv_id)

@router.get("/{tv_id}/videos")
async def get_tv_videos(tv_id: int):
    return await tmdb_service.get_tv_videos(tv_id)