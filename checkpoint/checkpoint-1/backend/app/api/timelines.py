"""
Timeline extraction API endpoints
File: backend/app/api/timelines.py
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.models.judgment import Judgment
from app.models.entity import Entity, Timeline, EntityType
from app.services.entity_extractor import EntityExtractor
from app.services.auth_service import AuthService

router = APIRouter()


class TimelineExtractionRequest(BaseModel):
    """Request model for timeline extraction"""
    judgment_id: int = Field(..., description="ID of the judgment to analyze")


class TimelineExtractionResponse(BaseModel):
    """Response model for timeline extraction"""
    judgment_id: int
    timeline_events: List[Dict[str, Any]]
    extracted_entities: List[Dict[str, Any]]
    processing_time_ms: int


@router.post("/extract", response_model=TimelineExtractionResponse)
async def extract_timeline(
    request: TimelineExtractionRequest,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract timeline and entities from a judgment
    
    Analyzes the judgment text to identify:
    - Chronological events and dates
    - Legal entities (parties, judges, statutes)
    - Key legal issues and principles
    """
    try:
        # Verify judgment exists
        judgment = db.query(Judgment).filter(Judgment.id == request.judgment_id).first()
        if not judgment:
            raise HTTPException(
                status_code=404,
                detail="Judgment not found"
            )
        
        # Extract timeline and entities
        extractor = EntityExtractor(db)
        result = await extractor.extract_timeline_and_entities(
            judgment_id=request.judgment_id,
            text=judgment.full_text
        )
        
        return TimelineExtractionResponse(
            judgment_id=request.judgment_id,
            timeline_events=result["timeline_events"],
            extracted_entities=result["extracted_entities"],
            processing_time_ms=result["processing_time_ms"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting timeline: {str(e)}"
        )


@router.get("/judgment/{judgment_id}")
async def get_judgment_timeline(
    judgment_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get timeline and entities for a specific judgment"""
    try:
        # Get timeline events
        timeline_events = db.query(Timeline).filter(
            Timeline.judgment_id == judgment_id
        ).order_by(Timeline.event_date.asc()).all()
        
        # Get extracted entities
        entities = db.query(Entity).filter(
            Entity.judgment_id == judgment_id
        ).all()
        
        # Format response
        formatted_timeline = []
        for event in timeline_events:
            formatted_timeline.append({
                "id": event.id,
                "event_date": event.event_date.isoformat() if event.event_date else None,
                "event_description": event.event_description,
                "event_type": event.event_type,
                "parties_involved": event.parties_involved,
                "court_involved": event.court_involved,
                "legal_significance": event.legal_significance,
                "confidence_score": event.confidence_score
            })
        
        formatted_entities = []
        for entity in entities:
            formatted_entities.append({
                "id": entity.id,
                "entity_type": entity.entity_type.value,
                "entity_text": entity.entity_text,
                "normalized_text": entity.normalized_text,
                "confidence_score": entity.confidence_score,
                "is_primary": entity.is_primary,
                "context": entity.context,
                "metadata": entity.metadata
            })
        
        return {
            "judgment_id": judgment_id,
            "timeline_events": formatted_timeline,
            "extracted_entities": formatted_entities,
            "total_events": len(formatted_timeline),
            "total_entities": len(formatted_entities)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving timeline: {str(e)}"
        )
