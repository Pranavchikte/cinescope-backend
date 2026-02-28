from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.watch_history import WatchHistory
from app.schemas.watch_history import WatchHistoryCreate, WatchHistoryResponse
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/")
async def create_watch_history(watch_data: WatchHistoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Create or update watch history entry
    
    This endpoint tracks user's watch progress for movies/TV shows.
    """
    try:
        if not watch_data.movie_id and not watch_data.tv_show_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="movie_id or tv_show_id is required"
            )

        # Check if existing entry exists
        if watch_data.movie_id:
            existing_entry = db.query(WatchHistory).filter(
                WatchHistory.user_id == current_user.id,
                WatchHistory.movie_id == watch_data.movie_id
            ).first()
        else:
            existing_entry = db.query(WatchHistory).filter(
                WatchHistory.user_id == current_user.id,
                WatchHistory.tv_show_id == watch_data.tv_show_id,
                WatchHistory.season_number == watch_data.season_number,
                WatchHistory.episode_number == watch_data.episode_number
            ).first()
        
        if existing_entry:
            # Update existing entry
            existing_entry.progress = watch_data.progress
            existing_entry.quality = watch_data.quality
            existing_entry.timestamp = datetime.utcnow()
            db.commit()
            return {"message": "Watch history updated", "id": str(existing_entry.id)}
        else:
            # Create new entry
            new_entry = WatchHistory(
                user_id=current_user.id,
                movie_id=watch_data.movie_id,
                tv_show_id=watch_data.tv_show_id,
                season_number=watch_data.season_number,
                episode_number=watch_data.episode_number,
                progress=watch_data.progress,
                quality=watch_data.quality
            )
            db.add(new_entry)
            db.commit()
            db.refresh(new_entry)
            return {"message": "Watch history created", "id": str(new_entry.id)}
            
    except Exception as e:
        logger.error(f"Error creating watch history: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500,
            detail="Internal server error"
        )

@router.get("/")
async def get_watch_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get all watch history for the current user
    """
    try:
        history = db.query(WatchHistory).filter(
            WatchHistory.user_id == current_user.id
        ).order_by(WatchHistory.timestamp.desc()).all()
        
        return [
            {
                "id": str(h.id),
                "movie_id": h.movie_id,
                "tv_show_id": h.tv_show_id,
                "season_number": h.season_number,
                "episode_number": h.episode_number,
                "progress": h.progress,
                "quality": h.quality,
                "timestamp": h.timestamp.isoformat() if h.timestamp else None
            }
            for h in history
        ]
    except Exception as e:
        logger.error(f"Error getting watch history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500,
            detail="Internal server error"
        )

@router.get("/movie/{movie_id}")
async def get_movie_watch_history(movie_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get watch history for a specific movie
    """
    try:
        history = db.query(WatchHistory).filter(
            WatchHistory.user_id == current_user.id,
            WatchHistory.movie_id == movie_id
        ).first()
        
        if not history:
            return None
            
        return {
            "id": str(history.id),
            "movie_id": history.movie_id,
            "progress": history.progress,
            "quality": history.quality,
            "timestamp": history.timestamp.isoformat() if history.timestamp else None
        }
    except Exception as e:
        logger.error(f"Error getting movie watch history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500,
            detail="Internal server error"
        )

@router.get("/tv/{tv_id}")
async def get_tv_watch_history(
    tv_id: int, 
    season: Optional[int] = None, 
    episode: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Get watch history for a specific TV show
    """
    try:
        query = db.query(WatchHistory).filter(
            WatchHistory.user_id == current_user.id,
            WatchHistory.tv_show_id == tv_id
        )
        
        if season:
            query = query.filter(WatchHistory.season_number == season)
        if episode:
            query = query.filter(WatchHistory.episode_number == episode)
            
        history = query.order_by(WatchHistory.timestamp.desc()).all()
        
        return [
            {
                "id": str(h.id),
                "tv_show_id": h.tv_show_id,
                "season_number": h.season_number,
                "episode_number": h.episode_number,
                "progress": h.progress,
                "quality": h.quality,
                "timestamp": h.timestamp.isoformat() if h.timestamp else None
            }
            for h in history
        ]
    except Exception as e:
        logger.error(f"Error getting TV watch history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500,
            detail="Internal server error"
        )
