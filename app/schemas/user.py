from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
import uuid
import re
from app.models.watchlist import MediaType

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """
        Password must contain:
        - At least 8 characters
        - At least 1 number
        - At least 1 special character (!@#$%^&*(),.?":{}|<>)
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>)')
        
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    is_email_verified: bool
    role: str
    is_public_profile: bool
    created_at: datetime
    last_viewed_tmdb_id: Optional[int] = None
    last_viewed_media_type: Optional[MediaType] = None
    last_viewed_at: Optional[datetime] = None
    preferred_movie_genres: Optional[List[int]] = None
    preferred_tv_genres: Optional[List[int]] = None
    preferred_languages: Optional[List[str]] = None
    taste_onboarded: bool
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    is_public_profile: Optional[bool] = None

class LastViewedUpdate(BaseModel):
    tmdb_id: int
    media_type: MediaType

class TasteProfileUpdate(BaseModel):
    preferred_movie_genres: Optional[List[int]] = None
    preferred_tv_genres: Optional[List[int]] = None
    preferred_languages: Optional[List[str]] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Same validation as UserCreate"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>)')
        
        return v

class MessageResponse(BaseModel):
    message: str

class CreatorResponse(BaseModel):
    id: uuid.UUID
    username: str
    is_public_profile: bool
    
    class Config:
        from_attributes = True
