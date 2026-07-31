"""Weaviate embeddings service for vector search."""

import logging
from typing import Any
from uuid import UUID

import weaviate
from weaviate.classes.config import Configure, DataType, Property, VectorDistances

from attreq_api.config.settings import settings

logger = logging.getLogger(__name__)

# RI-6: second collection for raw FashionCLIP image vectors. Kept separate
# from `ClothingItem` (which auto-vectorizes a text `description` via
# text2vec-transformers) rather than retrofitting it — attaching a manual
# 512-d vector to that collection's default slot would require either named
# vectors (a collection recreation) or disabling auto-vectorization (breaking
# `search_similar_items`/`find_compatible_items`). `vectorizer_config=none()`
# here: every vector is supplied by the caller (FashionCLIP output), never
# computed by Weaviate.
VECTOR_COLLECTION_NAME = "ClothingItemVector"


class WeaviateEmbeddingsService:
    """Service for managing clothing item embeddings in Weaviate."""

    def __init__(self):
        """Initialize Weaviate client."""
        self.client = None
        self.collection_name = "ClothingItem"
        self._connect()

    def _connect(self) -> None:
        """Connect to Weaviate instance."""
        try:
            # Create Weaviate client
            self.client = weaviate.connect_to_local(
                host=settings.weaviate_host,
                port=settings.weaviate_port,
            )
            logger.info(
                f"Connected to Weaviate at {settings.weaviate_host}:{settings.weaviate_port}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {str(e)}")
            self.client = None

    def is_connected(self) -> bool:
        """Check if Weaviate client is connected.

        Returns:
            True if connected, False otherwise
        """
        return self.client is not None and self.client.is_ready()

    def init_schema(self) -> bool:
        """Initialize Weaviate schema for clothing items.

        Returns:
            True if schema initialized successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot initialize schema: Not connected to Weaviate")
            return False

        try:
            # Check if collection already exists
            if self.client.collections.exists(self.collection_name):
                logger.info(f"Collection '{self.collection_name}' already exists")
                return True

            # Create collection with schema
            self.client.collections.create(
                name=self.collection_name,
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
                properties=[
                    Property(name="itemId", data_type=DataType.TEXT),
                    Property(name="userId", data_type=DataType.TEXT),
                    Property(name="category", data_type=DataType.TEXT),
                    Property(name="colorPrimary", data_type=DataType.TEXT),
                    Property(name="colorSecondary", data_type=DataType.TEXT),
                    Property(name="pattern", data_type=DataType.TEXT),
                    Property(name="season", data_type=DataType.TEXT_ARRAY),
                    Property(name="occasion", data_type=DataType.TEXT_ARRAY),
                    Property(name="description", data_type=DataType.TEXT),
                ],
            )

            logger.info(f"Collection '{self.collection_name}' created successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize schema: {str(e)}")
            return False

    def add_item(
        self,
        item_id: UUID,
        user_id: UUID,
        category: str | None = None,
        color_primary: str | None = None,
        color_secondary: str | None = None,
        pattern: str | None = None,
        season: list[str] | None = None,
        occasion: list[str] | None = None,
    ) -> bool:
        """Add a clothing item to Weaviate.

        Args:
            item_id: UUID of the wardrobe item
            user_id: UUID of the user
            category: Clothing category
            color_primary: Primary color
            color_secondary: Secondary color
            pattern: Pattern type
            season: List of suitable seasons
            occasion: List of suitable occasions

        Returns:
            True if item added successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot add item: Not connected to Weaviate")
            return False

        try:
            # Build description for vectorization
            description_parts = []
            if category:
                description_parts.append(category)
            if color_primary:
                description_parts.append(f"{color_primary} color")
            if color_secondary:
                description_parts.append(f"with {color_secondary} accents")
            if pattern:
                description_parts.append(pattern)
            if season:
                description_parts.append(f"for {', '.join(season)}")
            if occasion:
                description_parts.append(f"suitable for {', '.join(occasion)}")

            description = " ".join(description_parts) if description_parts else "clothing item"

            # Get collection
            collection = self.client.collections.get(self.collection_name)

            # Add item
            collection.data.insert(
                properties={
                    "itemId": str(item_id),
                    "userId": str(user_id),
                    "category": category or "",
                    "colorPrimary": color_primary or "",
                    "colorSecondary": color_secondary or "",
                    "pattern": pattern or "",
                    "season": season or [],
                    "occasion": occasion or [],
                    "description": description,
                }
            )

            logger.info(f"Added item {item_id} to Weaviate")
            return True

        except Exception as e:
            logger.error(f"Failed to add item to Weaviate: {str(e)}")
            return False

    def search_similar_items(
        self,
        query: str,
        user_id: UUID,
        limit: int = 10,
        category_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar clothing items using hybrid search.

        Args:
            query: Search query (e.g., "blue shirt for formal occasions")
            user_id: UUID of the user
            limit: Maximum number of results to return
            category_filter: Optional category filter

        Returns:
            List of matching items with their properties
        """
        if not self.is_connected():
            logger.error("Cannot search: Not connected to Weaviate")
            return []

        try:
            # Get collection
            collection = self.client.collections.get(self.collection_name)

            # Build where filter
            where_filter = weaviate.classes.query.Filter.by_property("userId").equal(str(user_id))

            if category_filter:
                where_filter = where_filter & weaviate.classes.query.Filter.by_property(
                    "category"
                ).equal(category_filter)

            # Perform hybrid search
            response = collection.query.hybrid(
                query=query,
                limit=limit,
                where=where_filter,
            )

            # Parse results
            results = []
            for item in response.objects:
                results.append(
                    {
                        "item_id": item.properties.get("itemId"),
                        "category": item.properties.get("category"),
                        "color_primary": item.properties.get("colorPrimary"),
                        "color_secondary": item.properties.get("colorSecondary"),
                        "pattern": item.properties.get("pattern"),
                        "season": item.properties.get("season"),
                        "occasion": item.properties.get("occasion"),
                        "description": item.properties.get("description"),
                    }
                )

            logger.info(f"Found {len(results)} similar items for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Failed to search items: {str(e)}")
            return []

    def delete_item(self, item_id: UUID) -> bool:
        """Delete a clothing item from Weaviate.

        Args:
            item_id: UUID of the wardrobe item

        Returns:
            True if item deleted successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot delete item: Not connected to Weaviate")
            return False

        try:
            # Get collection
            collection = self.client.collections.get(self.collection_name)

            # Find and delete items matching the itemId
            where_filter = weaviate.classes.query.Filter.by_property("itemId").equal(str(item_id))

            # Delete matching items
            collection.data.delete_many(where=where_filter)

            logger.info(f"Deleted item {item_id} from Weaviate")
            return True

        except Exception as e:
            logger.error(f"Failed to delete item from Weaviate: {str(e)}")
            return False

    def close(self) -> None:
        """Close Weaviate client connection."""
        if self.client:
            self.client.close()
            logger.info("Weaviate connection closed")

    # ------------------------------------------------------------------
    # RI-6: ClothingItemVector — raw FashionCLIP vectors, manual (vectorizer
    # `none`) collection. See module-level `VECTOR_COLLECTION_NAME` docstring
    # for why this is a second collection rather than a retrofit of
    # `ClothingItem`. Every method here follows the same soft-fail contract
    # as the rest of this class: return `False`/`None`/`[]` on any error,
    # never raise.
    # ------------------------------------------------------------------

    def init_vector_schema(self) -> bool:
        """Create the `ClothingItemVector` collection if it doesn't exist yet."""
        if not self.is_connected():
            logger.error("Cannot initialize vector schema: Not connected to Weaviate")
            return False

        try:
            if self.client.collections.exists(VECTOR_COLLECTION_NAME):
                return True

            self.client.collections.create(
                name=VECTOR_COLLECTION_NAME,
                vectorizer_config=Configure.Vectorizer.none(),
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE
                ),
                properties=[
                    Property(name="itemId", data_type=DataType.TEXT),
                    Property(name="userId", data_type=DataType.TEXT),
                    Property(name="category", data_type=DataType.TEXT),
                    # Forward hook for RI-2's fixed vocabulary; not enforced here.
                    Property(name="schemaVersion", data_type=DataType.INT),
                ],
            )
            logger.info(f"Collection '{VECTOR_COLLECTION_NAME}' created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize vector schema: {str(e)}")
            return False

    def upsert_vector(
        self,
        item_id: UUID,
        user_id: UUID,
        category: str | None,
        vector: list[float],
    ) -> bool:
        """Idempotent upsert: delete any existing row for `item_id`, then insert.

        Weaviate v4's client has no native upsert-by-property, so this
        mirrors the delete-then-insert pattern `delete_item`/`add_item`
        already use for the `ClothingItem` collection.
        """
        if not self.is_connected():
            logger.error("Cannot upsert vector: Not connected to Weaviate")
            return False

        try:
            collection = self.client.collections.get(VECTOR_COLLECTION_NAME)
            where_filter = weaviate.classes.query.Filter.by_property("itemId").equal(str(item_id))
            collection.data.delete_many(where=where_filter)
            collection.data.insert(
                properties={
                    "itemId": str(item_id),
                    "userId": str(user_id),
                    "category": category or "",
                    "schemaVersion": 1,
                },
                vector=vector,
            )
            logger.info(f"Upserted vector for item {item_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vector for item {item_id}: {str(e)}")
            return False

    def get_vector(self, item_id: UUID) -> list[float] | None:
        """Fetch the stored vector for `item_id`, or `None` if absent/on error."""
        if not self.is_connected():
            return None

        try:
            collection = self.client.collections.get(VECTOR_COLLECTION_NAME)
            where_filter = weaviate.classes.query.Filter.by_property("itemId").equal(str(item_id))
            response = collection.query.fetch_objects(
                filters=where_filter, limit=1, include_vector=True
            )
            if not response.objects:
                return None
            vector = response.objects[0].vector
            # weaviate-client v4 returns {"default": [...]} for a single
            # unnamed vector on some versions, a bare list on others.
            if isinstance(vector, dict):
                vector = vector.get("default")
            return list(vector) if vector else None
        except Exception as e:
            logger.error(f"Failed to fetch vector for item {item_id}: {str(e)}")
            return None

    def query_neighbors(
        self,
        vector: list[float],
        user_id: UUID,
        k: int = 5,
        min_sim: float = 0.85,
        exclude_item_id: UUID | None = None,
    ) -> list[tuple[UUID, float]]:
        """Nearest neighbors (by cosine similarity) to a raw `vector`, scoped
        to `user_id`. Takes a raw vector (not an item id) so callers can
        query with a fresh, not-yet-stored vector (near-duplicate check at
        upload time) as well as an already-stored one.

        `similarity = 1 - distance` for COSINE distance; a self-query should
        return similarity ~= 1.0. Returns items with `similarity >= min_sim`,
        `exclude_item_id` dropped, `[]` on any failure or Weaviate miss.
        """
        if not self.is_connected():
            return []

        try:
            collection = self.client.collections.get(VECTOR_COLLECTION_NAME)
            where_filter = weaviate.classes.query.Filter.by_property("userId").equal(str(user_id))
            response = collection.query.near_vector(
                near_vector=vector,
                limit=k + 1,
                filters=where_filter,
                return_metadata=weaviate.classes.query.MetadataQuery(distance=True),
            )

            results: list[tuple[UUID, float]] = []
            for obj in response.objects:
                raw_item_id = obj.properties.get("itemId")
                if not raw_item_id:
                    continue
                try:
                    neighbor_id = UUID(raw_item_id)
                except (ValueError, TypeError):
                    continue
                if exclude_item_id is not None and neighbor_id == exclude_item_id:
                    continue
                distance = obj.metadata.distance if obj.metadata else None
                if distance is None:
                    continue
                similarity = 1.0 - distance
                if similarity >= min_sim:
                    results.append((neighbor_id, similarity))

            return results[:k]
        except Exception as e:
            logger.error(f"Failed to query neighbors: {str(e)}")
            return []

    def delete_vector(self, item_id: UUID) -> bool:
        """Delete `item_id`'s row from `ClothingItemVector` (best-effort)."""
        if not self.is_connected():
            logger.error("Cannot delete vector: Not connected to Weaviate")
            return False

        try:
            collection = self.client.collections.get(VECTOR_COLLECTION_NAME)
            where_filter = weaviate.classes.query.Filter.by_property("itemId").equal(str(item_id))
            collection.data.delete_many(where=where_filter)
            logger.info(f"Deleted vector for item {item_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector for item {item_id}: {str(e)}")
            return False


# Global instance
weaviate_service = WeaviateEmbeddingsService()
