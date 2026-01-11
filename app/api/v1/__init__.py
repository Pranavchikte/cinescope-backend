from fastapi import APIRouter
from app.api.v1 import auth, movies, tv, watchlist, ratings

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(movies.router, prefix="/movies", tags=["movies"])
api_router.include_router(tv.router, prefix="/tv", tags=["tv"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(ratings.router, prefix="/ratings", tags=["ratings"])