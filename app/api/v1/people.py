from fastapi import APIRouter
from app.services.tmdb import tmdb_service

router = APIRouter()

@router.get("/{person_id}")
async def get_person_details(person_id: int):
    """Get person details including bio, birthday, place of birth, known for"""
    return await tmdb_service.get_person_details(person_id)

@router.get("/{person_id}/movie-credits")
async def get_person_movie_credits(person_id: int):
    """Get all movies this person has worked on (cast and crew)"""
    return await tmdb_service.get_person_movie_credits(person_id)

@router.get("/{person_id}/tv-credits")
async def get_person_tv_credits(person_id: int):
    """Get all TV shows this person has worked on (cast and crew)"""
    return await tmdb_service.get_person_tv_credits(person_id)