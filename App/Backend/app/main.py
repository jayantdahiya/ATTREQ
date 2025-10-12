"""Main FastAPI application for ATTREQ backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.services.ai.embeddings import weaviate_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()

    # Initialize Weaviate schema if connected
    if weaviate_service.is_connected():
        weaviate_service.init_schema()

    yield

    # Shutdown
    await close_db()
    weaviate_service.close()


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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
if settings.app_env == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["attreq.com", "*.attreq.com"])

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

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.app_debug)
