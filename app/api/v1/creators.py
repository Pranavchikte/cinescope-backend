from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.rating import Rating
from app.schemas.user import CreatorResponse
from app.schemas.rating import RatingResponse

router = APIRouter()

@router.get("", response_model=List[CreatorResponse])
def get_all_creators(db: Session = Depends(get_db)):
    """Get list of all creators with public profiles"""
    creators = db.query(User).filter(
        User.role.in_([UserRole.creator, UserRole.admin]),
        User.is_public_profile == True
    ).all()
    
    return creators

@router.get("/{username}/ratings", response_model=List[RatingResponse])
def get_creator_ratings(
    username: str,
    rating_filter: str = None,
    media_type: str = None,
    db: Session = Depends(get_db)
):
    """Get a creator's public ratings"""
    # Find creator
    creator = db.query(User).filter(User.username == username).first()
    
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    
    if creator.role not in [UserRole.creator, UserRole.admin]:
        raise HTTPException(status_code=403, detail="User is not a creator")
    
    if not creator.is_public_profile:
        raise HTTPException(status_code=403, detail="Creator's profile is private")
    
    # Get ratings
    query = db.query(Rating).filter(Rating.user_id == creator.id)
    
    if rating_filter:
        query = query.filter(Rating.rating == rating_filter)
    
    if media_type:
        query = query.filter(Rating.media_type == media_type)
    
    ratings = query.order_by(Rating.rated_at.desc()).all()
    
    return ratings