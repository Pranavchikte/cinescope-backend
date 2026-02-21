import google.generativeai as genai
import logging
import re
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.vector_store import vector_store
from app.services.tmdb import tmdb_service
from app.models.rating import Rating, RatingValue
from app.services.cache import cache_service
import hashlib

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')


class ChatService:
    
    async def ask(self, query: str, user_id: str, db: Session) -> Dict[str, Any]:
        """
        Main RAG pipeline
        Returns: {"response": "text...", "movies": [...]}
        """
        query_clean = query.strip()
        cache_key = f"chat:{user_id}:{hashlib.sha256(query_clean.lower().encode()).hexdigest()}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached
        
        # Determine if user is asking about TV shows or movies
        query_lower = query_clean.lower()
        prefer_tv = any(word in query_lower for word in ['tv show', 'tv series', 'series', 'watching', 'tv', 'netflix series', 'amazon series', 'show like'])
        prefer_movie = any(word in query_lower for word in ['movie', 'film', 'watch', 'cinema', 'movie like', 'film like'])
        
        # Determine preferred media type
        if prefer_tv and not prefer_movie:
            preferred_type = 'tv'
        elif prefer_movie and not prefer_tv:
            preferred_type = 'movie'
        else:
            preferred_type = None  # Mixed or unclear - return both
        
        # Step 1: Search vector store with more results to filter
        search_results = vector_store.search(query_clean, n_results=12)
        
        # Step 2: Filter by preferred media type if applicable
        if preferred_type:
            similar_movies = [m for m in search_results if m.get('media_type') == preferred_type]
            # If no results of preferred type, fall back to all results
            if not similar_movies:
                similar_movies = search_results
        else:
            similar_movies = search_results
        
        # Step 2.5: Re-rank by popularity (rating) - most popular first
        # This ensures that even if ChromaDB returns semantically similar movies,
        # the most popular ones appear first
        similar_movies = sorted(similar_movies, key=lambda x: x.get('rating', 0), reverse=True)
        
        # Step 2.6: Check if we need TMDB fallback for general queries
        # For queries like "best action movies", "popular horror films", etc.
        # TMDB is more reliable than ChromaDB for pure popularity
        general_query, genre_id = self._is_general_popularity_query(query_lower)
        
        if general_query and len(similar_movies) < 3:
            # ChromaDB didn't return enough good results, fallback to TMDB
            tmdb_results = await self._get_tmdb_popular(genre_id, preferred_type)
            if tmdb_results:
                similar_movies = tmdb_results
                # Update preferred_type based on TMDB results
                if tmdb_results and tmdb_results[0].get('media_type') == 'tv':
                    preferred_type = 'tv'
                elif tmdb_results and tmdb_results[0].get('media_type') == 'movie':
                    preferred_type = 'movie'
        
        # Step 3: Check if movie-related
        if not self._is_movie_question(query) and not similar_movies:
            return {
                "response": "I can only help with movies and TV shows. Please ask me about recommendations, ratings, or movie information.",
                "movies": []
            }
        
        # Step 4: Get user's rating history
        user_context = self._get_user_context(user_id, db)
        
        # Step 5: Build prompt with media type context
        prompt = self._build_prompt(query_clean, user_context, similar_movies[:8], preferred_type)
        
        # Step 6: Get response from Gemini
        try:
            response = model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            answer = "Sorry, I couldn't process your request. Please try again."
        
        result = {
            "response": answer,
            "movies": similar_movies[:8]  # Return top 8
        }
        cache_service.set(cache_key, result, ttl=600)
        return result
    
    def _is_abbreviation_match(self, query: str, title: str) -> bool:
        """Check if query is an abbreviation of title (e.g., 'got' = 'game of thrones')"""
        abbreviations = {
            'got': 'game of thrones',
            'gotg': 'guardians of the galaxy',
            'gOT': 'game of thrones',
            'twd': 'the walking dead',
            'bb': 'breaking bad',
            'bcs': 'better call saul',
            'tpot': 'the punisher',
            'loki': 'loki',
            'she-hulk': 'she-hulk',
            'ds': 'doctor strange',
            'sm': 'spider-man',
            'avengers': 'avengers',
            'hotd': 'house of the dragon',
            'robb': 'ring of power',
        }
        
        query_clean = query.lower().strip()
        return abbreviations.get(query_clean, '') in title.lower()
    
    def _fuzzy_match(self, query: str, title: str) -> bool:
        """Check if query loosely matches title (for typos/partial matches)"""
        # Handle common abbreviations first
        abbrev_map = {
            'got': ['game', 'thrones'],
            'twd': ['walking', 'dead'],
            'bb': ['breaking', 'bad'],
        }
        
        if query in abbrev_map:
            return any(word in title for word in abbrev_map[query])
        
        # Simple fuzzy: query is at least 3 chars and appears in title
        if len(query) >= 3:
            return query in title
        
        return False
    
    def _is_movie_question(self, query: str) -> bool:
        """Check if question is movie-related"""
        # Expanded keywords including common queries
        movie_keywords = [
            "movie", "film", "watch", "recommend", "recommendation", "suggest", 
            "suggestion", "tv", "show", "series", "episode", "season",
            "actor", "actress", "cast", "director", "producer",
            "genre", "thriller", "comedy", "drama", "action", "horror", 
            "romance", "romantic", "sci-fi", "science fiction", "fantasy",
            "documentary", "animation", "animated", "anime",
            "netflix", "amazon", "prime", "hulu", "disney", "hotstar",
            "streaming", "watch", "watching", "view", "viewing",
            "latest", "new", "recent", "popular", "trending", "top",
            "best", "top rated", "highest", "rating", "score",
            "similar", "like", "same", "other", "more",
            "trailer", "preview", "clips",
            "plot", "story", "summary", "synopsis", "about",
            "sequel", "prequel", "spin-off", "spin off", "remake",
            "release", "date", "year", "2020", "2021", "2022", "2023", "2024", "2025",
            "hindi", "tamil", "telugu", "malayalam", "korean", "bollywood", "hollywood",
        ]
        
        # Also check for TMDB ID patterns (numbers at end of URL or standalone)
        if re.search(r'^\d+$', query.strip()):
            return True
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in movie_keywords)
    
    def _get_user_context(self, user_id: str, db: Session) -> str:
        """Get user's recent ratings"""
        ratings = db.query(Rating).filter(
            Rating.user_id == user_id
        ).order_by(Rating.rated_at.desc()).limit(10).all()
        
        if not ratings:
            return "User is new, no ratings yet."
        
        # Format ratings
        context = "User's recent ratings:\n"
        for rating in ratings:
            context += f"- Rated '{rating.rating.value}' (ID: {rating.tmdb_id})\n"
        
        return context
    
    def _build_prompt(self, query: str, user_context: str, similar_movies: List[Dict], preferred_type: str = None) -> str:
        """Build prompt for Gemini"""
        
        # Format similar movies
        movies_text = ""
        for i, movie in enumerate(similar_movies, 1):
            media_type = "TV Show" if movie.get('media_type') == 'tv' else "Movie"
            movies_text += f"{i}. {movie['title']} ({movie['year']}) - Rating: {movie['rating']}/10 - {media_type}\n"
        
        # Add context about preferred type
        type_context = ""
        if preferred_type == 'tv':
            type_context = "The user is specifically looking for TV shows/series. Prioritize TV shows in your recommendations."
        elif preferred_type == 'movie':
            type_context = "The user is specifically looking for movies. Prioritize movies in your recommendations."
        
        prompt = f"""You are a helpful movie and TV show recommendation assistant. 
The user is asking about: "{query}"

{type_context}

{user_context}

RECOMMENDED MOVIES/TV SHOWS FROM DATABASE:
{movies_text if movies_text else "No similar content found in database."}

TASK:
- If the user is asking about a specific movie/show (e.g., "what about Game of Thrones"), recommend similar content from the list above
- If the user wants recommendations, pick the best matches from the list
- If the user asks about availability or where to watch, say you don't have that info but can recommend similar titles
- Be conversational and friendly, max 2-3 sentences

IMPORTANT:
- Use PLAIN TEXT ONLY - no markdown, no asterisks, no special formatting
- If no good matches found, say "I couldn't find exact matches but here are some popular titles you might like" and list a few from the database
- Never say "I don't have information" - always provide value from the recommendations
- Include the media type (Movie or TV Show) in your response

YOUR RESPONSE:"""

        return prompt
    
    def _is_general_popularity_query(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Check if query is a general popularity query (not specific title search)
        Returns: (is_general, genre_id)
        """
        # Genre keyword mappings
        genre_keywords = {
            'action': '28',
            'adventure': '12',
            'animation': '16',
            'comedy': '35',
            'crime': '80',
            'documentary': '99',
            'drama': '18',
            'family': '10751',
            'fantasy': '14',
            'history': '36',
            'horror': '27',
            'music': '10402',
            'mystery': '9648',
            'romance': '10749',
            'sci-fi': '878',
            'science fiction': '878',
            'thriller': '53',
            'war': '10752',
            'western': '37',
        }
        
        # TV genre keywords
        tv_genre_keywords = {
            'action': '10759',
            'animation': '16',
            'comedy': '35',
            'crime': '80',
            'documentary': '99',
            'drama': '18',
            'family': '10751',
            'kids': '10762',
            'mystery': '9648',
            'news': '10763',
            'reality': '10764',
            'sci-fi': '10765',
            'fantasy': '10765',
            'soap': '10766',
            'talk': '10767',
            'war': '10768',
            'western': '37',
        }
        
        # General popularity keywords (not specific title)
        general_keywords = [
            'best', 'top', 'popular', 'trending', 'latest', 'new',
            'recommend', 'suggestion', 'must watch', 'greatest'
        ]
        
        # Check if query contains genre + general keywords
        query_lower = query.lower()
        
        # Check for genre
        genre_id = None
        for genre, gid in {**genre_keywords, **tv_genre_keywords}.items():
            if genre in query_lower:
                genre_id = gid
                break
        
        # If query has general keywords and/or genre, it's a general query
        is_general = any(keyword in query_lower for keyword in general_keywords) or genre_id is not None
        
        return is_general, genre_id
    
    async def _get_tmdb_popular(self, genre_id: Optional[str], preferred_type: Optional[str]) -> List[Dict]:
        """
        Get popular movies/shows from TMDB directly (bypasses ChromaDB for general queries)
        """
        try:
            results = []
            
            # Determine media type
            is_tv = preferred_type == 'tv' or (preferred_type is None and 'tv' in str(genre_id))
            
            if is_tv:
                # Get popular TV shows
                data = await tmdb_service.discover_tv(
                    genre=genre_id,
                    sort_by="popularity.desc",
                    page=1,
                    vote_count_min=1000
                )
                if "results" in data:
                    for show in data["results"][:10]:
                        results.append({
                            "id": show["id"],
                            "title": show.get("name", ""),
                            "poster": f"https://image.tmdb.org/t/p/w500{show.get('poster_path', '')}" if show.get('poster_path') else "",
                            "rating": show.get("vote_average", 0),
                            "year": int(show.get("first_air_date", "0")[:4]) if show.get("first_air_date") else 0,
                            "media_type": "tv"
                        })
            else:
                # Get popular movies
                data = await tmdb_service.discover_movies(
                    genre=genre_id,
                    sort_by="popularity.desc",
                    page=1,
                    vote_count_min=1000
                )
                if "results" in data:
                    for movie in data["results"][:10]:
                        results.append({
                            "id": movie["id"],
                            "title": movie.get("title", ""),
                            "poster": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path', '')}" if movie.get('poster_path') else "",
                            "rating": movie.get("vote_average", 0),
                            "year": int(movie.get("release_date", "0")[:4]) if movie.get("release_date") else 0,
                            "media_type": "movie"
                        })
            
            return results
        except Exception as e:
            logger.error(f"TMDB fallback error: {e}")
            return []


chat_service = ChatService()
