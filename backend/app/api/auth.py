"""
Authentication API endpoints
File: backend/app/api/auth.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt

from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService
from app.utils.security import verify_password, get_password_hash
from app.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/register")
async def register(
    email: str,
    username: str,
    full_name: str,
    password: str,
    bar_council_number: Optional[str] = None,
    practice_area: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    try:
        auth_service = AuthService(db)
        
        # Check if user already exists
        if auth_service.get_user_by_email(email):
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        if auth_service.get_user_by_username(username):
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        
        # Create new user
        user = auth_service.create_user(
            email=email,
            username=username,
            full_name=full_name,
            password=password,
            bar_council_number=bar_council_number,
            practice_area=practice_area
        )
        
        return {
            "message": "User registered successfully",
            "user_id": user.id,
            "email": user.email,
            "username": user.username
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token"""
    try:
        auth_service = AuthService(db)
        
        # Authenticate user
        user = auth_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate access token
        access_token = auth_service.create_access_token(user.id)
        
        # Update last login
        auth_service.update_last_login(user.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "subscription_tier": user.subscription_tier.value
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "subscription_tier": current_user.subscription_tier.value,
        "bar_council_number": current_user.bar_council_number,
        "practice_area": current_user.practice_area,
        "experience_years": current_user.experience_years,
        "queries_today": current_user.queries_today,
        "total_queries": current_user.total_queries,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }


@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Refresh access token"""
    try:
        auth_service = AuthService(db)
        new_token = auth_service.create_access_token(current_user.id)
        
        return {
            "access_token": new_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Logout user (client should discard token)"""
    return {"message": "Successfully logged out"}


@router.put("/profile")
async def update_profile(
    full_name: Optional[str] = None,
    practice_area: Optional[str] = None,
    bio: Optional[str] = None,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    try:
        auth_service = AuthService(db)
        
        updated_user = auth_service.update_profile(
            user_id=current_user.id,
            full_name=full_name,
            practice_area=practice_area,
            bio=bio
        )
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user.id,
                "full_name": updated_user.full_name,
                "practice_area": updated_user.practice_area,
                "bio": updated_user.bio
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Profile update failed: {str(e)}"
        )
