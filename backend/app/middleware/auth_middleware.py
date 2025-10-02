"""
Authentication middleware
File: backend/app/middleware/auth_middleware.py
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for protected routes"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Routes that don't require authentication
        self.public_routes = {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/register",
            "/api/auth/login"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with authentication check"""
        # Skip auth for public routes
        if request.url.path in self.public_routes:
            return await call_next(request)
        
        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Check for Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate token format
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Process request
        response = await call_next(request)
        return response
