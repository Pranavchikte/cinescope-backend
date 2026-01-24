from fastapi import APIRouter, Query
from typing import Optional
from app.services.tmdb import tmdb_service

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

@router.get("/discover")
async def discover_movies(
    genre: Optional[str] = Query(None, description="Comma-separated genre IDs (e.g. '28,12')"),
    year: Optional[int] = Query(None, ge=1900, le=2030, description="Release year"),
    language: Optional[str] = Query(None, description="ISO 639-1 language code (e.g. 'en', 'hi')"),
    country: Optional[str] = Query(None, description="ISO 3166-1 country code (e.g. 'US', 'IN')"),
    sort_by: str = Query("popularity.desc", description="Sort by: popularity.desc, vote_average.desc, release_date.desc"),
    page: int = Query(1, ge=1, le=500, description="Page number")
):
    """
    Discover movies with filters
    Example: /movies/discover?genre=28,12&year=2023&language=hi&country=IN&sort_by=popularity.desc
    """
    return await tmdb_service.discover_movies(
        genre=genre,
        year=year,
        language=language,
        country=country,
        sort_by=sort_by,
        page=page
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