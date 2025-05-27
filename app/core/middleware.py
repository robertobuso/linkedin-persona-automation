"""
Custom middleware for LinkedIn Presence Automation Application.

Provides rate limiting, request logging, security headers,
and other middleware functionality.
"""

import time
import logging
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import redis
import os
from datetime import datetime, timedelta

from app.utils.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)

# Redis connection for rate limiting
redis_client = None
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis connection failed: {str(e)}. Rate limiting will use in-memory storage.")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.
    
    Implements per-user and per-IP rate limiting with configurable
    limits and time windows.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        calls: int = 100,
        period: int = 60,
        per_user: bool = True
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: ASGI application
            calls: Number of calls allowed per period
            period: Time period in seconds
            per_user: Whether to apply limits per user or per IP
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.per_user = per_user
        self.memory_store: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response
        """
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get identifier for rate limiting
        identifier = await self._get_identifier(request)
        
        # Check rate limit
        if not await self._check_rate_limit(identifier):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate Limit Exceeded",
                    "message": f"Too many requests. Limit: {self.calls} per {self.period} seconds",
                    "retry_after": self.period,
                    "timestamp": datetime.utcnow().isoformat()
                },
                headers={"Retry-After": str(self.period)}
            )
        
        # Record the request
        await self._record_request(identifier)
        
        return await call_next(request)
    
    async def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting."""
        if self.per_user:
            # Try to get user ID from token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    from app.core.security import verify_token
                    token = auth_header.split(" ")[1]
                    payload = verify_token(token)
                    user_id = payload.get("sub")
                    if user_id:
                        return f"user:{user_id}"
                except Exception:
                    pass
        
        # Fall back to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit."""
        current_time = time.time()
        
        if redis_client:
            return await self._check_rate_limit_redis(identifier, current_time)
        else:
            return self._check_rate_limit_memory(identifier, current_time)
    
    async def _check_rate_limit_redis(self, identifier: str, current_time: float) -> bool:
        """Check rate limit using Redis."""
        try:
            key = f"rate_limit:{identifier}"
            
            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time - self.period)
            pipe.zcard(key)
            pipe.expire(key, self.period)
            
            results = pipe.execute()
            current_requests = results[1]
            
            return current_requests < self.calls
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {str(e)}")
            return True  # Allow request if Redis fails
    
    def _check_rate_limit_memory(self, identifier: str, current_time: float) -> bool:
        """Check rate limit using in-memory storage."""
        if identifier not in self.memory_store:
            self.memory_store[identifier] = []
        
        # Remove old requests
        self.memory_store[identifier] = [
            req_time for req_time in self.memory_store[identifier]
            if req_time > current_time - self.period
        ]
        
        return len(self.memory_store[identifier]) < self.calls
    
    async def _record_request(self, identifier: str) -> None:
        """Record the current request."""
        current_time = time.time()
        
        if redis_client:
            try:
                key = f"rate_limit:{identifier}"
                redis_client.zadd(key, {str(current_time): current_time})
                redis_client.expire(key, self.period)
            except Exception as e:
                logger.error(f"Redis request recording failed: {str(e)}")
        else:
            if identifier not in self.memory_store:
                self.memory_store[identifier] = []
            self.memory_store[identifier].append(current_time)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware with correlation IDs and performance tracking.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with logging.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started - {request.method} {request.url.path} "
            f"[{correlation_id}] from {request.client.host}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed - {request.method} {request.url.path} "
                f"[{correlation_id}] {response.status_code} in {duration:.3f}s"
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed - {request.method} {request.url.path} "
                f"[{correlation_id}] {str(e)} in {duration:.3f}s"
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware for adding security-related HTTP headers.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Cache control middleware for setting appropriate cache headers.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Define cache policies for different endpoints
        self.cache_policies = {
            "/api/v1/analytics/dashboard": "private, max-age=300",  # 5 minutes
            "/api/v1/content/feed": "private, max-age=600",  # 10 minutes
            "/api/v1/drafts": "private, no-cache",  # No cache
            "/api/v1/auth": "private, no-cache, no-store",  # No cache for auth
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add cache headers.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response with cache headers
        """
        response = await call_next(request)
        
        # Set cache policy based on path
        path = request.url.path
        
        # Find matching cache policy
        cache_control = "private, no-cache"  # Default
        for pattern, policy in self.cache_policies.items():
            if path.startswith(pattern):
                cache_control = policy
                break
        
        response.headers["Cache-Control"] = cache_control
        
        # Add ETag for GET requests
        if request.method == "GET" and response.status_code == 200:
            import hashlib
            content_hash = hashlib.md5(str(response.body).encode()).hexdigest()
            response.headers["ETag"] = f'"{content_hash}"'
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Response compression middleware for reducing bandwidth usage.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and compress response if appropriate.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response (potentially compressed)
        """
        response = await call_next(request)
        
        # Check if client accepts compression
        accept_encoding = request.headers.get("Accept-Encoding", "")
        
        # Only compress JSON responses larger than 1KB
        if (
            "gzip" in accept_encoding and
            response.headers.get("Content-Type", "").startswith("application/json") and
            hasattr(response, "body") and
            len(response.body) > 1024
        ):
            import gzip
            
            # Compress response body
            compressed_body = gzip.compress(response.body)
            
            # Update response
            response.body = compressed_body
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Content-Length"] = str(len(compressed_body))
        
        return response