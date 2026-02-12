from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.api.deps import get_verified_user
from app.models.user import User
from app.services.chat_service import chat_service

router = APIRouter()


class ChatRequest(BaseModel):
    query: str


class MovieCard(BaseModel):
    id: int
    title: str
    poster: str
    rating: float
    year: int


class ChatResponse(BaseModel):
    response: str
    movies: list[MovieCard]


@router.post("/ask", response_model=ChatResponse)
def ask_chatbot(
    data: ChatRequest,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """
    Ask the movie chatbot a question
    
    Example request:
    {
        "query": "Recommend a thriller like Gone Girl"
    }
    
    Example response:
    {
        "response": "Based on your ratings, try Sharp Objects...",
        "movies": [
            {
                "id": 12345,
                "title": "Sharp Objects",
                "poster": "https://...",
                "rating": 8.1,
                "year": 2018
            }
        ]
    }
    """
    if not data.query or len(data.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query too short")
    
    result = chat_service.ask(
        query=data.query,
        user_id=str(current_user.id),
        db=db
    )
    
    return result