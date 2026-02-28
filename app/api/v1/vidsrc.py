from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.watch_history import WatchHistory
from app.schemas.watch_history import WatchHistoryCreate
from app.services.vidsrc_service import VidsrcService
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
vidsrc_service = VidsrcService()

@router.get("/movie/{movie_id}")
async def get_vidsrc_movie_embed(movie_id: int, current_user: User = Depends(get_current_user)):
    """
    Get Vidsrc embed URL for a movie
    
    This endpoint returns the embed URL for watching a movie through Vidsrc.
    Authentication is required.
    """
    try:
        # Get embed URL from Vidsrc service
        embed_url = await vidsrc_service.get_movie_embed_url(movie_id)
        
        if not embed_url:
            logger.error(f"Failed to get embed URL for movie {movie_id}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vidsrc service unavailable for movies"
            )
        
        return {
            "embed_url": embed_url,
            "quality_options": ["Auto (1080p+)"],
            "default_quality": "Auto",
            "media_type": "movie",
            "tmdb_id": movie_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Vidsrc embed for movie {movie_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500,
            detail="Internal server error"
        )

@router.get("/tv/{tv_id}")
async def get_vidsrc_tv_embed(
    tv_id: int,
    season: Optional[int] = Query(None, description="Season number"),
    episode: Optional[int] = Query(None, description="Episode number"),
    current_user: User = Depends(get_current_user)
):
    """
    Get Vidsrc embed URL for a TV show or episode
    
    This endpoint returns the embed URL for watching a TV show through Vidsrc.
    Authentication is required.
    
    If season and episode are provided, returns the specific episode.
    Otherwise, returns the TV show page (for browsing episodes).
    """
    try:
        if season and episode:
            # Get specific episode embed URL
            embed_url = await vidsrc_service.get_tv_embed_url(tv_id, season, episode)
            
            if not embed_url:
                logger.error(f"Failed to get embed URL for TV {tv_id} S{season}E{episode}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Vidsrc service unavailable for this episode"
                )
            
            return {
                "embed_url": embed_url,
                "quality_options": ["Auto (1080p+)"],
                "default_quality": "Auto",
                "media_type": "tv",
                "tmdb_id": tv_id,
                "season": season,
                "episode": episode
            }
        else:
            # Return TV show info (no specific episode)
            # Generate base embed URL for TV show
            embed_url = await vidsrc_service.get_tv_embed_url(tv_id, 1, 1)
            
            if not embed_url:
                logger.error(f"Failed to get embed URL for TV {tv_id}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Vidsrc service unavailable for TV shows"
                )
            
            return {
                "embed_url": embed_url,
                "quality_options": ["Auto (1080p+)"],
                "default_quality": "Auto",
                "media_type": "tv",
                "tmdb_id": tv_id,
                "message": "Specify season and episode parameters to watch specific episode"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Vidsrc embed for TV {tv_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500,
            detail="Internal server error"
        )