"""
User and team management models
File: backend/app/models/user.py
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.database import Base


class UserRole(PyEnum):
    """User role enumeration"""
    ADMIN = "admin"
    MEMBER = "member"
    FREE = "free"
    PRO = "pro"
    TEAM = "team"


class User(Base):
    """User model for individual advocates and team members"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    bar_council_number = Column(String(100), nullable=True)
    practice_area = Column(String(255), nullable=True)
    experience_years = Column(Integer, default=0)
    bio = Column(Text, nullable=True)
    
    # Account settings
    role = Column(Enum(UserRole), default=UserRole.FREE)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    subscription_tier = Column(Enum(UserRole), default=UserRole.FREE)
    
    # Team management
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    team_role = Column(Enum(UserRole), default=UserRole.MEMBER)
    
    # Usage tracking
    queries_today = Column(Integer, default=0)
    last_query_date = Column(DateTime, nullable=True)
    total_queries = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    team = relationship("Team", back_populates="members")
    queries = relationship("Query", back_populates="user")
    saved_judgments = relationship("SavedJudgment", back_populates="user")


class Team(Base):
    """Team model for law firms and organizations"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Team settings
    max_members = Column(Integer, default=10)
    subscription_tier = Column(Enum(UserRole), default=UserRole.TEAM)
    
    # Billing
    billing_email = Column(String(255), nullable=True)
    subscription_status = Column(String(50), default="active")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    members = relationship("User", back_populates="team")
    admin = relationship("User", foreign_keys="User.team_id", uselist=False)


class SavedJudgment(Base):
    """User's saved judgments for quick access"""
    __tablename__ = "saved_judgments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    judgment_id = Column(Integer, ForeignKey("judgments.id"), nullable=False)
    
    # Personal notes
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="saved_judgments")
    judgment = relationship("Judgment", back_populates="saved_by_users")
