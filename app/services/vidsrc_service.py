import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings
from app.services.cache import cache_service

logger = logging.getLogger(__name__)


class VidsrcService:
    def __init__(self):
        # Multiple Vidsrc domains for fallback
        self.domains = [
            "vidsrc-embed.ru",
            "vidsrc-embed.su", 
            "vidsrcme.su",
            "vsrc.su"
        ]
        self.default_lang = "en"
        self.cache_ttl = 86400  # 24 hours
    
    async def _generate_embed_url(self, tmdb_id: int, media_type: str = "movie", 
                                 season: Optional[int] = None, episode: Optional[int] = None) -> Optional[str]:
        """
        Generate Vidsrc embed URL for movie or TV show
        """
        # Try each domain until one works
        for domain in self.domains:
            try:
                if media_type == "movie":
                    # Movie embed URL: https://vidsrc-embed.ru/embed/movie/{tmdb_id}?autoplay=1&ds_lang=en
                    embed_url = f"https://{domain}/embed/movie/{tmdb_id}?autoplay=1&ds_lang={self.default_lang}"
                elif media_type == "tv":
                    if season and episode:
                        # Episode embed URL: https://vidsrc-embed.ru/embed/tv/{tmdb_id}/{season}-{episode}?autoplay=1&ds_lang=en
                        embed_url = f"https://{domain}/embed/tv/{tmdb_id}/{season}-{episode}?autoplay=1&ds_lang={self.default_lang}&autonext=1"
                    else:
                        # TV show embed URL: https://vidsrc-embed.ru/embed/tv/{tmdb_id}?autoplay=1&ds_lang=en
                        embed_url = f"https://{domain}/embed/tv/{tmdb_id}?autoplay=1&ds_lang={self.default_lang}"
                else:
                    return None
                
                # Test if URL is accessible
                async with httpx.AsyncClient() as client:
                    response = await client.get(embed_url, timeout=5.0)
                    if response.status_code == 200:
                        return embed_url
                    else:
                        logger.warning(f"Domain {domain} returned status {response.status_code}")
                        continue
                
            except Exception as e:
                logger.warning(f"Domain {domain} failed: {str(e)}")
                continue
        
        return None
    
    async def get_movie_embed_url(self, tmdb_id: int) -> Optional[str]:
        """
        Get embed URL for a movie
        """
        cache_key = f"vidsrc:movie:{tmdb_id}"
        
        # Check cache first
        cached_url = cache_service.get(cache_key)
        if cached_url:
            return cached_url
        
        # Generate new embed URL
        embed_url = await self._generate_embed_url(tmdb_id, "movie")
        
        if embed_url:
            # Cache the result
            cache_service.set(cache_key, embed_url, self.cache_ttl)
        
        return embed_url
    
    async def get_tv_embed_url(self, tmdb_id: int, season: int, episode: int) -> Optional[str]:
        """
        Get embed URL for a TV episode
        """
        cache_key = f"vidsrc:tv:{tmdb_id}:{season}-{episode}"
        
        # Check cache first
        cached_url = cache_service.get(cache_key)
        if cached_url:
            return cached_url
        
        # Generate new embed URL
        embed_url = await self._generate_embed_url(tmdb_id, "tv", season, episode)
        
        if embed_url:
            # Cache the result
            cache_service.set(cache_key, embed_url, self.cache_ttl)
        
        return embed_url
    
    async def get_latest_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        """
        Get latest movies from Vidsrc (optional feature)
        """
        # This could be used for trending or new releases
        # For now, we'll return an empty list
        return []
    
    async def get_latest_tv_shows(self, page: int = 1) -> List[Dict[str, Any]]:
        """
        Get latest TV shows from Vidsrc (optional feature)
        """
        # This could be used for trending or new releases
        # For now, we'll return an empty list
        return []