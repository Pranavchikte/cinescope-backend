from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base

class MediaType(str, enum.Enum):
    movie = "movie"
    tv = "tv"

class Watchlist(Base):
    __tablename__ = "watchlist"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tmdb_id = Column(Integer, nullable=False)
    media_type = Column(SQLEnum(MediaType), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    user = relationship("User", back_populates="watchlist")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'tmdb_id', 'media_type', name='unique_user_media'),
    )