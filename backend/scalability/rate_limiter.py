"""
Rate Limiting for API Protection
Uses slowapi with Redis or in-memory storage
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from config import settings


def get_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting
    Tries to get session_id from body, falls back to IP
    """
    # Try to get session from query params or headers
    session_id = request.headers.get("X-Session-ID")
    if session_id:
        return f"session:{session_id}"
    
    # Fallback to IP address
    return get_remote_address(request)


# Configure limiter
limiter = Limiter(
    key_func=get_identifier,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL if settings.REDIS_ENABLED else None
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please wait before trying again.",
            "retry_after": exc.detail
        }
    )


# Rate limit decorators for different endpoints
def chat_rate_limit():
    """Rate limit for chat endpoint (more restrictive)"""
    return limiter.limit("20/minute")


def products_rate_limit():
    """Rate limit for products endpoint (less restrictive)"""
    return limiter.limit("60/minute")


def search_rate_limit():
    """Rate limit for search endpoint"""
    return limiter.limit("30/minute")
