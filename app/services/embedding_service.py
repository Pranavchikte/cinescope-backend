import logging
import asyncio
from typing import List, Dict, Any
from app.services.tmdb import tmdb_service
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)


class EmbeddingService:
    
    async def index_popular_movies(self, num_pages: int = 50):
        """
        Fetch popular movies from TMDB and index them
        num_pages: Number of pages to fetch (50 pages = ~1000 movies)
        Sorted by popularity.desc (most popular first)
        Only includes movies with 2000+ votes (truly popular)
        """
        all_movies = []
        
        logger.info(f"Fetching {num_pages} pages of popular movies (2000+ votes)...")
        
        for page in range(1, num_pages + 1):
            data = await tmdb_service.discover_movies(
                sort_by="popularity.desc",
                page=page,
                vote_count_min=2000  # Increased from 500 - only blockbusters
            )
            
            # Delay to avoid TMDB rate limit (30 req/10sec)
            await asyncio.sleep(0.5)
            
            if "results" in data and data["results"]:
                movies = data["results"]
                
                # Format for vector store
                for movie in movies:
                    # Get genre names
                    genre_ids = movie.get("genre_ids", [])
                    genre_names = await self._get_genre_names(genre_ids)
                    
                    all_movies.append({
                        "id": movie["id"],
                        "title": movie.get("title", ""),
                        "overview": movie.get("overview", ""),
                        "genres": genre_names,
                        "poster_path": movie.get("poster_path", ""),
                        "vote_average": movie.get("vote_average", 0),
                        "release_date": movie.get("release_date", ""),
                        "media_type": "movie"  # ADD THIS LINE
                    })
                
                logger.info(f"Page {page}/{num_pages} - Fetched {len(movies)} movies")
            else:
                logger.warning(f"No results on page {page}")
                break
        
        # Add to vector store
        # Remove duplicates by ID
        if all_movies:
            # Deduplicate by keeping first occurrence of each ID
            seen_ids = set()
            unique_movies = []
            for movie in all_movies:
                if movie["id"] not in seen_ids:
                    seen_ids.add(movie["id"])
                    unique_movies.append(movie)
            
            vector_store.add_movies(unique_movies)
            logger.info(f"✅ Indexed {len(unique_movies)} unique movies (removed {len(all_movies) - len(unique_movies)} duplicates)")
        else:
            logger.error("No movies to index")
    
    async def _get_genre_names(self, genre_ids: List[int]) -> List[str]:
        """Convert genre IDs to names"""
        # Hardcoded genre mapping (faster than API call every time)
        genre_map = {
            28: "Action",
            12: "Adventure",
            16: "Animation",
            35: "Comedy",
            80: "Crime",
            99: "Documentary",
            18: "Drama",
            10751: "Family",
            14: "Fantasy",
            36: "History",
            27: "Horror",
            10402: "Music",
            9648: "Mystery",
            10749: "Romance",
            878: "Science Fiction",
            10770: "TV Movie",
            53: "Thriller",
            10752: "War",
            37: "Western"
        }
        
        return [genre_map.get(gid, "") for gid in genre_ids if gid in genre_map]
    
    async def index_popular_tv(self, num_pages: int = 50):
        """
        Fetch popular TV shows from TMDB and index them
        num_pages: Number of pages to fetch (50 pages = ~1000 TV shows)
        Sorted by popularity.desc (most popular first)
        Only includes shows with 2000+ votes (truly popular)
        """
        all_shows = []
        
        logger.info(f"Fetching {num_pages} pages of popular TV shows (2000+ votes)...")
        
        for page in range(1, num_pages + 1):
            data = await tmdb_service.discover_tv(
                sort_by="popularity.desc",
                page=page,
                vote_count_min=2000  # Increased from 500 - only blockbusters
            )
            
            # Delay to avoid TMDB rate limit (30 req/10sec)
            await asyncio.sleep(0.5)
            
            if "results" in data and data["results"]:
                shows = data["results"]
                
                # Format for vector store
                for show in shows:
                    # Get genre names
                    genre_ids = show.get("genre_ids", [])
                    genre_names = await self._get_genre_names(genre_ids)
                    
                    all_shows.append({
                        "id": show["id"],
                        "title": show.get("name", ""),  # TV uses 'name' not 'title'
                        "overview": show.get("overview", ""),
                        "genres": genre_names,
                        "poster_path": show.get("poster_path", ""),
                        "vote_average": show.get("vote_average", 0),
                        "release_date": show.get("first_air_date", ""),  # TV uses 'first_air_date'
                        "media_type": "tv"  # Add media type tag
                    })
                
                logger.info(f"Page {page}/{num_pages} - Fetched {len(shows)} TV shows")
            else:
                logger.warning(f"No results on page {page}")
                break
        
        # Add to vector store
        if all_shows:
            # Deduplicate by keeping first occurrence of each ID
            seen_ids = set()
            unique_shows = []
            for show in all_shows:
                if show["id"] not in seen_ids:
                    seen_ids.add(show["id"])
                    unique_shows.append(show)
            
            vector_store.add_movies(unique_shows)  # Same method works for TV
            logger.info(f"✅ Indexed {len(unique_shows)} unique TV shows (removed {len(all_shows) - len(unique_shows)} duplicates)")
        else:
            logger.error("No TV shows to index")


embedding_service = EmbeddingService()