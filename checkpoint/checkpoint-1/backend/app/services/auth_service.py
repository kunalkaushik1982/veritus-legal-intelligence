"""
Authentication service for user management
File: backend/app/services/auth_service.py
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.models.user import User, UserRole
from app.database import get_db

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication and user management service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(
        self,
        email: str,
        username: str,
        full_name: str,
        password: str,
        bar_council_number: Optional[str] = None,
        practice_area: Optional[str] = None
    ) -> User:
        """Create a new user account"""
        hashed_password = self._get_password_hash(password)
        
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            bar_council_number=bar_council_number,
            practice_area=practice_area,
            role=UserRole.FREE,
            subscription_tier=UserRole.FREE
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password"""
        # Try to find user by email or username
        user = self.get_user_by_email(username) or self.get_user_by_username(username)
        
        if not user:
            return None
        
        if not self._verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    def create_access_token(self, user_id: int) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[int]:
        """Verify JWT token and return user ID"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            
            if user_id is None:
                return None
            
            return int(user_id)
            
        except jwt.PyJWTError:
            return None
    
    def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> User:
        """Get current authenticated user"""
        token = credentials.credentials
        user_id = self.verify_token(token)
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = self.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        user = self.get_user_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
    
    def check_query_limit(self, user_id: int) -> bool:
        """Check if user has exceeded daily query limit"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Reset daily count if it's a new day
        today = datetime.utcnow().date()
        if user.last_query_date != today:
            user.queries_today = 0
            user.last_query_date = today
            self.db.commit()
        
        # Check limits based on subscription tier
        if user.subscription_tier == UserRole.FREE:
            return user.queries_today < settings.FREE_TIER_QUERIES_PER_DAY
        else:
            return user.queries_today < settings.PRO_TIER_QUERIES_PER_DAY
    
    def increment_query_count(self, user_id: int):
        """Increment user's query count"""
        user = self.get_user_by_id(user_id)
        if user:
            user.queries_today += 1
            user.total_queries += 1
            user.last_query_date = datetime.utcnow().date()
            self.db.commit()
    
    def update_profile(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        practice_area: Optional[str] = None,
        bio: Optional[str] = None
    ) -> User:
        """Update user profile information"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if full_name is not None:
            user.full_name = full_name
        if practice_area is not None:
            user.practice_area = practice_area
        if bio is not None:
            user.bio = bio
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def _get_password_hash(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
