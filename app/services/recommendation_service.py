from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from app.models.rating import Rating, RatingValue
from app.models.user import User
from app.services.tmdb import tmdb_service
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
        """
        # Get user's ratings
        ratings = db.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.media_type == "movie"
        ).all()
        
        rating_count = len(ratings)
        
        # NEW USER: No ratings or very few
        if rating_count < 5:
            return await tmdb_service.discover_movies(
                sort_by="popularity.desc",
                page=page,
                vote_count_min=vote_count_min,
                vote_average_min=vote_average_min
            )
        
        # Get rated movie IDs to exclude
        rated_movie_ids = {r.tmdb_id for r in ratings}
        
        # Analyze preferences
        favorite_genres = await self._get_favorite_genres(user_id, db, media_type="movie")
        
        # SOME RATINGS (5-19): Use top 2 genres
        if rating_count < 20:
            top_genres = favorite_genres[:2] if len(favorite_genres) >= 2 else favorite_genres
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
            genre_ids = ",".join(str(g) for g in top_genres)
            
            results = await tmdb_service.discover_movies(
                genre=genre_ids if genre_ids else None,
                sort_by="vote_average.desc",
                page=page,
                vote_count_min=vote_count_min,
                vote_average_min=7.0  # Higher threshold for experienced users
            )
        
        # Filter out already rated movies
        if "results" in results:
            results["results"] = [
                movie for movie in results["results"]
                if movie["id"] not in rated_movie_ids
            ]
        
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
        """
        ratings = db.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.media_type == "tv"
        ).all()
        
        rating_count = len(ratings)
        
        # NEW USER
        if rating_count < 5:
            return await tmdb_service.discover_tv(
                sort_by="popularity.desc",
                page=page,
                vote_count_min=vote_count_min,
                vote_average_min=vote_average_min
            )
        
        rated_tv_ids = {r.tmdb_id for r in ratings}
        favorite_genres = await self._get_favorite_genres(user_id, db, media_type="tv")
        
        # SOME RATINGS
        if rating_count < 20:
            top_genres = favorite_genres[:2] if len(favorite_genres) >= 2 else favorite_genres
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
            genre_ids = ",".join(str(g) for g in top_genres)
            
            results = await tmdb_service.discover_tv(
                genre=genre_ids if genre_ids else None,
                sort_by="vote_average.desc",
                page=page,
                vote_count_min=vote_count_min,
                vote_average_min=7.0
            )
        
        # Filter out already rated
        if "results" in results:
            results["results"] = [
                show for show in results["results"]
                if show["id"] not in rated_tv_ids
            ]
        
        return results
    
    async def _get_favorite_genres(
        self,
        user_id: str,
        db: Session,
        media_type: str
    ) -> List[int]:
        """
        Analyze user's ratings to find favorite genres
        Returns list of genre IDs sorted by preference
        """
        # Get user's "perfection" and "go_for_it" ratings
        high_ratings = db.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.media_type == media_type,
            Rating.rating.in_([RatingValue.perfection, RatingValue.go_for_it])
        ).all()
        
        if not high_ratings:
            return []
        
        # Collect all genres from highly rated content
        all_genres = []
        for rating in high_ratings:
            # Fetch movie/tv details to get genres
            if media_type == "movie":
                details = await tmdb_service.get_movie_details(rating.tmdb_id)
            else:
                details = await tmdb_service.get_tv_details(rating.tmdb_id)
            
            if "genres" in details:
                genre_ids = [g["id"] for g in details["genres"]]
                # Weight "perfection" higher than "go_for_it"
                weight = 2 if rating.rating == RatingValue.perfection else 1
                all_genres.extend(genre_ids * weight)
        
        # Count genre frequency
        genre_counts = Counter(all_genres)
        
        # Return top genres sorted by count
        return [genre_id for genre_id, count in genre_counts.most_common()]

recommendation_service = RecommendationService()