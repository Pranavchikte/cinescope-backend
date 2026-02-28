from sqlalchemy import Column, UUID, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as UUIDType
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base

class WatchHistory(Base):
    __tablename__ = "watch_history"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, nullable=True)
    tv_show_id = Column(Integer, nullable=True)  # For future TV show support
    season_number = Column(Integer, nullable=True)
    episode_number = Column(Integer, nullable=True)
    progress = Column(Integer, nullable=True)  # Minutes watched
    quality = Column(String, nullable=True)  # "1080p", "720p", "480p", "Auto"
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="watch_history")
