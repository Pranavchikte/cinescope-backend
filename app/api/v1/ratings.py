from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.rating import Rating
from app.schemas.rating import RatingCreate, RatingUpdate, RatingResponse

router = APIRouter()

@router.get("", response_model=List[RatingResponse])
def get_ratings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ratings = db.query(Rating).filter(Rating.user_id == current_user.id).all()
    return ratings

@router.post("", response_model=RatingResponse, status_code=201)
def create_rating(
    data: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if already rated
    existing = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.tmdb_id == data.tmdb_id,
        Rating.media_type == data.media_type
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already rated. Use PUT to update.")
    
    rating = Rating(
        user_id=current_user.id,
        tmdb_id=data.tmdb_id,
        media_type=data.media_type,
        rating=data.rating
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating

@router.put("/{rating_id}", response_model=RatingResponse)
def update_rating(
    rating_id: str,
    data: RatingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rating = db.query(Rating).filter(
        Rating.id == rating_id,
        Rating.user_id == current_user.id
    ).first()
    
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    rating.rating = data.rating
    db.commit()
    db.refresh(rating)
    return rating

@router.delete("/{rating_id}")
def delete_rating(
    rating_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rating = db.query(Rating).filter(
        Rating.id == rating_id,
        Rating.user_id == current_user.id
    ).first()
    
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    db.delete(rating)
    db.commit()
    return {"message": "Rating deleted"}