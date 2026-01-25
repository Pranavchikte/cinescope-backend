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
    
    # Movies
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
    
    async def get_movie_watch_providers(self, movie_id: int) -> Dict[Any, Any]:
        """Get streaming providers for a movie"""
        return await self._make_request(f"/movie/{movie_id}/watch/providers", cache_ttl=86400)
    
    async def get_movie_recommendations(self, movie_id: int, page: int = 1) -> Dict[Any, Any]:
        """Get TMDB's ML-based movie recommendations"""
        return await self._make_request(f"/movie/{movie_id}/recommendations", {"page": page}, cache_ttl=86400)
    
    async def get_similar_movies(self, movie_id: int, page: int = 1) -> Dict[Any, Any]:
        """Get movies similar to given movie (based on genres, keywords)"""
        return await self._make_request(f"/movie/{movie_id}/similar", {"page": page}, cache_ttl=86400)
    
    async def discover_movies(
        self,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        language: Optional[str] = None,
        country: Optional[str] = None,
        provider: Optional[str] = None,
        sort_by: str = "popularity.desc",
        page: int = 1,
        vote_count_min: int = 100,
        vote_average_min: Optional[float] = None,
        vote_average_max: Optional[float] = None,
        runtime_min: Optional[int] = None,
        runtime_max: Optional[int] = None,
    ) -> Dict[Any, Any]:
        """
        Discover movies with filters
        genre: comma-separated genre IDs (e.g. "28,12" for Action,Adventure)
        year: release year
        language: ISO 639-1 code (e.g. "en", "hi")
        country: ISO 3166-1 code (e.g. "US", "IN")
        provider: comma-separated provider IDs (e.g. "8,119" for Netflix,Prime Video)
        sort_by: popularity.desc, vote_average.desc, release_date.desc, etc.
        vote_count_min: minimum number of votes (filters low-quality content)
        vote_average_min/max: rating range filter
        runtime_min/max: movie duration in minutes
        """
        params = {
            "sort_by": sort_by,
            "page": page,
        }
        
        if genre:
            params["with_genres"] = genre
        if year:
            params["primary_release_year"] = year
        if language:
            params["with_original_language"] = language
        if country:
            params["region"] = country
        if provider:
            params["with_watch_providers"] = provider
            if not country:
                params["watch_region"] = "IN"
            else:
                params["watch_region"] = country
        
        # Quality filters
        if vote_count_min:
            params["vote_count.gte"] = vote_count_min
        if vote_average_min:
            params["vote_average.gte"] = vote_average_min
        if vote_average_max:
            params["vote_average.lte"] = vote_average_max
        if runtime_min:
            params["with_runtime.gte"] = runtime_min
        if runtime_max:
            params["with_runtime.lte"] = runtime_max
        
        return await self._make_request("/discover/movie", params, cache_ttl=3600)
    
    # TV Shows
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
    
    async def get_tv_watch_providers(self, tv_id: int) -> Dict[Any, Any]:
        """Get streaming providers for a TV show"""
        return await self._make_request(f"/tv/{tv_id}/watch/providers", cache_ttl=86400)
    
    async def get_tv_recommendations(self, tv_id: int, page: int = 1) -> Dict[Any, Any]:
        """Get TMDB's ML-based TV recommendations"""
        return await self._make_request(f"/tv/{tv_id}/recommendations", {"page": page}, cache_ttl=86400)
    
    async def get_similar_tv(self, tv_id: int, page: int = 1) -> Dict[Any, Any]:
        """Get TV shows similar to given show"""
        return await self._make_request(f"/tv/{tv_id}/similar", {"page": page}, cache_ttl=86400)
    
    async def discover_tv(
        self,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        language: Optional[str] = None,
        country: Optional[str] = None,
        provider: Optional[str] = None,
        sort_by: str = "popularity.desc",
        page: int = 1,
        vote_count_min: int = 100,
        vote_average_min: Optional[float] = None,
        vote_average_max: Optional[float] = None,
    ) -> Dict[Any, Any]:
        """
        Discover TV shows with filters
        genre: comma-separated genre IDs
        year: first air date year
        language: ISO 639-1 code
        country: ISO 3166-1 code
        provider: comma-separated provider IDs
        sort_by: popularity.desc, vote_average.desc, first_air_date.desc, etc.
        vote_count_min: minimum number of votes
        vote_average_min/max: rating range filter
        """
        params = {
            "sort_by": sort_by,
            "page": page,
        }
        
        if genre:
            params["with_genres"] = genre
        if year:
            params["first_air_date_year"] = year
        if language:
            params["with_original_language"] = language
        if country:
            params["region"] = country
        if provider:
            params["with_watch_providers"] = provider
            if not country:
                params["watch_region"] = "IN"
            else:
                params["watch_region"] = country
        
        # Quality filters
        if vote_count_min:
            params["vote_count.gte"] = vote_count_min
        if vote_average_min:
            params["vote_average.gte"] = vote_average_min
        if vote_average_max:
            params["vote_average.lte"] = vote_average_max
        
        return await self._make_request("/discover/tv", params, cache_ttl=3600)
    
    # Genre lists
    async def get_movie_genres(self) -> Dict[Any, Any]:
        return await self._make_request("/genre/movie/list", cache_ttl=86400)
    
    async def get_tv_genres(self) -> Dict[Any, Any]:
        return await self._make_request("/genre/tv/list", cache_ttl=86400)
    
    # Watch Providers
    async def get_watch_providers(self, region: str = "IN") -> Dict[Any, Any]:
        """
        Get list of available watch providers for a region
        region: ISO 3166-1 country code (default: IN for India)
        """
        return await self._make_request(f"/watch/providers/movie?watch_region={region}", cache_ttl=86400)

tmdb_service = TMDBService()