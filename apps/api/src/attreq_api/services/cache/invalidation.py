"""Shared cache-invalidation helpers.

Extracted so that every place an item's eligibility for "Today" changes
(archive/unarchive, hard delete, the existing manual-refresh endpoint) goes
through the same invalidation path instead of re-implementing the
occasion-key loop.
"""

import logging
from datetime import date
from uuid import UUID

from attreq_api.services.cache.redis_client import redis_cache

logger = logging.getLogger(__name__)

# Must match the occasion set the daily-suggestions endpoint accepts.
DAILY_SUGGESTION_OCCASIONS = ["casual", "formal", "party", "business", "athletic"]


async def invalidate_daily_suggestions(user_id: UUID) -> int:
    """Delete today's cached daily-suggestions entries for every occasion.

    Archiving/unarchiving/deleting a wardrobe item must remove it from
    "Today" immediately rather than waiting out the 24h TTL — this is the
    fix for RI-7 finding A.

    Returns the number of keys actually deleted.
    """
    today = date.today().isoformat()
    cleared_count = 0

    for occasion in DAILY_SUGGESTION_OCCASIONS:
        # v2: RI-4 changed the cached payload shape (fullbody/footwear/
        # outerwear slots, explanation/confidence/rediscovery) — must match
        # the key the daily-suggestions endpoint writes/reads (see that
        # module's docstring on why the version bump exists).
        cache_key = f"daily_suggestions:v2:{user_id}:{today}:{occasion}"
        if await redis_cache.delete(cache_key):
            cleared_count += 1

    logger.info(f"Invalidated {cleared_count} daily-suggestion cache entries for user {user_id}")
    return cleared_count
