from pydantic import BaseModel
from datetime import datetime
import uuid
from app.models.watchlist import MediaType
from app.models.rating import RatingValue

class RatingCreate(BaseModel):
    tmdb_id: int
    media_type: MediaType
    rating: RatingValue

class RatingUpdate(BaseModel):
    rating: RatingValue

class RatingResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tmdb_id: int
    media_type: MediaType
    rating: RatingValue
    rated_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True