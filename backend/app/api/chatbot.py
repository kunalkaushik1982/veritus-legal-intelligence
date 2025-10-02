"""
Chatbot API endpoints for legal queries
File: backend/app/api/chatbot.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.judgment import Query
from app.services.ai_service import AIService
from app.services.auth_service import AuthService
from app.utils.validators import validate_query_length

router = APIRouter()


class ChatbotQuery(BaseModel):
    """Request model for chatbot queries"""
    query: str = Field(..., min_length=10, max_length=1000, description="Legal query text")
    context_limit: int = Field(default=5, ge=1, le=10, description="Number of judgments to retrieve")


class ChatbotResponse(BaseModel):
    """Response model for chatbot queries"""
    response: str
    citations: List[Dict[str, Any]]
    relevant_judgments: List[int]
    confidence_score: int
    response_time_ms: int
    tokens_used: int
    query_intent: str


@router.post("/query", response_model=ChatbotResponse)
async def process_legal_query(
    query_data: ChatbotQuery,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process a legal query using AI-powered chatbot
    
    This endpoint handles natural language queries about legal matters,
    retrieves relevant Supreme Court judgments, and provides contextual answers.
    """
    try:
        # Validate query
        if not validate_query_length(query_data.query):
            raise HTTPException(
                status_code=400,
                detail="Query must be between 10 and 1000 characters"
            )
        
        # Check user's query limit
        auth_service = AuthService(db)
        if not auth_service.check_query_limit(current_user.id):
            raise HTTPException(
                status_code=429,
                detail="Daily query limit exceeded. Please upgrade your plan for unlimited queries."
            )
        
        # Process query with AI service
        ai_service = AIService()
        result = await ai_service.process_legal_query(
            query=query_data.query,
            user_id=current_user.id,
            context_limit=query_data.context_limit
        )
        
        # Save query to database
        query_record = Query(
            user_id=current_user.id,
            query_text=query_data.query,
            query_type="chatbot",
            query_intent=result.get("query_intent", "general"),
            response_text=result["response"],
            relevant_judgments=result.get("relevant_judgments", []),
            citations_found=result.get("citations", []),
            response_time_ms=result["response_time_ms"],
            tokens_used=result.get("tokens_used", 0),
            confidence_score=result["confidence_score"]
        )
        
        db.add(query_record)
        
        # Update user's query count
        auth_service.increment_query_count(current_user.id)
        
        db.commit()
        
        return ChatbotResponse(
            response=result["response"],
            citations=result.get("citations", []),
            relevant_judgments=result.get("relevant_judgments", []),
            confidence_score=result["confidence_score"],
            response_time_ms=result["response_time_ms"],
            tokens_used=result.get("tokens_used", 0),
            query_intent=result.get("query_intent", "general")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/history")
async def get_query_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's query history"""
    try:
        queries = db.query(Query).filter(
            Query.user_id == current_user.id
        ).order_by(
            Query.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "queries": [
                {
                    "id": query.id,
                    "query_text": query.query_text,
                    "query_type": query.query_type,
                    "query_intent": query.query_intent,
                    "response_text": query.response_text[:200] + "..." if len(query.response_text) > 200 else query.response_text,
                    "confidence_score": query.confidence_score,
                    "response_time_ms": query.response_time_ms,
                    "created_at": query.created_at,
                    "user_rating": query.user_rating
                }
                for query in queries
            ],
            "total_count": db.query(Query).filter(Query.user_id == current_user.id).count(),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving query history: {str(e)}"
        )


@router.post("/feedback/{query_id}")
async def submit_query_feedback(
    query_id: int,
    rating: int = Field(..., ge=1, le=5),
    feedback: Optional[str] = Field(None, max_length=500),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for a specific query"""
    try:
        query = db.query(Query).filter(
            Query.id == query_id,
            Query.user_id == current_user.id
        ).first()
        
        if not query:
            raise HTTPException(
                status_code=404,
                detail="Query not found"
            )
        
        query.user_rating = rating
        query.user_feedback = feedback
        
        db.commit()
        
        return {
            "message": "Feedback submitted successfully",
            "query_id": query_id,
            "rating": rating
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting feedback: {str(e)}"
        )


@router.get("/suggestions")
async def get_query_suggestions(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get suggested queries based on user's practice area"""
    suggestions = [
        "What are the key principles for anticipatory bail under Section 438 CrPC?",
        "How has the Supreme Court interpreted Article 21 of the Constitution?",
        "What are the requirements for maintenance under Section 125 CrPC?",
        "How does the court determine compensation in motor accident cases?",
        "What are the grounds for divorce under Hindu Marriage Act?",
        "How has the court interpreted the right to privacy in recent judgments?",
        "What are the principles for granting interim relief in civil cases?",
        "How does the court handle cases involving fundamental rights violations?"
    ]
    
    return {
        "suggestions": suggestions,
        "practice_area": current_user.practice_area,
        "message": "These are popular legal research queries. Click any suggestion to get started."
    }


@router.get("/stats")
async def get_chatbot_stats(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chatbot usage statistics"""
    try:
        total_queries = db.query(Query).filter(Query.user_id == current_user.id).count()
        
        avg_confidence = db.query(Query).filter(
            Query.user_id == current_user.id,
            Query.confidence_score.isnot(None)
        ).with_entities(
            db.func.avg(Query.confidence_score)
        ).scalar() or 0
        
        avg_response_time = db.query(Query).filter(
            Query.user_id == current_user.id,
            Query.response_time_ms.isnot(None)
        ).with_entities(
            db.func.avg(Query.response_time_ms)
        ).scalar() or 0
        
        return {
            "total_queries": total_queries,
            "queries_today": current_user.queries_today,
            "average_confidence_score": round(avg_confidence, 1),
            "average_response_time_ms": round(avg_response_time, 0),
            "subscription_tier": current_user.subscription_tier.value,
            "daily_limit": current_user.subscription_tier.value == "free" and 20 or 1000
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving stats: {str(e)}"
        )
