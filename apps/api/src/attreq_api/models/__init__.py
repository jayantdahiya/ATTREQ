"""Models package."""

from attreq_api.models.outfit import Outfit
from attreq_api.models.recommendation_event import RecommendationEvent
from attreq_api.models.scoring_weights import ScoringWeights
from attreq_api.models.style_dna import StyleDnaPhoto
from attreq_api.models.user import User
from attreq_api.models.user_event import UserEvent
from attreq_api.models.wardrobe import WardrobeItem
from attreq_api.models.wardrobe_photo import WardrobeItemPhoto

__all__ = [
    "User",
    "WardrobeItem",
    "Outfit",
    "StyleDnaPhoto",
    "WardrobeItemPhoto",
    "RecommendationEvent",
    "UserEvent",
    "ScoringWeights",
]
