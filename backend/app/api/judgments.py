"""
Judgment search API endpoints
File: backend/app/api/judgments.py
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.models.judgment import Judgment
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/search")
async def search_judgments(
    query: str = Query(..., min_length=3, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    year_from: Optional[int] = Query(default=None),
    year_to: Optional[int] = Query(default=None),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search judgments by text content
    
    Allows searching through judgment titles, case numbers, and content
    to find relevant Supreme Court cases.
    """
    try:
        # Build search query
        search_query = db.query(Judgment).filter(
            Judgment.case_title.ilike(f"%{query}%")
        )
        
        # Apply year filters
        if year_from:
            search_query = search_query.filter(Judgment.year >= year_from)
        if year_to:
            search_query = search_query.filter(Judgment.year <= year_to)
        
        # Execute search
        judgments = search_query.limit(limit).all()
        
        # Format results
        results = []
        for judgment in judgments:
            results.append({
                "id": judgment.id,
                "case_title": judgment.case_title,
                "case_number": judgment.case_number,
                "petitioner": judgment.petitioner,
                "respondent": judgment.respondent,
                "judgment_date": judgment.judgment_date.isoformat() if judgment.judgment_date else None,
                "year": judgment.year,
                "summary": judgment.summary,
                "statutes_cited": judgment.statutes_cited,
                "is_processed": judgment.is_processed
            })
        
        return {
            "results": results,
            "total_found": len(results),
            "query": query,
            "filters": {
                "year_from": year_from,
                "year_to": year_to
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching judgments: {str(e)}"
        )


@router.get("/{judgment_id}")
async def get_judgment_details(
    judgment_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific judgment"""
    try:
        judgment = db.query(Judgment).filter(Judgment.id == judgment_id).first()
        
        if not judgment:
            raise HTTPException(
                status_code=404,
                detail="Judgment not found"
            )
        
        return {
            "id": judgment.id,
            "case_title": judgment.case_title,
            "case_number": judgment.case_number,
            "petitioner": judgment.petitioner,
            "respondent": judgment.respondent,
            "court": judgment.court,
            "bench": judgment.bench,
            "judges": judgment.judges,
            "case_date": judgment.case_date.isoformat() if judgment.case_date else None,
            "judgment_date": judgment.judgment_date.isoformat() if judgment.judgment_date else None,
            "case_type": judgment.case_type,
            "statutes_cited": judgment.statutes_cited,
            "issues_framed": judgment.issues_framed,
            "ratio_decidendi": judgment.ratio_decidendi,
            "summary": judgment.summary,
            "key_points": judgment.key_points,
            "year": judgment.year,
            "month": judgment.month,
            "is_processed": judgment.is_processed,
            "processing_status": judgment.processing_status,
            "created_at": judgment.created_at.isoformat(),
            "updated_at": judgment.updated_at.isoformat() if judgment.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving judgment: {str(e)}"
        )


@router.get("/")
async def list_judgments(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    year: Optional[int] = Query(default=None),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """List judgments with optional filtering"""
    try:
        query = db.query(Judgment)
        
        if year:
            query = query.filter(Judgment.year == year)
        
        judgments = query.offset(offset).limit(limit).all()
        
        results = []
        for judgment in judgments:
            results.append({
                "id": judgment.id,
                "case_title": judgment.case_title,
                "case_number": judgment.case_number,
                "judgment_date": judgment.judgment_date.isoformat() if judgment.judgment_date else None,
                "year": judgment.year,
                "summary": judgment.summary,
                "is_processed": judgment.is_processed
            })
        
        total_count = query.count()
        
        return {
            "judgments": results,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing judgments: {str(e)}"
        )
