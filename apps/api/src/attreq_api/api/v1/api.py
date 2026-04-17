"""API v1 router aggregation."""

from fastapi import APIRouter

from attreq_api.api.v1.endpoints import auth, outfits, recommendations, users, wardrobe

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include user management routes
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Include wardrobe management routes
api_router.include_router(wardrobe.router, prefix="/wardrobe", tags=["wardrobe"])

# Include outfit management routes
api_router.include_router(outfits.router, prefix="/outfits", tags=["outfits"])

# Include recommendation routes
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["recommendations"]
)
