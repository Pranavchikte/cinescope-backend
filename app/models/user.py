from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base
from app.models.base import TimeStampMixin
from app.models.watchlist import MediaType

class UserRole(str, enum.Enum):
    admin = "admin"
    creator = "creator"
    user = "user"

class User(Base, TimeStampMixin):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.user, nullable=False)
    is_public_profile = Column(Boolean, default=True, nullable=False)
    last_viewed_tmdb_id = Column(Integer, nullable=True)
    last_viewed_media_type = Column(SQLEnum(MediaType), nullable=True)
    last_viewed_at = Column(DateTime, nullable=True)
    preferred_movie_genres = Column(JSON, nullable=True)
    preferred_tv_genres = Column(JSON, nullable=True)
    preferred_languages = Column(JSON, nullable=True)
    taste_onboarded = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    creator_requests = relationship("CreatorRequest", foreign_keys="CreatorRequest.user_id", back_populates="user", cascade="all, delete-orphan")
