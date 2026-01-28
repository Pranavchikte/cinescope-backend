from pydantic import BaseModel
from datetime import datetime
import uuid
from typing import Optional

class CreatorRequestCreate(BaseModel):
    message: Optional[str] = None

class CreatorRequestUpdate(BaseModel):
    status: str  # "approved" or "rejected"

class CreatorRequestResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    username: str = ""  # Will be populated from user relationship
    status: str
    message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True