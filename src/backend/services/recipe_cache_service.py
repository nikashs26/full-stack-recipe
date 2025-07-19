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
            # Initialize ChromaDB with persistent storage
            self.client = chromadb.PersistentClient(path="./chroma_db")
            
            # Create embedding function
            self.embedding_function = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
            
            # Collection for search results
            self.search_collection = self.client.get_or_create_collection(
                name="recipe_search_cache",
                metadata={"description": "Cache for recipe search results"},
                embedding_function=self.embedding_function
            )
            
            # Collection for individual recipes
            self.recipe_collection = self.client.get_or_create_collection(
                name="recipe_details_cache",
                metadata={"description": "Cache for individual recipe details"},
                embedding_function=self.embedding_function
            )
            
            logger.info("ChromaDB recipe cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB recipe cache: {e}")
            self.client = None
            self.search_collection = None
            self.recipe_collection = None

    def _generate_cache_key(self, query: str = "", ingredient: str = "") -> str:
        """Generate a unique cache key for the search parameters"""
        search_params = f"query:{query.lower().strip()}_ingredient:{ingredient.lower().strip()}"
        return hashlib.md5(search_params.encode()).hexdigest()

    def get_cached_recipes(self, query: str = "", ingredient: str = "") -> Optional[List[Dict[Any, Any]]]:
        """Retrieve cached recipes for the given search parameters"""
        if not self.recipe_collection or not self.search_collection:
            return None
        
        try:
            # Sanitize inputs
            query = (query or "").strip()
            ingredient = (ingredient or "").strip()
            
            # If no search terms, return all recipes
            if not query and not ingredient:
                results = self.recipe_collection.get(
                    include=["documents", "metadatas"]
                )
                
                if results['documents']:
                    recipes = []
                    for doc in results['documents']:
                        try:
                            recipe = json.loads(doc)
                            recipes.append(recipe)
                        except json.JSONDecodeError:
                            continue
                    return recipes
                return None
            
            # Generate search text
            search_text = f"{query} {ingredient}".strip()
            
            # Search in search collection
            search_results = self.search_collection.query(
                query_texts=[search_text],
                n_results=50,  # Get more results for better filtering
                include=["metadatas", "distances"]
            )
            
            if not search_results['metadatas']:
                return None
            
            # Get recipe IDs from search results
            recipe_ids = []
            recipe_scores = {}  # Store scores by recipe ID
            
            for i, metadata in enumerate(search_results['metadatas']):
                recipe_id = metadata['id']
                recipe_ids.append(recipe_id)
                # Get distance from first query result
                distances = search_results['distances']
                if isinstance(distances, list) and len(distances) > 0:
                    distance = distances[0][i]
                    recipe_scores[recipe_id] = 1 - distance  # Convert distance to similarity
                else:
                    recipe_scores[recipe_id] = 1.0  # Default score if no distance
            
            # Get full recipe data
            recipe_results = self.recipe_collection.get(
                ids=recipe_ids,
                include=["documents", "metadatas"]
            )
            
            if recipe_results['documents']:
                recipes = []
                for i, doc in enumerate(recipe_results['documents']):
                    try:
                        recipe = json.loads(doc)
                        recipe_id = recipe_results['metadatas'][i]['id']
                        recipe['relevance_score'] = recipe_scores.get(recipe_id, 1.0)
                        recipes.append(recipe)
                    except json.JSONDecodeError:
                        continue
                
                # Sort by relevance score
                recipes.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                return recipes
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached recipes: {e}")
            return None

    def cache_recipes(self, recipes: List[Dict[Any, Any]], query: str = "", ingredient: str = "") -> bool:
        """Cache recipes in ChromaDB for future use"""
        if not self.recipe_collection or not self.search_collection or not recipes:
            return False
        
        try:
            for recipe in recipes:
                recipe_id = str(recipe['id'])
                
                # Extract metadata and search terms
                metadata = {
                    "id": recipe_id,
                    "title": recipe.get('title', ''),
                    "cuisine": recipe.get('cuisine', ''),
                    "cached_at": str(int(time.time()))
                }
                
                # Create search text
                search_terms = []
                search_terms.append(recipe.get('title', ''))
                search_terms.extend(recipe.get('cuisines', []))
                search_terms.extend(recipe.get('diets', []))
                search_terms.extend(
                    ing.get('name', '') for ing in recipe.get('ingredients', [])
                )
                search_text = ' '.join(filter(None, search_terms))
                
                # Store recipe details
                self.recipe_collection.upsert(
                    ids=[recipe_id],
                    documents=[json.dumps(recipe)],
                    metadatas=[metadata]
                )
                
                # Store search data
                self.search_collection.upsert(
                    ids=[recipe_id],
                    documents=[search_text],
                    metadatas=[metadata]
                )
            
            logger.info(f"Cached {len(recipes)} recipes")
            return True
            
        except Exception as e:
            logger.error(f"Error caching recipes: {e}")
            return False

    def clear_cache(self) -> bool:
        """Clear all cached recipes"""
        if not self.recipe_collection or not self.search_collection:
            return False
        
        try:
            # Clear both collections
            self.recipe_collection.delete()
            self.search_collection.delete()
            logger.info("Cache cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing recipe cache: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the recipe cache"""
        if not self.recipe_collection or not self.search_collection:
            return {"status": "unavailable", "error": "ChromaDB not initialized"}
        
        try:
            all_results = self.recipe_collection.get(include=["metadatas"])
            
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