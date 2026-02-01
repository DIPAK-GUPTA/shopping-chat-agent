"""
Shopping Chat Agent - FastAPI Backend
Main application entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from config import settings
from routes import chat_router, products_router
from scalability.rate_limiter import limiter, rate_limit_exceeded_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📱 Phone catalog loaded")
    print(f"🤖 AI Agent initialized (Gemini: {settings.GEMINI_MODEL})")
    
    if settings.REDIS_ENABLED:
        print(f"📦 Redis caching enabled: {settings.REDIS_URL}")
    else:
        print("📦 Using in-memory caching")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered shopping assistant for mobile phones",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiter state
app.state.limiter = limiter

# Add rate limit error handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI Shopping Chat Agent for Mobile Phones",
        "endpoints": {
            "chat": "/api/chat",
            "products": "/api/products",
            "docs": "/docs"
        }
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ai_enabled": bool(settings.GEMINI_API_KEY),
        "redis_enabled": settings.REDIS_ENABLED
    }


# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(products_router, prefix="/api")


# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    print(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred. Please try again."
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
