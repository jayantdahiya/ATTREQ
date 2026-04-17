"""Main FastAPI application for ATTREQ backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from attreq_api.api.v1.api import api_router
from attreq_api.config.database import close_db, init_db
from attreq_api.config.settings import settings
from attreq_api.services.ai.embeddings import weaviate_service
from attreq_api.services.cache.redis_client import redis_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()

    # Initialize Weaviate schema if connected
    if weaviate_service.is_connected():
        weaviate_service.init_schema()

    # Check Redis connection
    if await redis_cache.is_connected():
        logging.getLogger(__name__).info("Redis cache connected successfully")

    yield

    # Shutdown
    await close_db()
    weaviate_service.close()
    await redis_cache.close()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered personal stylist API for wardrobe management and outfit recommendations",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
if settings.app_env == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

# Mount static files directory for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to ATTREQ API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app_name": settings.app_name, "environment": settings.app_env}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("attreq_api.main:app", host="0.0.0.0", port=8000, reload=settings.app_debug)
