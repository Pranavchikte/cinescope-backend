from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.api.deps import get_current_user, get_verified_user
from app.models.user import User, UserRole
from app.models.creator_request import CreatorRequest, RequestStatus
from app.schemas.creator_request import CreatorRequestCreate, CreatorRequestUpdate, CreatorRequestResponse

router = APIRouter()

def require_admin(current_user: User = Depends(get_verified_user)):
    """Dependency to check if user is admin"""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.post("", response_model=CreatorRequestResponse, status_code=201)
def request_creator_access(
    data: CreatorRequestCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """Request creator access"""
    # Check if already a creator
    if current_user.role == UserRole.creator or current_user.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="You already have creator access")
    
    # Check if already has pending request
    existing = db.query(CreatorRequest).filter(
        CreatorRequest.user_id == current_user.id,
        CreatorRequest.status == RequestStatus.pending
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending request")
    
    # Create request
    request = CreatorRequest(
        user_id=current_user.id,
        message=data.message,
        status=RequestStatus.pending
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    # Add username to response
    response = CreatorRequestResponse.model_validate(request)
    response.username = current_user.username
    return response

@router.get("", response_model=List[CreatorRequestResponse])
def get_creator_requests(
    status_filter: str = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all creator requests (admin only)"""
    query = db.query(CreatorRequest)
    
    if status_filter:
        query = query.filter(CreatorRequest.status == status_filter)
    
    requests = query.order_by(CreatorRequest.created_at.desc()).all()
    
    # Add usernames
    result = []
    for req in requests:
        response = CreatorRequestResponse.model_validate(req)
        response.username = req.user.username
        result.append(response)
    
    return result

@router.patch("/{request_id}/approve", response_model=CreatorRequestResponse)
def approve_creator_request(
    request_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Approve creator request (admin only)"""
    request = db.query(CreatorRequest).filter(CreatorRequest.id == request_id).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status != RequestStatus.pending:
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Update request
    request.status = RequestStatus.approved
    request.reviewed_by = current_user.id
    request.reviewed_at = datetime.utcnow()
    
    # Grant creator role to user
    user = db.query(User).filter(User.id == request.user_id).first()
    user.role = UserRole.creator
    
    db.commit()
    db.refresh(request)
    
    response = CreatorRequestResponse.model_validate(request)
    response.username = user.username
    return response

@router.patch("/{request_id}/reject", response_model=CreatorRequestResponse)
def reject_creator_request(
    request_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Reject creator request (admin only)"""
    request = db.query(CreatorRequest).filter(CreatorRequest.id == request_id).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status != RequestStatus.pending:
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Update request
    request.status = RequestStatus.rejected
    request.reviewed_by = current_user.id
    request.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(request)
    
    response = CreatorRequestResponse.model_validate(request)
    response.username = request.user.username
    return response

@router.get("/my-request", response_model=CreatorRequestResponse)
def get_my_creator_request(
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """Get current user's creator request"""
    request = db.query(CreatorRequest).filter(
        CreatorRequest.user_id == current_user.id
    ).order_by(CreatorRequest.created_at.desc()).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="No request found")
    
    response = CreatorRequestResponse.model_validate(request)
    response.username = current_user.username
    return response