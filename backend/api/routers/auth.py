from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import User
from schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from auth import (
    verify_password,
    get_password_hash,
    create_tokens_for_user,
    get_current_active_user,
    decode_token
)
import os

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Check if registration is enabled
    enable_registration = os.getenv("ENABLE_REGISTRATION", "true").lower() == "true"
    if not enable_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hashed_password,
        role="user"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user and return JWT tokens"""
    # Find user
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get client IP and user agent
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Create tokens
    tokens = create_tokens_for_user(user, db, ip_address, user_agent)

    return tokens

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        payload = decode_token(refresh_token)
        token_type = payload.get("type")
        user_id = payload.get("sub")

        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Get client IP and user agent
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Create new tokens
        tokens = create_tokens_for_user(user, db, ip_address, user_agent)

        return tokens

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout user (invalidate tokens)"""
    # In a production system, you would invalidate the token here
    # For now, we'll just return success
    # The client should delete the token
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user
