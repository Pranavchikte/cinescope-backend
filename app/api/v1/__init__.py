from fastapi import APIRouter
from app.api.v1 import auth, movies, tv, watchlist, ratings, creator_requests, creators, people, chat, vidsrc, watch_history

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(movies.router, prefix="/movies", tags=["movies"])
api_router.include_router(tv.router, prefix="/tv", tags=["tv"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(ratings.router, prefix="/ratings", tags=["ratings"])
api_router.include_router(creator_requests.router, prefix="/creator-requests", tags=["creator-requests"])
api_router.include_router(creators.router, prefix="/creators", tags=["creators"])
api_router.include_router(people.router, prefix="/people", tags=["people"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(vidsrc.router, prefix="/vidsrc", tags=["vidsrc"])
api_router.include_router(watch_history.router, prefix="/watch-history", tags=["watch-history"])
