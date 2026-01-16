from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.token import Token
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, create_password_reset_token, verify_password_reset_token
from app.schemas.user import UserCreate, UserLogin, UserResponse, ForgotPasswordRequest, ResetPasswordRequest, MessageResponse
from app.services.email import email_service


router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
    
@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset email"""
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success (don't reveal if email exists)
    if not user:
        return {"message": "If that email exists, a reset link has been sent"}
    
    # Create reset token
    reset_token = create_password_reset_token(user.email)
    
    # Send email
    email_sent = await email_service.send_password_reset_email(user.email, reset_token)
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send email")
    
    return {"message": "If that email exists, a reset link has been sent"}

@router.post("/reset-password", response_model=MessageResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token"""
    # Verify token
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Get user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password
    user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Password reset successful"}