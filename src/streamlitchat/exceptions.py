"""Custom exceptions for StreamlitChat."""
from typing import Optional

class ChatError(Exception):
    """Base exception for StreamlitChat errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        """Initialize with message and optional details.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.details = details or {}

class APIError(ChatError):
    """Exception for API-related errors."""
    pass

class ValidationError(ChatError):
    """Exception for input validation errors."""
    pass 