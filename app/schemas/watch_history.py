from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WatchHistoryCreate(BaseModel):
    movie_id: Optional[int] = None
    tv_show_id: Optional[int] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    progress: Optional[int] = None  # Minutes watched
    quality: Optional[str] = None  # "1080p", "720p", "480p", "Auto"
    
    class Config:
        from_attributes = True

class WatchHistoryResponse(BaseModel):
    id: str
    user_id: str
    movie_id: int
    tv_show_id: Optional[int]
    season_number: Optional[int]
    episode_number: Optional[int]
    progress: Optional[int]
    quality: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True
