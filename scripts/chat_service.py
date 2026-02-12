import google.generativeai as genai
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.vector_store import vector_store
from app.models.rating import Rating, RatingValue

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


class ChatService:
    
    def ask(self, query: str, user_id: str, db: Session) -> Dict[str, Any]:
        """
        Main RAG pipeline
        Returns: {"response": "text...", "movies": [...]}
        """
        
        # Step 1: Check if movie-related
        if not self._is_movie_question(query):
            return {
                "response": "I can only help with movies and TV shows. Please ask me about recommendations, ratings, or movie information.",
                "movies": []
            }
        
        # Step 2: Get user's rating history
        user_context = self._get_user_context(user_id, db)
        
        # Step 3: Search similar movies from vector store
        similar_movies = vector_store.search(query, n_results=5)
        
        # Step 4: Build prompt
        prompt = self._build_prompt(query, user_context, similar_movies)
        
        # Step 5: Get response from Gemini
        try:
            response = model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            answer = "Sorry, I couldn't process your request. Please try again."
        
        return {
            "response": answer,
            "movies": similar_movies[:3]  # Return top 3 movies
        }
    
    def _is_movie_question(self, query: str) -> bool:
        """Check if question is movie-related"""
        movie_keywords = [
            "movie", "film", "watch", "recommend", "suggestion", "tv", "show", 
            "series", "actor", "director", "genre", "thriller", "comedy", "drama",
            "action", "horror", "romance", "sci-fi", "documentary"
        ]
        
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
    
    def _build_prompt(self, query: str, user_context: str, similar_movies: List[Dict]) -> str:
        """Build prompt for Gemini"""
        
        # Format similar movies
        movies_text = ""
        for i, movie in enumerate(similar_movies, 1):
            movies_text += f"{i}. {movie['title']} ({movie['year']}) - Rating: {movie['rating']}/10\n"
        
        prompt = f"""You are a movie expert assistant. Answer the user's question using the context below.

{user_context}

SIMILAR MOVIES FROM DATABASE:
{movies_text if movies_text else "No similar movies found."}

USER QUESTION: {query}

INSTRUCTIONS:
- Be conversational and friendly
- Reference the user's ratings if available
- Recommend movies from the similar movies list
- Keep response under 100 words
- Don't mention TMDB IDs

YOUR RESPONSE:"""
        
        return prompt


chat_service = ChatService()