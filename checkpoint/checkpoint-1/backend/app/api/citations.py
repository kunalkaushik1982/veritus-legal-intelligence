"""
Citation analysis API endpoints
File: backend/app/api/citations.py
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.models.judgment import Judgment
from app.models.citation import Citation, CitationType
from app.services.citation_analyzer import CitationAnalyzer
from app.services.auth_service import AuthService

router = APIRouter()


class CitationAnalysisRequest(BaseModel):
    """Request model for citation analysis"""
    source_judgment_id: int = Field(..., description="ID of the judgment making the citation")
    target_judgment_id: int = Field(..., description="ID of the judgment being cited")
    context_text: str = Field(..., min_length=50, max_length=2000, description="Text containing the citation")


class CitationAnalysisResponse(BaseModel):
    """Response model for citation analysis"""
    citation_type: str
    strength_score: int
    confidence_score: int
    legal_principle: Optional[str]
    statute_reference: Optional[str]
    issue_category: Optional[str]
    is_positive: bool
    context: str


@router.post("/analyze", response_model=CitationAnalysisResponse)
async def analyze_citation(
    request: CitationAnalysisRequest,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze the strength and type of a citation relationship
    
    This endpoint analyzes how one judgment cites another, determining:
    - Type of citation (relied upon, distinguished, overruled, etc.)
    - Strength of the citation (0-100 score)
    - Legal principles involved
    - Whether the citation is positive or negative
    """
    try:
        # Verify judgments exist
        source_judgment = db.query(Judgment).filter(Judgment.id == request.source_judgment_id).first()
        target_judgment = db.query(Judgment).filter(Judgment.id == request.target_judgment_id).first()
        
        if not source_judgment or not target_judgment:
            raise HTTPException(
                status_code=404,
                detail="One or both judgments not found"
            )
        
        # Perform citation analysis
        analyzer = CitationAnalyzer(db)
        analysis_result = await analyzer.analyze_citation_strength(
            request.source_judgment_id,
            request.target_judgment_id,
            request.context_text
        )
        
        # Save citation to database
        citation = Citation(
            source_judgment_id=request.source_judgment_id,
            target_judgment_id=request.target_judgment_id,
            citation_type=CitationType(analysis_result["citation_type"]),
            context=request.context_text,
            strength_score=analysis_result["strength_score"],
            confidence_score=analysis_result["confidence_score"],
            is_positive=analysis_result["is_positive"],
            legal_principle=analysis_result.get("legal_principle"),
            statute_reference=analysis_result.get("statute_reference"),
            issue_category=analysis_result.get("issue_category")
        )
        
        db.add(citation)
        db.commit()
        
        return CitationAnalysisResponse(
            citation_type=analysis_result["citation_type"],
            strength_score=analysis_result["strength_score"],
            confidence_score=analysis_result["confidence_score"],
            legal_principle=analysis_result.get("legal_principle"),
            statute_reference=analysis_result.get("statute_reference"),
            issue_category=analysis_result.get("issue_category"),
            is_positive=analysis_result["is_positive"],
            context=request.context_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing citation: {str(e)}"
        )


@router.get("/network/{judgment_id}")
async def get_citation_network(
    judgment_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get citation network for a specific judgment
    
    Returns a network visualization of how the judgment relates to other cases
    through citations, including strength scores and relationship types.
    """
    try:
        # Verify judgment exists
        judgment = db.query(Judgment).filter(Judgment.id == judgment_id).first()
        if not judgment:
            raise HTTPException(
                status_code=404,
                detail="Judgment not found"
            )
        
        # Build citation network
        analyzer = CitationAnalyzer(db)
        network_result = await analyzer.build_citation_network(judgment_id)
        
        return network_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error building citation network: {str(e)}"
        )


@router.get("/statistics/{judgment_id}")
async def get_citation_statistics(
    judgment_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive citation statistics for a judgment
    
    Provides detailed metrics about how the judgment has been cited
    and how it cites other judgments.
    """
    try:
        # Verify judgment exists
        judgment = db.query(Judgment).filter(Judgment.id == judgment_id).first()
        if not judgment:
            raise HTTPException(
                status_code=404,
                detail="Judgment not found"
            )
        
        # Get citation statistics
        analyzer = CitationAnalyzer(db)
        stats = await analyzer.get_citation_statistics(judgment_id)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting citation statistics: {str(e)}"
        )


@router.get("/strength-ranking")
async def get_citation_strength_ranking(
    limit: int = Query(default=20, ge=1, le=100),
    citation_type: Optional[str] = Query(default=None),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get ranking of judgments by citation strength
    
    Returns judgments ranked by their influence and citation strength,
    useful for identifying landmark cases.
    """
    try:
        # Build query
        query = db.query(Citation)
        
        if citation_type:
            try:
                citation_type_enum = CitationType(citation_type)
                query = query.filter(Citation.citation_type == citation_type_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid citation type: {citation_type}"
                )
        
        # Get citations with strength scores
        citations = query.filter(Citation.strength_score.isnot(None)).all()
        
        # Group by target judgment and calculate average strength
        judgment_strengths = {}
        for citation in citations:
            target_id = citation.target_judgment_id
            if target_id not in judgment_strengths:
                judgment_strengths[target_id] = []
            judgment_strengths[target_id].append(citation.strength_score)
        
        # Calculate average strengths
        ranking = []
        for judgment_id, strengths in judgment_strengths.items():
            avg_strength = sum(strengths) / len(strengths)
            ranking.append({
                "judgment_id": judgment_id,
                "average_strength": avg_strength,
                "citation_count": len(strengths),
                "max_strength": max(strengths),
                "min_strength": min(strengths)
            })
        
        # Sort by average strength
        ranking.sort(key=lambda x: x["average_strength"], reverse=True)
        
        # Get judgment details for top results
        top_judgment_ids = [item["judgment_id"] for item in ranking[:limit]]
        judgments = db.query(Judgment).filter(Judgment.id.in_(top_judgment_ids)).all()
        judgment_dict = {j.id: j for j in judgments}
        
        # Format results
        results = []
        for item in ranking[:limit]:
            judgment = judgment_dict.get(item["judgment_id"])
            if judgment:
                results.append({
                    "judgment_id": item["judgment_id"],
                    "case_title": judgment.case_title,
                    "case_number": judgment.case_number,
                    "judgment_date": judgment.judgment_date.isoformat() if judgment.judgment_date else None,
                    "average_strength": round(item["average_strength"], 2),
                    "citation_count": item["citation_count"],
                    "max_strength": item["max_strength"],
                    "min_strength": item["min_strength"]
                })
        
        return {
            "ranking": results,
            "total_judgments": len(ranking),
            "limit": limit,
            "citation_type": citation_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting citation strength ranking: {str(e)}"
        )
