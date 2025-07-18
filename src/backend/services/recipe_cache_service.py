import chromadb
import json
import hashlib
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecipeCacheService:
    def __init__(self):
        """Initialize ChromaDB client and collection for recipe caching"""
        try:
            self.client = chromadb.Client()
            self.collection = self.client.get_or_create_collection("recipe_cache")
            logger.info("ChromaDB recipe cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB recipe cache: {e}")
            self.client = None
            self.collection = None

    def _generate_cache_key(self, query: str = "", ingredient: str = "") -> str:
        """Generate a unique cache key for the search parameters"""
        search_params = f"query:{query.lower().strip()}_ingredient:{ingredient.lower().strip()}"
        return hashlib.md5(search_params.encode()).hexdigest()

    def get_cached_recipes(self, query: str = "", ingredient: str = "") -> Optional[List[Dict[Any, Any]]]:
        """Retrieve cached recipes for the given search parameters"""
        if not self.collection:
            return None
        
        try:
            cache_key = self._generate_cache_key(query, ingredient)
            
            # Query ChromaDB for cached results
            results = self.collection.get(
                ids=[cache_key],
                include=["documents", "metadatas"]
            )
            
            if results['ids'] and len(results['ids']) > 0:
                # Parse the cached recipe data
                cached_data = json.loads(results['documents'][0])
                logger.info(f"Found {len(cached_data)} cached recipes for query: '{query}', ingredient: '{ingredient}'")
                return cached_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached recipes: {e}")
            return None

    def cache_recipes(self, recipes: List[Dict[Any, Any]], query: str = "", ingredient: str = "") -> bool:
        """Cache recipes in ChromaDB for future use"""
        if not self.collection or not recipes:
            return False
        
        try:
            cache_key = self._generate_cache_key(query, ingredient)
            
            # Prepare metadata
            metadata = {
                "query": query,
                "ingredient": ingredient,
                "recipe_count": len(recipes),
                "cached_at": str(int(time.time()))
            }
            
            # Store in ChromaDB
            self.collection.upsert(
                ids=[cache_key],
                documents=[json.dumps(recipes)],
                metadatas=[metadata]
            )
            
            print(f"🔥 SAVED TO CHROMA: {len(recipes)} recipes for query='{query}', ingredient='{ingredient}'")
            logger.info(f"Cached {len(recipes)} recipes for query: '{query}', ingredient: '{ingredient}'")
            return True
            
        except Exception as e:
            logger.error(f"Error caching recipes: {e}")
            return False

    def clear_cache(self) -> bool:
        """Clear all cached recipes"""
        if not self.collection:
            return False
        
        try:
            # Get all IDs and delete them
            all_results = self.collection.get()
            if all_results['ids']:
                self.collection.delete(ids=all_results['ids'])
                logger.info(f"Cleared {len(all_results['ids'])} cached recipe entries")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing recipe cache: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the recipe cache"""
        if not self.collection:
            return {"status": "unavailable", "error": "ChromaDB not initialized"}
        
        try:
            all_results = self.collection.get(include=["metadatas"])
            
            total_entries = len(all_results['ids']) if all_results['ids'] else 0
            total_recipes = sum(int(metadata.get('recipe_count', 0)) for metadata in all_results['metadatas']) if all_results['metadatas'] else 0
            
            return {
                "status": "available",
                "total_cache_entries": total_entries,
                "total_cached_recipes": total_recipes,
                "cache_keys": all_results['ids'] if all_results['ids'] else []
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}

# Import time for metadata
import time 