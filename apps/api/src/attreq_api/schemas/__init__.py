"""Schemas package."""

from attreq_api.schemas.outfit import (
    OutfitCreate,
    OutfitFeedback,
    OutfitList,
    OutfitResponse,
    OutfitWear,
    OutfitWithItems,
)
from attreq_api.schemas.recommendation import (
    DailySuggestionRequest,
    DailySuggestionsResponse,
    OutfitSuggestion,
    WeatherData,
)
from attreq_api.schemas.token import Token, TokenPayload
from attreq_api.schemas.user import (
    PasswordChange,
    UserCreate,
    UserProfile,
    UserResponse,
    UserUpdate,
)
from attreq_api.schemas.wardrobe import (
    WardrobeItemCreate,
    WardrobeItemList,
    WardrobeItemResponse,
    WardrobeItemUpdate,
    WardrobeItemUploadResponse,
)

__all__ = [
    "Token",
    "TokenPayload",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
    "PasswordChange",
    "WardrobeItemCreate",
    "WardrobeItemUpdate",
    "WardrobeItemResponse",
    "WardrobeItemList",
    "WardrobeItemUploadResponse",
    "OutfitCreate",
    "OutfitResponse",
    "OutfitWithItems",
    "OutfitFeedback",
    "OutfitWear",
    "OutfitList",
    "WeatherData",
    "OutfitSuggestion",
    "DailySuggestionRequest",
    "DailySuggestionsResponse",
]
