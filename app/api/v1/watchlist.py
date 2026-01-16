from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_user, get_verified_user
from app.models.user import User
from app.models.watchlist import Watchlist
from app.schemas.watchlist import WatchlistCreate, WatchlsitResponse

router = APIRouter()

@router.get("", response_model=List[WatchlsitResponse])
def get_watchlist(
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    watchlist = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    return watchlist

@router.post("", response_model=WatchlsitResponse, status_code=201)
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
    return{"message": "Removed from watchlist"}