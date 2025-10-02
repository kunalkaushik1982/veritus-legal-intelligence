"""
Entity extraction model for legal document analysis
File: backend/app/models/entity.py
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.database import Base


class EntityType(PyEnum):
    """Types of entities that can be extracted"""
    PARTY = "party"
    JUDGE = "judge"
    STATUTE = "statute"
    CASE_LAW = "case_law"
    DATE = "date"
    ISSUE = "issue"
    PRINCIPLE = "principle"
    COURT = "court"
    LOCATION = "location"
    AMOUNT = "amount"


class Entity(Base):
    """Extracted entities from legal documents"""
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True, index=True)
    judgment_id = Column(Integer, ForeignKey("judgments.id"), nullable=False)
    
    # Entity details
    entity_type = Column(Enum(EntityType), nullable=False)
    entity_text = Column(String(500), nullable=False)
    normalized_text = Column(String(500), nullable=True)  # Standardized version
    
    # Position in document
    start_position = Column(Integer, nullable=True)
    end_position = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)
    paragraph_number = Column(Integer, nullable=True)
    
    # Entity properties
    confidence_score = Column(Integer, nullable=True)  # 0-100
    is_primary = Column(Boolean, default=False)  # Primary vs secondary entity
    context = Column(Text, nullable=True)  # Surrounding text
    
    # Additional metadata
    entity_metadata = Column(JSON, nullable=True)  # Flexible additional data
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    # Processing information
    extraction_method = Column(String(50), default="ai")  # ai, regex, manual
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # judgment = relationship("app.models.judgment.Judgment", back_populates="entities")


class Timeline(Base):
    """Timeline events extracted from judgments"""
    __tablename__ = "timelines"
    
    id = Column(Integer, primary_key=True, index=True)
    judgment_id = Column(Integer, ForeignKey("judgments.id"), nullable=False)
    
    # Event details
    event_date = Column(DateTime, nullable=True)
    event_description = Column(Text, nullable=False)
    event_type = Column(String(100), nullable=True)  # filing, hearing, judgment, etc.
    
    # Event context
    parties_involved = Column(JSON, nullable=True)  # List of party names
    court_involved = Column(String(200), nullable=True)
    legal_significance = Column(Text, nullable=True)
    
    # Position in document
    page_number = Column(Integer, nullable=True)
    paragraph_number = Column(Integer, nullable=True)
    
    # Processing metadata
    confidence_score = Column(Integer, nullable=True)  # 0-100
    extraction_method = Column(String(50), default="ai")
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    # judgment = relationship("app.models.judgment.Judgment", back_populates="timelines")
