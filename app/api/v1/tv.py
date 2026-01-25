from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.services.tmdb import tmdb_service
from app.services.recommendation_service import recommendation_service
from app.core.database import get_db
from app.api.deps import get_verified_user
from app.models.user import User

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

@router.get("/providers")
async def get_watch_providers(region: str = Query("IN", description="ISO 3166-1 country code")):
    """Get list of streaming providers available in a region"""
    return await tmdb_service.get_watch_providers(region)

@router.get("/personalized")
async def get_personalized_tv(
    page: int = Query(1, ge=1, le=500, description="Page number"),
    vote_count_min: int = Query(500, ge=0, description="Minimum vote count"),
    vote_average_min: float = Query(6.5, ge=0, le=10, description="Minimum rating"),
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized TV recommendations based on your rating history
    - New users: Popular/trending shows
    - Few ratings (5-19): Top 2 favorite genres
    - Many ratings (20+): Full personalization with top 3 genres
    """
    return await recommendation_service.get_personalized_tv(
        user_id=str(current_user.id),
        db=db,
        page=page,
        vote_count_min=vote_count_min,
        vote_average_min=vote_average_min
    )

@router.get("/discover")
async def discover_tv(
    genre: Optional[str] = Query(None, description="Comma-separated genre IDs"),
    year: Optional[int] = Query(None, ge=1900, le=2030, description="First air date year"),
    language: Optional[str] = Query(None, description="ISO 639-1 language code (e.g. 'en', 'hi')"),
    country: Optional[str] = Query(None, description="ISO 3166-1 country code (e.g. 'US', 'IN')"),
    provider: Optional[str] = Query(None, description="Comma-separated provider IDs (e.g. '8,119')"),
    sort_by: str = Query("popularity.desc", description="Sort by: popularity.desc, vote_average.desc, first_air_date.desc"),
    page: int = Query(1, ge=1, le=500, description="Page number"),
    vote_count_min: int = Query(100, ge=0, description="Minimum vote count"),
    vote_average_min: Optional[float] = Query(None, ge=0, le=10, description="Minimum rating (0-10)"),
    vote_average_max: Optional[float] = Query(None, ge=0, le=10, description="Maximum rating (0-10)"),
):
    """
    Discover TV shows with filters
    Example: /tv/discover?provider=119&language=hi&country=IN&vote_average_min=7.5
    """
    return await tmdb_service.discover_tv(
        genre=genre,
        year=year,
        language=language,
        country=country,
        provider=provider,
        sort_by=sort_by,
        page=page,
        vote_count_min=vote_count_min,
        vote_average_min=vote_average_min,
        vote_average_max=vote_average_max,
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

@router.get("/{tv_id}/providers")
async def get_tv_watch_providers(tv_id: int):
    """Get streaming providers where this TV show is available"""
    return await tmdb_service.get_tv_watch_providers(tv_id)

@router.get("/{tv_id}/recommendations")
async def get_tv_recommendations(
    tv_id: int,
    page: int = Query(1, ge=1, le=500, description="Page number")
):
    """Get TMDB's ML-based recommendations for a TV show"""
    return await tmdb_service.get_tv_recommendations(tv_id, page)

@router.get("/{tv_id}/similar")
async def get_similar_tv(
    tv_id: int,
    page: int = Query(1, ge=1, le=500, description="Page number")
):
    """Get TV shows similar to this one"""
    return await tmdb_service.get_similar_tv(tv_id, page)