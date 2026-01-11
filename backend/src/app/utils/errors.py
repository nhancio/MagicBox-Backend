"""
Custom exception classes and error handling utilities.
"""
from typing import Optional, Dict, Any
import traceback
from fastapi import HTTPException, status


class MagicBoxError(Exception):
    """Base exception for all MagicBox application errors."""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code or "GENERIC_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(MagicBoxError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)
        self.field = field


class NotFoundError(MagicBoxError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: Optional[str] = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(message, code="NOT_FOUND", details={"resource_type": resource_type, "resource_id": resource_id})


class UnauthorizedError(MagicBoxError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, code="UNAUTHORIZED")


class ForbiddenError(MagicBoxError):
    """Raised when user lacks permission."""
    
    def __init__(self, message: str = "Forbidden", action: Optional[str] = None):
        super().__init__(message, code="FORBIDDEN", details={"action": action})


class ConflictError(MagicBoxError):
    """Raised when a resource conflict occurs."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None):
        super().__init__(message, code="CONFLICT", details={"resource_type": resource_type})


class RateLimitError(MagicBoxError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message, code="RATE_LIMIT", details={"retry_after": retry_after})


class ExternalServiceError(MagicBoxError):
    """Raised when an external service call fails."""
    
    def __init__(self, service: str, message: str, status_code: Optional[int] = None):
        super().__init__(message, code="EXTERNAL_SERVICE_ERROR", details={"service": service, "status_code": status_code})
        self.service = service
        self.status_code = status_code


class AIError(MagicBoxError):
    """Raised when AI service operations fail."""
    
    def __init__(self, message: str, model: Optional[str] = None):
        super().__init__(message, code="AI_ERROR", details={"model": model})
        self.model = model


class DatabaseError(MagicBoxError):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(message, code="DATABASE_ERROR", details={"operation": operation})


def error_to_http_exception(error: MagicBoxError) -> HTTPException:
    """Convert MagicBoxError to FastAPI HTTPException."""
    status_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "RATE_LIMIT": status.HTTP_429_TOO_MANY_REQUESTS,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY,
        "AI_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "GENERIC_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    status_code = status_map.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error": error.code,
            "message": error.message,
            "details": error.details,
        }
    )


def format_exception(exc: Exception) -> Dict[str, Any]:
    """Format exception for logging/error reporting."""
    return {
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(),
    }