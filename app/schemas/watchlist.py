from pydantic import BaseModel
from datetime import datetime
import uuid
from app.models.watchlist import MediaType

class WatchlistCreate(BaseModel):
    tmdb_id: int
    media_type: MediaType

class WatchlsitResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tmdb_id: int
    media_type: MediaType
    added_at: datetime
    
    class Config:
        from_attributes = True