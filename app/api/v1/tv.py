from fastapi import APIRouter, Query
from typing import Optional
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

@router.get("/genres")
async def get_tv_genres():
    """Get list of TV genres"""
    return await tmdb_service.get_tv_genres()

@router.get("/discover")
async def discover_tv(
    genre: Optional[str] = Query(None, description="Comma-separated genre IDs"),
    year: Optional[int] = Query(None, ge=1900, le=2030, description="First air date year"),
    language: Optional[str] = Query(None, description="ISO 639-1 language code (e.g. 'en', 'hi')"),
    country: Optional[str] = Query(None, description="ISO 3166-1 country code (e.g. 'US', 'IN')"),
    sort_by: str = Query("popularity.desc", description="Sort by: popularity.desc, vote_average.desc, first_air_date.desc"),
    page: int = Query(1, ge=1, le=500, description="Page number")
):
    """
    Discover TV shows with filters
    Example: /tv/discover?genre=18&year=2023&language=hi&sort_by=vote_average.desc
    """
    return await tmdb_service.discover_tv(
        genre=genre,
        year=year,
        language=language,
        country=country,
        sort_by=sort_by,
        page=page
    )

@router.get("/{tv_id}")
async def get_tv_details(tv_id: int):
    return await tmdb_service.get_tv_details(tv_id)

@router.get("/{tv_id}/credits")
async def get_tv_credits(tv_id: int):
    return await tmdb_service.get_tv_credits(tv_id)

@router.get("/{tv_id}/videos")
async def get_tv_videos(tv_id: int):
    return await tmdb_service.get_tv_videos(tv_id)