"""
User management API endpoints
File: backend/app/api/users.py
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User, Team
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed user profile information"""
    try:
        return {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "bar_council_number": current_user.bar_council_number,
            "practice_area": current_user.practice_area,
            "experience_years": current_user.experience_years,
            "bio": current_user.bio,
            "role": current_user.role.value,
            "subscription_tier": current_user.subscription_tier.value,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "queries_today": current_user.queries_today,
            "total_queries": current_user.total_queries,
            "created_at": current_user.created_at.isoformat(),
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving profile: {str(e)}"
        )


@router.put("/profile")
async def update_user_profile(
    full_name: Optional[str] = Field(None, max_length=255),
    practice_area: Optional[str] = Field(None, max_length=255),
    bio: Optional[str] = Field(None, max_length=1000),
    experience_years: Optional[int] = Field(None, ge=0, le=50),
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
        
        # Update experience years if provided
        if experience_years is not None:
            updated_user.experience_years = experience_years
            db.commit()
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user.id,
                "full_name": updated_user.full_name,
                "practice_area": updated_user.practice_area,
                "bio": updated_user.bio,
                "experience_years": updated_user.experience_years
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating profile: {str(e)}"
        )


@router.get("/usage")
async def get_usage_statistics(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's usage statistics"""
    try:
        from app.models.judgment import Query
        
        # Get query statistics
        total_queries = db.query(Query).filter(Query.user_id == current_user.id).count()
        
        # Get queries by type
        query_types = db.query(Query.query_type, db.func.count(Query.id)).filter(
            Query.user_id == current_user.id
        ).group_by(Query.query_type).all()
        
        # Get average confidence score
        avg_confidence = db.query(Query).filter(
            Query.user_id == current_user.id,
            Query.confidence_score.isnot(None)
        ).with_entities(
            db.func.avg(Query.confidence_score)
        ).scalar() or 0
        
        return {
            "total_queries": total_queries,
            "queries_today": current_user.queries_today,
            "queries_by_type": dict(query_types),
            "average_confidence_score": round(avg_confidence, 1),
            "subscription_tier": current_user.subscription_tier.value,
            "daily_limit": current_user.subscription_tier.value == "free" and 20 or 1000,
            "queries_remaining": max(0, (current_user.subscription_tier.value == "free" and 20 or 1000) - current_user.queries_today)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving usage statistics: {str(e)}"
        )


@router.get("/saved-judgments")
async def get_saved_judgments(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's saved judgments"""
    try:
        from app.models.user import SavedJudgment
        
        saved_judgments = db.query(SavedJudgment).filter(
            SavedJudgment.user_id == current_user.id
        ).offset(offset).limit(limit).all()
        
        results = []
        for saved in saved_judgments:
            results.append({
                "id": saved.id,
                "judgment_id": saved.judgment_id,
                "case_title": saved.judgment.case_title,
                "case_number": saved.judgment.case_number,
                "judgment_date": saved.judgment.judgment_date.isoformat() if saved.judgment.judgment_date else None,
                "notes": saved.notes,
                "tags": saved.tags.split(",") if saved.tags else [],
                "saved_at": saved.created_at.isoformat()
            })
        
        total_count = db.query(SavedJudgment).filter(SavedJudgment.user_id == current_user.id).count()
        
        return {
            "saved_judgments": results,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving saved judgments: {str(e)}"
        )


@router.post("/save-judgment/{judgment_id}")
async def save_judgment(
    judgment_id: int,
    notes: Optional[str] = Field(None, max_length=1000),
    tags: Optional[str] = Field(None, max_length=500),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Save a judgment to user's collection"""
    try:
        from app.models.user import SavedJudgment
        from app.models.judgment import Judgment
        
        # Check if judgment exists
        judgment = db.query(Judgment).filter(Judgment.id == judgment_id).first()
        if not judgment:
            raise HTTPException(
                status_code=404,
                detail="Judgment not found"
            )
        
        # Check if already saved
        existing = db.query(SavedJudgment).filter(
            SavedJudgment.user_id == current_user.id,
            SavedJudgment.judgment_id == judgment_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Judgment already saved"
            )
        
        # Save judgment
        saved_judgment = SavedJudgment(
            user_id=current_user.id,
            judgment_id=judgment_id,
            notes=notes,
            tags=tags
        )
        
        db.add(saved_judgment)
        db.commit()
        
        return {
            "message": "Judgment saved successfully",
            "saved_judgment_id": saved_judgment.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error saving judgment: {str(e)}"
        )
