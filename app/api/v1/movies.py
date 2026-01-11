from fastapi import APIRouter, Query
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

@router.get("/{movie_id}")
async def get_movie_details(movie_id: int):
    return await tmdb_service.get_movie_details(movie_id)

@router.get("/{movie_id}/credits")
async def get_movie_credits(movie_id: int):
    return await tmdb_service.get_movie_credits(movie_id)

@router.get("/{movie_id}/videos")
async def get_movie_videos(movie_id: int):
    return await tmdb_service.get_movie_videos(movie_id)