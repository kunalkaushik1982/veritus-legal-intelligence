"""
Database configuration and connection management
File: backend/app/database.py
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from typing import Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy setup
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_db() -> Generator:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis() -> redis.Redis:
    """Get Redis client instance"""
    return redis_client


async def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they're registered
        from app.models import user, judgment, citation, entity, query
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def check_db_connection():
    """Check database connectivity"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def check_redis_connection():
    """Check Redis connectivity"""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False
