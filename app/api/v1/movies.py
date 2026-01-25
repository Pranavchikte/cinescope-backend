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
async def get_trending_movies(time_window: str = Query("week", regex="^(day|week)$")):
    return await tmdb_service.get_trending_movies(time_window)

@router.get("/popular")
async def get_popular_movies():
    return await tmdb_service.get_popular_movies()

@router.get("/search")
async def search_movies(query: str = Query(..., min_length=1)):
    return await tmdb_service.search_movies(query)

@router.get("/genres")
async def get_movie_genres():
    """Get list of movie genres"""
    return await tmdb_service.get_movie_genres()

@router.get("/providers")
async def get_watch_providers(region: str = Query("IN", description="ISO 3166-1 country code")):
    """Get list of streaming providers available in a region"""
    return await tmdb_service.get_watch_providers(region)

@router.get("/personalized")
async def get_personalized_movies(
    page: int = Query(1, ge=1, le=500, description="Page number"),
    vote_count_min: int = Query(500, ge=0, description="Minimum vote count"),
    vote_average_min: float = Query(6.5, ge=0, le=10, description="Minimum rating"),
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized movie recommendations based on your rating history
    - New users: Popular/trending movies
    - Few ratings (5-19): Top 2 favorite genres
    - Many ratings (20+): Full personalization with top 3 genres
    """
    return await recommendation_service.get_personalized_movies(
        user_id=str(current_user.id),
        db=db,
        page=page,
        vote_count_min=vote_count_min,
        vote_average_min=vote_average_min
    )

@router.get("/discover")
async def discover_movies(
    genre: Optional[str] = Query(None, description="Comma-separated genre IDs (e.g. '28,12')"),
    year: Optional[int] = Query(None, ge=1900, le=2030, description="Release year"),
    language: Optional[str] = Query(None, description="ISO 639-1 language code (e.g. 'en', 'hi')"),
    country: Optional[str] = Query(None, description="ISO 3166-1 country code (e.g. 'US', 'IN')"),
    provider: Optional[str] = Query(None, description="Comma-separated provider IDs (e.g. '8,119' for Netflix,Prime)"),
    sort_by: str = Query("popularity.desc", description="Sort by: popularity.desc, vote_average.desc, release_date.desc"),
    page: int = Query(1, ge=1, le=500, description="Page number"),
    vote_count_min: int = Query(100, ge=0, description="Minimum vote count (filters low-quality content)"),
    vote_average_min: Optional[float] = Query(None, ge=0, le=10, description="Minimum rating (0-10)"),
    vote_average_max: Optional[float] = Query(None, ge=0, le=10, description="Maximum rating (0-10)"),
    runtime_min: Optional[int] = Query(None, ge=0, description="Minimum runtime in minutes"),
    runtime_max: Optional[int] = Query(None, ge=0, description="Maximum runtime in minutes"),
):
    """
    Discover movies with filters
    Example: /movies/discover?genre=28&provider=8,119&country=IN&vote_count_min=500&vote_average_min=7.0
    """
    return await tmdb_service.discover_movies(
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
        runtime_min=runtime_min,
        runtime_max=runtime_max,
    )

@router.get("/{movie_id}")
async def get_movie_details(movie_id: int):
    return await tmdb_service.get_movie_details(movie_id)

@router.get("/{movie_id}/credits")
async def get_movie_credits(movie_id: int):
    return await tmdb_service.get_movie_credits(movie_id)

@router.get("/{movie_id}/videos")
async def get_movie_videos(movie_id: int):
    return await tmdb_service.get_movie_videos(movie_id)

@router.get("/{movie_id}/providers")
async def get_movie_watch_providers(movie_id: int):
    """Get streaming providers where this movie is available"""
    return await tmdb_service.get_movie_watch_providers(movie_id)

@router.get("/{movie_id}/recommendations")
async def get_movie_recommendations(
    movie_id: int,
    page: int = Query(1, ge=1, le=500, description="Page number")
):
    """Get TMDB's ML-based recommendations for a movie"""
    return await tmdb_service.get_movie_recommendations(movie_id, page)

@router.get("/{movie_id}/similar")
async def get_similar_movies(
    movie_id: int,
    page: int = Query(1, ge=1, le=500, description="Page number")
):
    """Get movies similar to this one (by genre, keywords)"""
    return await tmdb_service.get_similar_movies(movie_id, page)