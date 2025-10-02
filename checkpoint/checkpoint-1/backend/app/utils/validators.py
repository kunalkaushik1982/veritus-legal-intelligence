"""
Utility functions for validation and common operations
File: backend/app/utils/validators.py
"""

import re
from typing import Optional


def validate_query_length(query: str) -> bool:
    """Validate query length for chatbot"""
    return 10 <= len(query.strip()) <= 1000


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False
    
    return True


def validate_case_number(case_number: str) -> bool:
    """Validate Supreme Court case number format"""
    pattern = r'^(Civil|Criminal|Writ|Special Leave|Appeal)\s+(Appeal|Petition|Application)?\s*(No\.?\s*)?\d+[A-Z]?/\d{4}$'
    return re.match(pattern, case_number, re.IGNORECASE) is not None


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()


def extract_year_from_date(date_str: str) -> Optional[int]:
    """Extract year from various date formats"""
    # Try to find 4-digit year
    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if year_match:
        return int(year_match.group())
    
    return None
