"""
Citation relationship model for case law analysis
File: backend/app/models/citation.py
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.database import Base


class CitationType(PyEnum):
    """Citation relationship types"""
    RELIED_UPON = "relied_upon"
    DISTINGUISHED = "distinguished"
    OVERRULED = "overruled"
    REFERRED = "referred"
    FOLLOWED = "followed"
    CITED = "cited"


class Citation(Base):
    """Citation relationship between judgments"""
    __tablename__ = "citations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Source and target judgments
    source_judgment_id = Column(Integer, ForeignKey("judgments.id"), nullable=False)
    target_judgment_id = Column(Integer, ForeignKey("judgments.id"), nullable=False)
    
    # Citation details
    citation_type = Column(Enum(CitationType), nullable=False)
    context = Column(Text, nullable=True)  # Context where citation appears
    page_number = Column(Integer, nullable=True)
    paragraph_number = Column(Integer, nullable=True)
    
    # Strength analysis
    strength_score = Column(Integer, nullable=True)  # 0-100
    confidence_score = Column(Integer, nullable=True)  # 0-100
    is_positive = Column(Boolean, default=True)  # True if supports, False if opposes
    
    # Legal significance
    legal_principle = Column(Text, nullable=True)
    statute_reference = Column(String(200), nullable=True)
    issue_category = Column(String(100), nullable=True)
    
    # Processing metadata
    extraction_method = Column(String(50), default="ai")  # ai, manual, hybrid
    is_verified = Column(Boolean, default=False)
    verification_source = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    source_judgment = relationship("Judgment", foreign_keys=[source_judgment_id], back_populates="citations_as_source")
    target_judgment = relationship("Judgment", foreign_keys=[target_judgment_id], back_populates="citations_as_target")


class CitationNetwork(Base):
    """Precomputed citation network for performance"""
    __tablename__ = "citation_networks"
    
    id = Column(Integer, primary_key=True, index=True)
    judgment_id = Column(Integer, ForeignKey("judgments.id"), nullable=False)
    
    # Network metrics
    citation_count = Column(Integer, default=0)
    cited_by_count = Column(Integer, default=0)
    influence_score = Column(Integer, nullable=True)  # 0-100
    authority_score = Column(Integer, nullable=True)  # 0-100
    
    # Network data (JSON for flexibility)
    direct_citations = Column(Text, nullable=True)  # JSON array of judgment IDs
    indirect_citations = Column(Text, nullable=True)  # JSON array of judgment IDs
    citation_paths = Column(Text, nullable=True)  # JSON of citation paths
    
    # Timestamps
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    judgment = relationship("Judgment")
