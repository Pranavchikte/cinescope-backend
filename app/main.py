import logging
import time
import asyncio
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.database import get_db
from app.api.v1 import api_router

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CineScope API",
    description="Movie and TV tracking platform",
    version="1.0.0"
)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("="*50)
    logger.info("CineScope API Starting...")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"CORS Origins: {settings.ALLOWED_ORIGINS}")
    logger.info("="*50)
    # Warm up vector store/model to reduce first chat latency
    try:
        from app.services.vector_store import vector_store
        await asyncio.to_thread(vector_store.search, "warmup", 1)
        logger.info("Chat warmup complete")
    except Exception as e:
        logger.warning(f"Chat warmup failed: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("CineScope API Shutting Down...")

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"Response: {request.method} {request.url.path} Status: {response.status_code} Duration: {duration:.3f}s")
    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "CineScope API is running"}

@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "checks": {
            "api": "ok",
            "database": "unknown",
            "redis": "unknown"
        }
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"
    
    # Check Redis
    try:
        from app.services.cache import cache_service
        cache_service.redis_client.ping()
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = f"error: {str(e)}"
    
    return health_status
