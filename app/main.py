"""
FastAPI main application for LinkedIn Presence Automation Application.

Main FastAPI application with middleware configuration, route registration,
and application lifecycle management.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
import os
from datetime import datetime

from app.api.v1.router import api_router
from app.core.middleware import (
    RateLimitMiddleware, 
    RequestLoggingMiddleware, 
    SecurityHeadersMiddleware
)
# from app.core.config import get_settings
from app.core.security import get_current_user
from app.database.connection import init_database, close_database, run_migrations
from app.api.v1.router import api_router
from app.utils.exceptions import (
    get_http_status_code, 
    format_error_response,
    ContentNotFoundError,
    InvalidCredentialsError,
    ValidationError,
    RateLimitExceededError,
    LinkedInAutomationError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting LinkedIn Automation Application...")
    try:
        logger.info("Initializing database connection...")
        await init_database() # This just initializes db_manager
        # No need to call run_migrations() here if entrypoint.sh does it
        logger.info("Application startup completed successfully (migrations handled by entrypoint).")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise
    
    yield
    
    logger.info("Shutting down application...")
    await close_database()
    logger.info("Application shutdown completed")
    
# Create FastAPI application
app = FastAPI(
    title="LinkedIn Presence Automation API",
    description="Automated LinkedIn content creation and posting system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
)

# Add custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(ContentNotFoundError)
async def content_not_found_handler(request: Request, exc: ContentNotFoundError):
    """Handle content not found errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Content Not Found",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    """Handle invalid credentials errors."""
    return JSONResponse(
        status_code=401,
        content={
            "error": "Invalid Credentials",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(RateLimitExceededError)
async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate Limit Exceeded",
            "message": str(exc),
            "retry_after": 60,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Request Validation Error",
            "message": "Invalid request data",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(LinkedInAutomationError)
async def automation_exception_handler(request: Request, exc: LinkedInAutomationError):
    """Handle custom LinkedIn automation exceptions."""
    status_code = get_http_status_code(exc)
    error_response = format_error_response(exc)
    
    logger.error(f"Application error: {exc.message} - {exc.error_code}")
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "DATABASE_ERROR",
            "message": "A database error occurred"
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "LinkedIn Automation API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "False").lower() == "true",
        workers=int(os.getenv("WORKERS", "1")),
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )