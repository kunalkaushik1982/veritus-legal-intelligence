"""
Collaborative Editing Models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Document(Base):
    """Document model for collaborative editing"""
    __tablename__ = "collab_documents"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=False)
    is_locked = Column(Boolean, default=False)
    version = Column(Integer, default=0)
    
    # Relationships
    operations = relationship("Operation", back_populates="document", cascade="all, delete-orphan")
    snapshots = relationship("Snapshot", back_populates="document", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="document", cascade="all, delete-orphan")

class Operation(Base):
    """Operation model for Operational Transform"""
    __tablename__ = "collab_operations"
    
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("collab_documents.id"), nullable=False)
    user_id = Column(String, nullable=False)
    username = Column(String, nullable=False)
    operation_type = Column(String, nullable=False)  # 'insert', 'delete', 'retain'
    position = Column(Integer, nullable=False)
    content = Column(Text, default="")
    length = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="operations")

class Snapshot(Base):
    """Document snapshot for version history"""
    __tablename__ = "collab_snapshots"
    
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("collab_documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=False)
    snapshot_metadata = Column(JSON, default=dict)
    
    # Relationships
    document = relationship("Document", back_populates="snapshots")

class Comment(Base):
    """Comment model for document comments"""
    __tablename__ = "collab_comments"
    
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("collab_documents.id"), nullable=False)
    user_id = Column(String, nullable=False)
    username = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    anchor_node_id = Column(String, nullable=True)
    anchor_offset = Column(Integer, nullable=True)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_resolved = Column(Boolean, default=False)
    
    # Relationships
    document = relationship("Document", back_populates="comments")

class Presence(Base):
    """User presence tracking"""
    __tablename__ = "collab_presence"
    
    id = Column(String, primary_key=True)
    document_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    username = Column(String, nullable=False)
    cursor_position = Column(Integer, default=0)
    selection_start = Column(Integer, default=0)
    selection_end = Column(Integer, default=0)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
