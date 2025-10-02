"""
Judgment data model for Supreme Court cases
File: backend/app/models/judgment.py
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Judgment(Base):
    """Supreme Court judgment model"""
    __tablename__ = "judgments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Case identification
    case_number = Column(String(100), unique=True, index=True, nullable=False)
    case_title = Column(String(500), nullable=False)
    petitioner = Column(String(500), nullable=True)
    respondent = Column(String(500), nullable=True)
    
    # Court information
    court = Column(String(100), default="Supreme Court of India")
    bench = Column(String(200), nullable=True)
    judges = Column(JSON, nullable=True)  # List of judge names
    
    # Case details
    case_date = Column(DateTime, nullable=True)
    judgment_date = Column(DateTime, nullable=True)
    case_type = Column(String(100), nullable=True)
    
    # Legal content
    statutes_cited = Column(JSON, nullable=True)  # List of statutes
    issues_framed = Column(JSON, nullable=True)  # List of legal issues
    ratio_decidendi = Column(Text, nullable=True)  # Core legal principle
    
    # Full text and processing
    full_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)  # Extracted key legal points
    
    # File information
    pdf_url = Column(String(500), nullable=True)
    pdf_size = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")
    entities_extracted = Column(Boolean, default=False)
    citations_extracted = Column(Boolean, default=False)
    embeddings_generated = Column(Boolean, default=False)
    
    # Metadata
    source = Column(String(100), default="Supreme Court")
    year = Column(Integer, nullable=True)
    month = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    citations_as_source = relationship("Citation", foreign_keys="Citation.source_judgment_id", back_populates="source_judgment")
    citations_as_target = relationship("Citation", foreign_keys="Citation.target_judgment_id", back_populates="target_judgment")


