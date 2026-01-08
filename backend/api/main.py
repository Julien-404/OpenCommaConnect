from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import redis
import logging
from sqlalchemy import text

from database import engine, get_db
from routers import auth, devices, routes, upload, maps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Comma Connect API",
    description="Self-hosted Comma Connect server for openpilot",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(routes.router, prefix="/api/v1/routes", tags=["Routes"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])
app.include_router(maps.router, prefix="/api/v1/maps", tags=["Maps"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Comma Connect API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "unknown",
        "redis": "unknown"
    }

    # Check database
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status["database"] = "disconnected"
        status["status"] = "unhealthy"

    # Check Redis
    try:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        status["redis"] = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        status["redis"] = "disconnected"
        status["status"] = "degraded"

    return status

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
