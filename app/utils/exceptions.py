"""
Custom exceptions for LinkedIn Presence Automation Application.

Defines application-specific exceptions with proper error codes
and messages for consistent error handling.
"""

from typing import Optional, Dict, Any


class LinkedInAutomationError(Exception):
    """Base exception for LinkedIn Automation application."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base exception.
        
        Args:
            message: Error message
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


class ContentNotFoundError(LinkedInAutomationError):
    """Exception raised when requested content is not found."""
    
    def __init__(self, message: str = "Content not found", **kwargs):
        super().__init__(message, error_code="CONTENT_NOT_FOUND", **kwargs)


class InvalidCredentialsError(LinkedInAutomationError):
    """Exception raised when authentication credentials are invalid."""
    
    def __init__(self, message: str = "Invalid credentials", **kwargs):
        super().__init__(message, error_code="INVALID_CREDENTIALS", **kwargs)


class RateLimitExceededError(LinkedInAutomationError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, error_code="RATE_LIMIT_EXCEEDED", **kwargs)
        self.retry_after = retry_after


class ValidationError(LinkedInAutomationError):
    """Exception raised when data validation fails."""
    
    def __init__(
        self,
        message: str = "Validation error",
        field_errors: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field_errors = field_errors or {}


class AuthenticationError(LinkedInAutomationError):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)


class AuthorizationError(LinkedInAutomationError):
    """Exception raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(message, error_code="AUTHORIZATION_ERROR", **kwargs)


class ContentProcessingError(LinkedInAutomationError):
    """Exception raised when content processing fails."""
    
    def __init__(self, message: str = "Content processing failed", **kwargs):
        super().__init__(message, error_code="CONTENT_PROCESSING_ERROR", **kwargs)


class AIServiceError(LinkedInAutomationError):
    """Exception raised when AI service operations fail."""
    
    def __init__(self, message: str = "AI service error", **kwargs):
        super().__init__(message, error_code="AI_SERVICE_ERROR", **kwargs)


class DatabaseError(LinkedInAutomationError):
    """Exception raised when database operations fail."""
    
    def __init__(self, message: str = "Database error", **kwargs):
        super().__init__(message, error_code="DATABASE_ERROR", **kwargs)


class ExternalServiceError(LinkedInAutomationError):
    """Exception raised when external service calls fail."""
    
    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="EXTERNAL_SERVICE_ERROR", **kwargs)
        self.service_name = service_name


class ConfigurationError(LinkedInAutomationError):
    """Exception raised when configuration is invalid."""
    
    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)


class BusinessLogicError(LinkedInAutomationError):
    """Exception raised when business logic validation fails."""
    
    def __init__(self, message: str = "Business logic error", **kwargs):
        super().__init__(message, error_code="BUSINESS_LOGIC_ERROR", **kwargs)


class ResourceConflictError(LinkedInAutomationError):
    """Exception raised when resource conflicts occur."""
    
    def __init__(self, message: str = "Resource conflict", **kwargs):
        super().__init__(message, error_code="RESOURCE_CONFLICT", **kwargs)


class ServiceUnavailableError(LinkedInAutomationError):
    """Exception raised when service is temporarily unavailable."""
    
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, error_code="SERVICE_UNAVAILABLE", **kwargs)
        self.retry_after = retry_after


class QuotaExceededError(LinkedInAutomationError):
    """Exception raised when usage quota is exceeded."""
    
    def __init__(
        self,
        message: str = "Usage quota exceeded",
        quota_type: Optional[str] = None,
        reset_time: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="QUOTA_EXCEEDED", **kwargs)
        self.quota_type = quota_type
        self.reset_time = reset_time


class DataIntegrityError(LinkedInAutomationError):
    """Exception raised when data integrity constraints are violated."""
    
    def __init__(self, message: str = "Data integrity error", **kwargs):
        super().__init__(message, error_code="DATA_INTEGRITY_ERROR", **kwargs)


class TimeoutError(LinkedInAutomationError):
    """Exception raised when operations timeout."""
    
    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_seconds: Optional[float] = None,
        **kwargs
    ):
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)
        self.timeout_seconds = timeout_seconds


class FeatureNotAvailableError(LinkedInAutomationError):
    """Exception raised when requested feature is not available."""
    
    def __init__(
        self,
        message: str = "Feature not available",
        feature_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="FEATURE_NOT_AVAILABLE", **kwargs)
        self.feature_name = feature_name


class MaintenanceModeError(LinkedInAutomationError):
    """Exception raised when system is in maintenance mode."""
    
    def __init__(
        self,
        message: str = "System is under maintenance",
        estimated_completion: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="MAINTENANCE_MODE", **kwargs)
        self.estimated_completion = estimated_completion


# Exception mapping for HTTP status codes
EXCEPTION_STATUS_MAP = {
    ContentNotFoundError: 404,
    InvalidCredentialsError: 401,
    AuthenticationError: 401,
    AuthorizationError: 403,
    ValidationError: 422,
    RateLimitExceededError: 429,
    ResourceConflictError: 409,
    QuotaExceededError: 429,
    ServiceUnavailableError: 503,
    MaintenanceModeError: 503,
    TimeoutError: 408,
    FeatureNotAvailableError: 501,
    BusinessLogicError: 400,
    DataIntegrityError: 400,
    ConfigurationError: 500,
    DatabaseError: 500,
    AIServiceError: 500,
    ExternalServiceError: 502,
    LinkedInAutomationError: 500,
}


def get_http_status_code(exception: Exception) -> int:
    """
    Get HTTP status code for exception.
    
    Args:
        exception: Exception instance
        
    Returns:
        HTTP status code
    """
    return EXCEPTION_STATUS_MAP.get(type(exception), 500)


def format_error_response(exception: LinkedInAutomationError) -> dict:
    """
    Format exception as error response dictionary.
    
    Args:
        exception: LinkedIn automation exception
        
    Returns:
        Error response dictionary
    """
    response = {
        "error": exception.error_code,
        "message": exception.message,
    }
    
    if exception.details:
        response["details"] = exception.details
    
    # Add specific fields for certain exception types
    if isinstance(exception, RateLimitExceededError) and exception.retry_after:
        response["retry_after"] = exception.retry_after
    
    if isinstance(exception, ValidationError) and exception.field_errors:
        response["field_errors"] = exception.field_errors
    
    if isinstance(exception, ExternalServiceError) and exception.service_name:
        response["service"] = exception.service_name
    
    if isinstance(exception, QuotaExceededError):
        if exception.quota_type:
            response["quota_type"] = exception.quota_type
        if exception.reset_time:
            response["reset_time"] = exception.reset_time
    
    if isinstance(exception, TimeoutError) and exception.timeout_seconds:
        response["timeout_seconds"] = exception.timeout_seconds
    
    if isinstance(exception, FeatureNotAvailableError) and exception.feature_name:
        response["feature"] = exception.feature_name
    
    if isinstance(exception, MaintenanceModeError) and exception.estimated_completion:
        response["estimated_completion"] = exception.estimated_completion
    
    return response