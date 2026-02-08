import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.core.config import settings
from app.services.cache import cache_service

logger = logging.getLogger(__name__)


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
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                response.raise_for_status()
                data = response.json()
            
            cache_service.set(cache_key, data, cache_ttl)
            return data
        
        except httpx.TimeoutException:
            # If timeout, try to return cached data (even if expired)
            cached_data = cache_service.get(cache_key)
            if cached_data:
                return cached_data
            return {"error": "Request timeout", "results": []}
        
        except httpx.HTTPStatusError as e:
            # TMDB API error (rate limit, invalid key, etc.)
            logger.error(f"TMDB API error: {e.response.status_code} - {e.response.text}")
            return {"error": f"TMDB API error: {e.response.status_code}", "results": []}
        
        except Exception as e:
            # Any other error
            logger.error(f"TMDB request failed: {str(e)}")
            # Try to return cached data
            cached_data = cache_service.get(cache_key)
            if cached_data:
                return cached_data
            return {"error": "Service unavailable", "results": []}
    
    def _boost_indian_content(self, results: List[Dict], boost_factor: float = 5.0) -> List[Dict]:
        """
        Boost ranking of Indian language content in results
        boost_factor: multiplier for Indian content popularity score
        """
        if not results:
            return results
        
        for item in results:
            original_language = item.get("original_language", "")
            if original_language in settings.INDIAN_LANGUAGES:
                # Boost popularity score for Indian content
                if "popularity" in item:
                    item["popularity"] = item["popularity"] * boost_factor
                # Add flag for frontend
                item["is_indian_content"] = True
            else:
                item["is_indian_content"] = False
        
        # Re-sort by boosted popularity
        results.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        return results
    
    # Movies
    async def get_trending_movies(self, time_window: str = "week") -> Dict[Any, Any]:
        """Get trending movies with Indian content boosted"""
        data = await self._make_request(f"/trending/movie/{time_window}", {"region": settings.INDIAN_REGION}, cache_ttl=3600)
    
    # Boost Indian content in results
        if "results" in data:
            data["results"] = self._boost_indian_content(data["results"], boost_factor=5.0)
        return data
    
    async def get_indian_trending_movies(self) -> Dict[Any, Any]:
        """
        Get trending movies from multiple Indian languages
        Returns categorized results by language
        """
        results_by_language = {}
        
        # Fetch trending for each Indian language
        for lang in settings.INDIAN_LANGUAGES[:6]:  # Top 6 languages for performance
            lang_data = await self.discover_movies(
                language=lang,
                country=settings.INDIAN_REGION,
                sort_by="popularity.desc",
                page=1,
                vote_count_min=100
            )
            
            if "results" in lang_data and lang_data["results"]:
                results_by_language[lang] = lang_data["results"][:10]  # Top 10 per language
        
        return {
            "results_by_language": results_by_language,
            "languages": {
                "hi": "Hindi",
                "mr": "Marathi",
                "ta": "Tamil",
                "te": "Telugu",
                "pa": "Punjabi",
                "ml": "Malayalam"
            }
        }
    
    async def get_new_indian_releases_movies(self) -> Dict[Any, Any]:
        """Get recent Indian movie releases (last 30 days)"""
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        # Combine all Indian languages
        indian_langs = ",".join(settings.INDIAN_LANGUAGES)
        
        params = {
            "with_original_language": indian_langs,
            "region": settings.INDIAN_REGION,
            "primary_release_date.gte": thirty_days_ago.strftime("%Y-%m-%d"),
            "primary_release_date.lte": today.strftime("%Y-%m-%d"),
            "sort_by": "primary_release_date.desc",
            "vote_count.gte": 50,  # Lower threshold for new releases
            "page": 1
        }
        
        return await self._make_request("/discover/movie", params, cache_ttl=1800)  # 30min cache
    
    async def get_popular_movies(self) -> Dict[Any, Any]:
        """Get popular movies with Indian content boosted"""
        data = await self._make_request("/movie/popular", {"region": settings.INDIAN_REGION}, cache_ttl=3600)
    
        if "results" in data:
            data["results"] = self._boost_indian_content(data["results"], boost_factor=5.0)
    
        return data
    
    async def search_movies(self, query: str) -> Dict[Any, Any]:
    
        data = await self._make_request("/search/movie", {"query": query}, cache_ttl=1800)
        
        if "results" in data and data["results"]:
            # Sort by combined score: popularity * (1 + log(vote_count)) * (vote_average/10)
            # This ensures popular, well-rated movies with many votes rank highest
            for item in data["results"]:
                popularity = item.get("popularity", 0)
                vote_count = max(item.get("vote_count", 0), 1)  # Avoid log(0)
                vote_average = item.get("vote_average", 5.0)
                
                # Calculate combined score
                import math
                item["_search_score"] = popularity * (1 + math.log10(vote_count)) * (vote_average / 10)
            
            # Sort by score descending
            data["results"].sort(key=lambda x: x.get("_search_score", 0), reverse=True)
            
            # Remove internal score field before returning
            for item in data["results"]:
                item.pop("_search_score", None)
        
        return data
    
    async def get_movie_details(self, movie_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/movie/{movie_id}", cache_ttl=86400)
    
    async def get_movie_credits(self, movie_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/movie/{movie_id}/credits", cache_ttl=86400)
    
    async def get_movie_videos(self, movie_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/movie/{movie_id}/videos", cache_ttl=86400)
    
    async def get_movie_images(self, movie_id: int) -> Dict[Any, Any]:
        """Get movie images (backdrops and posters)"""
        return await self._make_request(f"/movie/{movie_id}/images", cache_ttl=86400)
    
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
        Discover movies with filters (defaults to Indian region)
        """
        params = {
            "sort_by": sort_by,
            "page": page,
            "region": country if country else settings.INDIAN_REGION,  # Default to India
        }
        
        if genre:
            params["with_genres"] = genre
        if year:
            params["primary_release_year"] = year
        if language:
            params["with_original_language"] = language
        if provider:
            params["with_watch_providers"] = provider
            params["watch_region"] = country if country else settings.INDIAN_REGION
        
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
        """Get trending TV shows with Indian content boosted"""
        data = await self._make_request(f"/trending/tv/{time_window}", {"region": settings.INDIAN_REGION}, cache_ttl=3600)
        
        if "results" in data:
            data["results"] = self._boost_indian_content(data["results"])
        
        return data
    
    async def get_indian_trending_tv(self) -> Dict[Any, Any]:
        """
        Get trending TV shows from multiple Indian languages
        Returns categorized results by language
        """
        results_by_language = {}
        
        for lang in settings.INDIAN_LANGUAGES[:6]:
            lang_data = await self.discover_tv(
                language=lang,
                country=settings.INDIAN_REGION,
                sort_by="popularity.desc",
                page=1,
                vote_count_min=100
            )
            
            if "results" in lang_data and lang_data["results"]:
                results_by_language[lang] = lang_data["results"][:10]
        
        return {
            "results_by_language": results_by_language,
            "languages": {
                "hi": "Hindi",
                "mr": "Marathi",
                "ta": "Tamil",
                "te": "Telugu",
                "pa": "Punjabi",
                "ml": "Malayalam"
            }
        }
    
    async def get_new_indian_releases_tv(self) -> Dict[Any, Any]:
        """Get recent Indian TV show releases (last 30 days)"""
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        indian_langs = ",".join(settings.INDIAN_LANGUAGES)
        
        params = {
            "with_original_language": indian_langs,
            "region": settings.INDIAN_REGION,
            "first_air_date.gte": thirty_days_ago.strftime("%Y-%m-%d"),
            "first_air_date.lte": today.strftime("%Y-%m-%d"),
            "sort_by": "first_air_date.desc",
            "vote_count.gte": 50,
            "page": 1
        }
        
        return await self._make_request("/discover/tv", params, cache_ttl=1800)
    
    async def get_popular_tv(self) -> Dict[Any, Any]:
        """Get popular TV shows with Indian content boosted"""
        data = await self._make_request("/tv/popular", {"region": settings.INDIAN_REGION}, cache_ttl=3600)
        
        if "results" in data:
            data["results"] = self._boost_indian_content(data["results"])
        
        return data
    
    async def get_tv_details(self, tv_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/tv/{tv_id}", cache_ttl=86400)
    
    async def search_tv(self, query: str) -> Dict[Any, Any]:
        """
        Search TV shows with popularity-based sorting
        Prioritizes: high popularity + high vote count + good ratings
        """
        data = await self._make_request("/search/tv", {"query": query}, cache_ttl=1800)
        
        if "results" in data and data["results"]:
            # Sort by combined score: popularity * (1 + log(vote_count)) * (vote_average/10)
            for item in data["results"]:
                popularity = item.get("popularity", 0)
                vote_count = max(item.get("vote_count", 0), 1)  # Avoid log(0)
                vote_average = item.get("vote_average", 5.0)
                
                # Calculate combined score
                import math
                item["_search_score"] = popularity * (1 + math.log10(vote_count)) * (vote_average / 10)
            
            # Sort by score descending
            data["results"].sort(key=lambda x: x.get("_search_score", 0), reverse=True)
            
            # Remove internal score field before returning
            for item in data["results"]:
                item.pop("_search_score", None)
        
        return data
    
    async def get_tv_credits(self, tv_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/tv/{tv_id}/credits", cache_ttl=86400)
    
    async def get_tv_videos(self, tv_id: int) -> Dict[Any, Any]:
        return await self._make_request(f"/tv/{tv_id}/videos", cache_ttl=86400)
    
    async def get_tv_images(self, tv_id: int) -> Dict[Any, Any]:
        """Get TV show images (backdrops and posters)"""
        return await self._make_request(f"/tv/{tv_id}/images", cache_ttl=86400)
    
    async def get_tv_watch_providers(self, tv_id: int) -> Dict[Any, Any]:
        """Get streaming providers for a TV show"""
        return await self._make_request(f"/tv/{tv_id}/watch/providers", cache_ttl=86400)
    
    async def get_tv_recommendations(self, tv_id: int, page: int = 1) -> Dict[Any, Any]:
        """Get TMDB's ML-based TV recommendations"""
        return await self._make_request(f"/tv/{tv_id}/recommendations", {"page": page}, cache_ttl=86400)
    
    async def get_similar_tv(self, tv_id: int, page: int = 1) -> Dict[Any, Any]:
        """Get TV shows similar to given show"""
        return await self._make_request(f"/tv/{tv_id}/similar", {"page": page}, cache_ttl=86400)
    
    async def get_tv_season(self, tv_id: int, season_number: int) -> Dict[Any, Any]:
        """Get season details with all episodes"""
        return await self._make_request(f"/tv/{tv_id}/season/{season_number}", cache_ttl=86400)
    
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
        Discover TV shows with filters (defaults to Indian region)
        """
        params = {
            "sort_by": sort_by,
            "page": page,
            "region": country if country else settings.INDIAN_REGION,
        }
        
        if genre:
            params["with_genres"] = genre
        if year:
            params["first_air_date_year"] = year
        if language:
            params["with_original_language"] = language
        if provider:
            params["with_watch_providers"] = provider
            params["watch_region"] = country if country else settings.INDIAN_REGION
        
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
    
    # People
    async def get_person_details(self, person_id: int) -> Dict[Any, Any]:
        """Get person details (bio, birthday, filmography overview)"""
        return await self._make_request(f"/person/{person_id}", cache_ttl=86400)
    
    async def get_person_movie_credits(self, person_id: int) -> Dict[Any, Any]:
        """Get all movies this person has worked on"""
        return await self._make_request(f"/person/{person_id}/movie_credits", cache_ttl=86400)
    
    async def get_person_tv_credits(self, person_id: int) -> Dict[Any, Any]:
        """Get all TV shows this person has worked on"""
        return await self._make_request(f"/person/{person_id}/tv_credits", cache_ttl=86400)
    
    # ADD THIS AT THE END OF TMDBService CLASS (line ~370)

    async def get_batch_movie_details(self, movie_ids: List[int]) -> List[Dict[Any, Any]]:
        """
        Fetch multiple movie details in parallel with caching
        Returns: List of movie detail objects
        """
        import asyncio
        
        async def fetch_movie(movie_id: int):
            try:
                return await self.get_movie_details(movie_id)
            except Exception as e:
                logger.warning(f"Failed to fetch movie {movie_id}: {e}")
                return None
        
        # Fetch all movies in parallel
        results = await asyncio.gather(*[fetch_movie(mid) for mid in movie_ids])
        
        # Filter out None (failed requests)
        return [r for r in results if r is not None]
    
    async def get_batch_tv_details(self, tv_ids: List[int]) -> List[Dict[Any, Any]]:
        """
        Fetch multiple TV show details in parallel with caching
        Returns: List of TV detail objects
        """
        import asyncio
        
        async def fetch_tv(tv_id: int):
            try:
                return await self.get_tv_details(tv_id)
            except Exception as e:
                logger.warning(f"Failed to fetch TV show {tv_id}: {e}")
                return None
        
        # Fetch all TV shows in parallel
        results = await asyncio.gather(*[fetch_tv(tid) for tid in tv_ids])
        
        # Filter out None (failed requests)
        return [r for r in results if r is not None]
    
    async def get_batch_mixed_details(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[Any, Any]]]:
        """
        Fetch mixed movie and TV details in one call
        Input: [{"tmdb_id": 123, "media_type": "movie"}, {"tmdb_id": 456, "media_type": "tv"}]
        Returns: {"movies": [...], "tv": [...]}
        """
        import asyncio
        
        movie_ids = [item["tmdb_id"] for item in items if item["media_type"] == "movie"]
        tv_ids = [item["tmdb_id"] for item in items if item["media_type"] == "tv"]
        
        movies, tv_shows = await asyncio.gather(
            self.get_batch_movie_details(movie_ids) if movie_ids else asyncio.sleep(0, result=[]),
            self.get_batch_tv_details(tv_ids) if tv_ids else asyncio.sleep(0, result=[])
        )
        
        return {
            "movies": movies,
            "tv": tv_shows
        }
    
    async def get_movie_full_details(self, movie_id: int) -> Dict[Any, Any]:
        """
        Fetch ALL movie details in one combined call (optimized with caching)
        Returns: {
            details: {...},
            credits: {...},
            videos: {...},
            images: {...},
            providers: {...},
            recommendations: {...},
            similar: {...}
        }
        """
        import asyncio
        
        # Fetch all data in parallel
        details, credits, videos, images, providers, recommendations, similar = await asyncio.gather(
            self.get_movie_details(movie_id),
            self.get_movie_credits(movie_id),
            self.get_movie_videos(movie_id),
            self.get_movie_images(movie_id),
            self.get_movie_watch_providers(movie_id),
            self.get_movie_recommendations(movie_id, page=1),
            self.get_similar_movies(movie_id, page=1),
        )
        
        return {
            "details": details,
            "credits": credits,
            "videos": videos,
            "images": images,
            "providers": providers,
            "recommendations": recommendations,
            "similar": similar
        }
    
    async def get_tv_full_details(self, tv_id: int) -> Dict[Any, Any]:
        """
        Fetch ALL TV show details in one combined call (optimized with caching)
        Returns: {
            details: {...},
            credits: {...},
            videos: {...},
            images: {...},
            providers: {...},
            recommendations: {...},
            similar: {...}
        }
        """
        import asyncio
        
        # Fetch all data in parallel
        details, credits, videos, images, providers, recommendations, similar = await asyncio.gather(
            self.get_tv_details(tv_id),
            self.get_tv_credits(tv_id),
            self.get_tv_videos(tv_id),
            self.get_tv_images(tv_id),
            self.get_tv_watch_providers(tv_id),
            self.get_tv_recommendations(tv_id, page=1),
            self.get_similar_tv(tv_id, page=1),
        )
        
        return {
            "details": details,
            "credits": credits,
            "videos": videos,
            "images": images,
            "providers": providers,
            "recommendations": recommendations,
            "similar": similar
        }

tmdb_service = TMDBService()