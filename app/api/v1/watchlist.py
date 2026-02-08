from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_user, get_verified_user
from app.models.user import User
from app.models.watchlist import Watchlist
from app.schemas.watchlist import WatchlistCreate, WatchlistResponse
from pydantic import BaseModel

class PaginatedWatchlistResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: List[WatchlistResponse]

router = APIRouter()

@router.get("", response_model=PaginatedWatchlistResponse)
def get_watchlist(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """Get user's watchlist with pagination"""
    # Get total count
    total = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).count()
    
    # Get paginated results
    watchlist = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id
    ).order_by(Watchlist.added_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": watchlist
    }

@router.post("", response_model=WatchlistResponse, status_code=201)
def add_to_watchlist(
    data: WatchlistCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.tmdb_id == data.tmdb_id,
        Watchlist.media_type == data.media_type
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")
    
    watchlist_item = Watchlist(
        user_id=current_user.id,
        tmdb_id=data.tmdb_id,
        media_type=data.media_type
    )
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)
    return watchlist_item

@router.delete("/{item_id}")
def remove_from_watchlist(
    item_id: str,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    item = db.query(Watchlist).filter(
        Watchlist.id == item_id,
        Watchlist.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Removed from watchlist"}