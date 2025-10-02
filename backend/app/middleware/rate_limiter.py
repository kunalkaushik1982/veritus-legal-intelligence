"""
Rate limiting middleware
File: backend/app/middleware/rate_limiter.py
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from typing import Dict, Tuple
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent API abuse"""
    
    def __init__(self, app, requests_per_window: int = None, window_seconds: int = None):
        super().__init__(app)
        self.requests_per_window = requests_per_window or settings.RATE_LIMIT_REQUESTS
        self.window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW
        self.requests: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        client_ip = self._get_client_ip(request)
        
        # Clean old requests
        self._clean_old_requests(client_ip)
        
        # Check rate limit
        if self._is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Record this request
        self._record_request(client_ip)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_window - len(self.requests.get(client_ip, []))
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded IP first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def _clean_old_requests(self, client_ip: str):
        """Remove requests older than the window"""
        current_time = time.time()
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < self.window_seconds
            ]
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited"""
        if client_ip not in self.requests:
            return False
        
        return len(self.requests[client_ip]) >= self.requests_per_window
    
    def _record_request(self, client_ip: str):
        """Record a request for the client"""
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        self.requests[client_ip].append(time.time())
