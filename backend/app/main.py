"""
Veritus Legal Intelligence Platform - FastAPI Application Entry Point
File: backend/app/main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.config import settings
from app.database import init_db
from app.api import auth, citations, timelines, judgments, users, test

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events"""
    # Startup
    try:
        await init_db()
        logger.info("🚀 Veritus backend started successfully!")
        logger.info(f"📊 Database: {settings.DATABASE_URL}")
        logger.info(f"🔑 OpenAI API: {'Configured' if settings.OPENAI_API_KEY else 'Not configured'}")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("👋 Veritus backend shutting down...")


# Initialize FastAPI application
app = FastAPI(
    title="Veritus Legal Intelligence API",
    description="AI-powered legal research and analysis platform for Supreme Court judgments",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(test.router, prefix="/api/test", tags=["Test"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(citations.router, prefix="/api/citations", tags=["Citations"])
app.include_router(timelines.router, prefix="/api/timelines", tags=["Timelines"])
app.include_router(judgments.router, prefix="/api/judgments", tags=["Judgments"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])


@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "message": "Veritus Legal Intelligence API",
        "status": "healthy",
        "version": "1.0.0",
        "description": "AI-powered legal research platform for Supreme Court judgments"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "database": "connected",
            "redis": "connected",
            "openai": "configured" if settings.OPENAI_API_KEY else "not_configured",
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
