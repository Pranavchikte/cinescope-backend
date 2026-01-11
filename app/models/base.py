from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class TimeStampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())