import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.services.cache import cache_service

class TMDBService:
    def __init__(self):
        self.base_url = settings.TMDB_BASE_URL
        self.api_key = settings.TMDB_API_KEY
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None, cache_ttl: int = 3600) -> Dict[Any, Any]:
        cache_key = f"tmdb:{endpoint}:{str(params)}"
        
        cached_data = cache_service.get(cache_key)
        if cached_data:
            return cached_data
        
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            data = response.json()
        
        cache_service.set(cache_key, data, cache_ttl)
        return data
    
    async def get_trending_movies(self, time_window: str = "week") -> Dict[Any, Any]:
        return await self._make_request(f"/trending/movie/{time_window}", cache_ttl=3600)
    
    async def get_popular_movies(self) -> Dict[Any, Any]:
        return await self._make_request("/movie/popular", cache_ttl=3600)
    
    async def search_movies(self, query: str) -> Dict[Any, Any]:
        return await self._make_request("/search/movie", {"query": query}, cache_ttl=3600)
    
    async def get_movie_details(self, movie_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/movie/{movie_id}", cache_ttl=86400)
    
    async def get_movie_credits(self, movie_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/movie/{movie_id}/credits", cache_ttl=86400)
    
    async def get_movie_videos(self, movie_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/movie/{movie_id}/videos", cache_ttl=86400)
    
    async def get_trending_tv(self, time_window: str = "week") -> Dict[Any, Any]:
        return await self._make_request(f"/trending/tv/{time_window}", cache_ttl=3600)
    
    async def get_popular_tv(self) -> Dict[Any, Any]:
        return await self._make_request("/tv/popular", cache_ttl=3600)
    
    async def get_tv_details(self, tv_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/tv/{tv_id}", cache_ttl=86400)
    
    async def search_tv(self, query: str) -> Dict[Any, Any]:
        return await self._make_request("/search/tv", {"query": query}, cache_ttl=3600)
    
    async def get_tv_credits(self, tv_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/tv/{tv_id}/credits", cache_ttl=86400)
    
    async def get_tv_videos(self, tv_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/tv/{tv_id}/videos", cache_ttl=86400)

tmdb_service = TMDBService()