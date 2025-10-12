"""Weaviate embeddings service for vector search."""

import logging
from typing import Any
from uuid import UUID

import weaviate
from weaviate.classes.config import Configure, DataType, Property

from app.core.config import settings

logger = logging.getLogger(__name__)


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
            logger.info(f"Connected to Weaviate at {settings.weaviate_host}:{settings.weaviate_port}")
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
                where_filter = where_filter & weaviate.classes.query.Filter.by_property("category").equal(category_filter)

            # Perform hybrid search
            response = collection.query.hybrid(
                query=query,
                limit=limit,
                where=where_filter,
            )

            # Parse results
            results = []
            for item in response.objects:
                results.append({
                    "item_id": item.properties.get("itemId"),
                    "category": item.properties.get("category"),
                    "color_primary": item.properties.get("colorPrimary"),
                    "color_secondary": item.properties.get("colorSecondary"),
                    "pattern": item.properties.get("pattern"),
                    "season": item.properties.get("season"),
                    "occasion": item.properties.get("occasion"),
                    "description": item.properties.get("description"),
                })

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


# Global instance
weaviate_service = WeaviateEmbeddingsService()

