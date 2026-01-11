from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base
from app.models.watchlist import MediaType

class RatingValue(str, enum.Enum):
    skip = "skip"
    timepass = "timepass"
    go_for_it = "go_for_it"
    perfection = "perfection"

class Rating(Base):
    __tablename__ = "ratings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tmdb_id = Column(Integer, nullable=False)
    media_type = Column(SQLEnum(MediaType), nullable=False)
    rating = Column(SQLEnum(RatingValue), nullable=False)
    rated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="ratings")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'tmdb_id', 'media_type', name='unique_user_rating'),
    )