from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_user, get_verified_user
from app.models.user import User
from app.models.rating import Rating
from app.schemas.rating import RatingCreate, RatingUpdate, RatingResponse
from app.services.cache import cache_service
from pydantic import BaseModel

class PaginatedRatingsResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: List[RatingResponse]

router = APIRouter()

@router.get("", response_model=PaginatedRatingsResponse)
def get_ratings(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """Get user's ratings with pagination"""
    # Get total count
    total = db.query(Rating).filter(Rating.user_id == current_user.id).count()
    
    # Get paginated results
    ratings = db.query(Rating).filter(
        Rating.user_id == current_user.id
    ).order_by(Rating.rated_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": ratings
    }

@router.post("", response_model=RatingResponse, status_code=201)
def create_rating(
    data: RatingCreate,
    current_user: User = Depends(get_verified_user),
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
    
    cache_service.delete(f"user_genres:{current_user.id}:movie")
    cache_service.delete(f"user_genres:{current_user.id}:tv")
    
    return rating

@router.put("/{rating_id}", response_model=RatingResponse)
def update_rating(
    rating_id: str,
    data: RatingUpdate,
    current_user: User = Depends(get_verified_user),
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
    
    cache_service.delete(f"user_genres:{current_user.id}:movie")
    cache_service.delete(f"user_genres:{current_user.id}:tv")
    
    return rating

@router.delete("/{rating_id}")
def delete_rating(
    rating_id: str,
    current_user: User = Depends(get_verified_user),
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
    
    cache_service.delete(f"user_genres:{current_user.id}:movie")
    cache_service.delete(f"user_genres:{current_user.id}:tv")
    
    return {"message": "Rating deleted"}