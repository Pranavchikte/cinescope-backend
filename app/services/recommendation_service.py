from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from app.models.rating import Rating, RatingValue
from app.models.user import User
from app.services.tmdb import tmdb_service
from app.services.cache import cache_service
from app.core.config import settings
from collections import Counter

class RecommendationService:
    
    async def get_personalized_movies(
        self,
        user_id: str,
        db: Session,
        page: int = 1,
        vote_count_min: int = 500,
        vote_average_min: float = 6.5
    ) -> Dict[Any, Any]:
        """
        Get personalized movie recommendations based on user's rating history
        ALWAYS boosts Indian content
        """
        # Get user's ratings
        ratings = db.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.media_type == "movie"
        ).all()
        
        rating_count = len(ratings)
        
        user = db.query(User).filter(User.id == user_id).first()
        pref_movie_genres = (user.preferred_movie_genres or []) if user else []
        pref_languages = (user.preferred_languages or []) if user else []

        # NEW USER: No ratings or very few
        if rating_count < 5:
            pref_genre_ids = ",".join(str(g) for g in pref_movie_genres) if pref_movie_genres else None
            pref_language = pref_languages[0] if pref_languages else None
            results = await tmdb_service.discover_movies(
                genre=pref_genre_ids,
                language=pref_language,
                sort_by="popularity.desc",
                page=page,
                vote_count_min=vote_count_min,
                vote_average_min=vote_average_min
            )
            return results
        
        # Get rated movie IDs to exclude
        rated_movie_ids = {r.tmdb_id for r in ratings}
        
        # Analyze preferences (NOW CACHED)
        favorite_genres = await self._get_favorite_genres(user_id, db, media_type="movie")
        
        # SOME RATINGS (5-19): Use top 2 genres
        if rating_count < 20:
            top_genres = favorite_genres[:2] if len(favorite_genres) >= 2 else favorite_genres
            for g in pref_movie_genres:
                if g not in top_genres:
                    top_genres.append(g)
            genre_ids = ",".join(str(g) for g in top_genres)
            
            results = await tmdb_service.discover_movies(
                genre=genre_ids if genre_ids else None,
                sort_by="vote_average.desc",
                page=page,
                vote_count_min=vote_count_min,
                vote_average_min=vote_average_min
            )
        # MANY RATINGS (20+): Full personalization
        else:
            top_genres = favorite_genres[:3] if len(favorite_genres) >= 3 else favorite_genres
            for g in pref_movie_genres:
                if g not in top_genres:
                    top_genres.append(g)
            genre_ids = ",".join(str(g) for g in top_genres)
            
            results = await tmdb_service.discover_movies(
                genre=genre_ids if genre_ids else None,
                sort_by="vote_average.desc",
                page=page,
                vote_count_min=vote_count_min,
                vote_average_min=7.0  # Higher threshold for experienced users
            )
        
        if "results" in results:
            # Filter out already rated movies
            results["results"] = [
                movie for movie in results["results"]
                if movie["id"] not in rated_movie_ids
            ]

        # Fallback: if too few results, relax filters
        if "results" in results and len(results["results"]) < 8:
            fallback = await tmdb_service.discover_movies(
                sort_by="popularity.desc",
                page=page,
                vote_count_min=50,
                vote_average_min=6.0
            )
            if "results" in fallback:
                combined = results["results"] + fallback["results"]
                seen = set()
                deduped = []
                for item in combined:
                    if item.get("id") in rated_movie_ids or item.get("id") in seen:
                        continue
                    seen.add(item.get("id"))
                    deduped.append(item)
                results["results"] = deduped
        
        return results
    
    async def get_personalized_tv(
        self,
        user_id: str,
        db: Session,
        page: int = 1,
        vote_count_min: int = 500,
        vote_average_min: float = 6.5
    ) -> Dict[Any, Any]:
        """
        Get personalized TV recommendations based on user's rating history
        ALWAYS boosts Indian content
        """
        ratings = db.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.media_type == "tv"
        ).all()
        
        rating_count = len(ratings)
        user = db.query(User).filter(User.id == user_id).first()
        pref_tv_genres = (user.preferred_tv_genres or []) if user else []
        pref_languages = (user.preferred_languages or []) if user else []
        
        # NEW USER
        if rating_count < 5:
            pref_genre_ids = ",".join(str(g) for g in pref_tv_genres) if pref_tv_genres else None
            pref_language = pref_languages[0] if pref_languages else None
            results = await tmdb_service.discover_tv(
                genre=pref_genre_ids,
                language=pref_language,
                sort_by="popularity.desc",
                page=page,
                vote_count_min=vote_count_min,
                vote_average_min=vote_average_min
            )
            return results
        
        rated_tv_ids = {r.tmdb_id for r in ratings}
        favorite_genres = await self._get_favorite_genres(user_id, db, media_type="tv")
        
        # SOME RATINGS
        if rating_count < 20:
            top_genres = favorite_genres[:2] if len(favorite_genres) >= 2 else favorite_genres
            for g in pref_tv_genres:
                if g not in top_genres:
                    top_genres.append(g)
            genre_ids = ",".join(str(g) for g in top_genres)
            
            results = await tmdb_service.discover_tv(
                genre=genre_ids if genre_ids else None,
                sort_by="vote_average.desc",
                page=page,
                vote_count_min=vote_count_min,
                vote_average_min=vote_average_min
            )
        # MANY RATINGS
        else:
            top_genres = favorite_genres[:3] if len(favorite_genres) >= 3 else favorite_genres
            for g in pref_tv_genres:
                if g not in top_genres:
                    top_genres.append(g)
            genre_ids = ",".join(str(g) for g in top_genres)
            
            results = await tmdb_service.discover_tv(
                genre=genre_ids if genre_ids else None,
                sort_by="vote_average.desc",
                page=page,
                vote_count_min=vote_count_min,
                vote_average_min=7.0
            )
        
        if "results" in results:
            # Filter out already rated
            results["results"] = [
                show for show in results["results"]
                if show["id"] not in rated_tv_ids
            ]

        # Fallback: if too few results, relax filters
        if "results" in results and len(results["results"]) < 8:
            fallback = await tmdb_service.discover_tv(
                sort_by="popularity.desc",
                page=page,
                vote_count_min=50,
                vote_average_min=6.0
            )
            if "results" in fallback:
                combined = results["results"] + fallback["results"]
                seen = set()
                deduped = []
                for item in combined:
                    if item.get("id") in rated_tv_ids or item.get("id") in seen:
                        continue
                    seen.add(item.get("id"))
                    deduped.append(item)
                results["results"] = deduped
        
        return results
    
    async def _get_favorite_genres(
        self,
        user_id: str,
        db: Session,
        media_type: str
    ) -> List[int]:
        """
        Analyze user's ratings to find favorite genres
        NOW WITH CACHING (1 hour TTL)
        Returns list of genre IDs sorted by preference
        """
        # Check cache first
        cache_key = f"user_genres:{user_id}:{media_type}"
        cached_genres = cache_service.get(cache_key)
        if cached_genres:
            return cached_genres
        
        # Get user's "perfection" and "go_for_it" ratings
        high_ratings = db.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.media_type == media_type,
            Rating.rating.in_([RatingValue.perfection, RatingValue.go_for_it])
        ).all()
        
        if not high_ratings:
            return []
        
        # Collect TMDB IDs for batch fetch
        tmdb_ids = [rating.tmdb_id for rating in high_ratings]
        
        # OPTIMIZED: Batch fetch instead of N individual calls
        if media_type == "movie":
            details_list = await tmdb_service.get_batch_movie_details(tmdb_ids)
        else:
            details_list = await tmdb_service.get_batch_tv_details(tmdb_ids)
        
        # Create mapping of tmdb_id -> details for fast lookup
        details_map = {details["id"]: details for details in details_list if "id" in details}
        
        # Collect all genres from highly rated content
        all_genres = []
        for rating in high_ratings:
            details = details_map.get(rating.tmdb_id)
            if details and "genres" in details:
                genre_ids = [g["id"] for g in details["genres"]]
                # Weight "perfection" higher than "go_for_it"
                weight = 2 if rating.rating == RatingValue.perfection else 1
                all_genres.extend(genre_ids * weight)
        
        # Count genre frequency
        genre_counts = Counter(all_genres)
        
        # Get top genres sorted by count
        favorite_genres = [genre_id for genre_id, count in genre_counts.most_common()]
        
        # Cache for 1 hour
        cache_service.set(cache_key, favorite_genres, ttl=3600)
        
        return favorite_genres

recommendation_service = RecommendationService()
