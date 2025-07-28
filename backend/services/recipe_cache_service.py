import chromadb
import json
import hashlib
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime, timedelta
import time
import random
import re

# Import recipe utilities
from . import recipe_utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecipeCacheService:
    def __init__(self, cache_ttl_days: int = 7):
        """
        Initialize ChromaDB client and collections for recipe caching
        
        Args:
            cache_ttl_days: Number of days before cache entries expire (default: 7)
        """
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
            
            self.cache_ttl = timedelta(days=cache_ttl_days)
            logger.info(f"ChromaDB recipe cache initialized with {cache_ttl_days} days TTL")
            logger.info(f"Using persistent storage at ./chroma_db")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB recipe cache: {e}")
            self.client = None
            self.search_collection = None
            self.recipe_collection = None
            self.cache_ttl = timedelta(days=cache_ttl_days)  # Set TTL even if initialization fails

    def _generate_cache_key(self, query: str = "", ingredient: str = "", filters: Optional[Dict[str, Any]] = None) -> str:
        """Generate a unique cache key for the search parameters including filters"""
        search_params = {
            "query": query.lower().strip(),
            "ingredient": ingredient.lower().strip(),
            "filters": filters or {}
        }
        return hashlib.md5(json.dumps(search_params, sort_keys=True).encode()).hexdigest()

    def _is_cache_valid(self, cached_at: str) -> bool:
        """Check if a cache entry is still valid based on TTL"""
        if not cached_at or not isinstance(cached_at, str):
            return False
            
        try:
            cached_time = datetime.fromisoformat(cached_at)
            return datetime.now() - cached_time < self.cache_ttl
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid cache timestamp '{cached_at}': {str(e)}")
            return False
            
    async def add_recipe(self, recipe: Dict[str, Any]) -> bool:
        """
        Add or update a recipe in the cache
        
        Args:
            recipe: The recipe data to cache
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not recipe or not isinstance(recipe, dict):
            logger.error("Invalid recipe: must be a non-empty dictionary")
            return False
            
        try:
            # Extract metadata for search
            metadata = self._extract_recipe_metadata(recipe)
            if not metadata or 'id' not in metadata:
                logger.error("Failed to extract required metadata from recipe")
                return False
                
            # Generate embeddings for the recipe
            recipe_text = f"{metadata.get('title', '')} {metadata.get('ingredients', '')}"
            
            # Add to recipe collection
            self.recipe_collection.upsert(
                ids=[metadata['id']],
                documents=[recipe_text],
                metadatas=[metadata]
            )
            
            logger.debug(f"Successfully cached recipe: {metadata.get('title')} (ID: {metadata['id']})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding recipe to cache: {str(e)}")
            return False

    def _extract_recipe_metadata(self, recipe: Dict[Any, Any]) -> Dict[str, Any]:
        """Extract searchable metadata from a recipe"""
        if not recipe or not isinstance(recipe, dict):
            logger.warning("Invalid recipe format: recipe must be a non-empty dictionary")
            return {}
            
        try:
            # Handle different recipe formats (TheMealDB vs Spoonacular)
            cuisines = []
            if 'cuisine' in recipe:  # TheMealDB format
                cuisines = [recipe['cuisine']] if recipe.get('cuisine') else []
            else:  # Spoonacular format
                cuisines = recipe.get('cuisines', [])
                if isinstance(cuisines, str):
                    cuisines = [c.strip() for c in cuisines.split(',') if c.strip()]
                
            # Handle dietary restrictions
            dietary_restrictions = recipe.get('dietary_restrictions', recipe.get('diets', []))
            if isinstance(dietary_restrictions, str):
                dietary_restrictions = [d.strip() for d in dietary_restrictions.split(',') if d.strip()]
                
            # Handle ingredients
            ingredients = []
            if 'strIngredient1' in recipe:  # TheMealDB format
                ingredients = [
                    recipe[f'strIngredient{i}'] 
                    for i in range(1, 21) 
                    if recipe.get(f'strIngredient{i}') and str(recipe[f'strIngredient{i}']).strip()
                ]
            else:  # Spoonacular format
                ingredients = [
                    str(ing.get('name', '')) 
                    for ing in recipe.get('extendedIngredients', []) 
                    if ing and isinstance(ing, dict)
                ]
            
            # Get recipe ID and title with proper fallbacks
            recipe_id = str(recipe.get('idMeal', recipe.get('id', ''))).strip()
            if not recipe_id:
                logger.warning("Recipe is missing an ID, generating a random one")
                import uuid
                recipe_id = str(uuid.uuid4())
                
            title = str(recipe.get('strMeal', recipe.get('title', 'Untitled Recipe'))).strip()
            
            # Create base metadata dictionary
            metadata = {
                "id": recipe_id,
                "title": title,
                "cuisine": cuisines[0] if cuisines else 'Other',
                "cuisines": ','.join(cuisines) if cuisines else '',
                "diets": ','.join(dietary_restrictions) if dietary_restrictions else '',
                "tags": ','.join(recipe.get('tags', [])) if recipe.get('tags') else '',
                "dish_types": ','.join(recipe.get('dishTypes', [])) if recipe.get('dishTypes') else '',
                "ingredients": ','.join(ingredients) if ingredients else '',
                "cached_at": datetime.now().isoformat(),
                "source": recipe.get('source', 'themealdb' if 'idMeal' in recipe else 'spoonacular'),
            }
            
            # Add optional fields if they exist
            if 'nutrition' in recipe and recipe['nutrition']:
                metadata["calories"] = recipe['nutrition'].get('calories', 0)
                
            if 'readyInMinutes' in recipe:
                metadata["cooking_time"] = recipe['readyInMinutes']
                
            if 'strArea' in recipe:
                metadata["area"] = recipe['strArea']
                
            # Add category if it exists
            if 'strCategory' in recipe:
                metadata["category"] = recipe['strCategory']
                
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting recipe metadata: {str(e)}")
            return {}

    def _extract_search_terms(self, recipe: Dict[Any, Any]) -> str:
        """Extract searchable terms from a recipe"""
        return recipe_utils.extract_search_terms(recipe)
        
    def _normalize_recipe(self, recipe: Union[Dict[Any, Any], str]) -> Optional[Dict[str, Any]]:
        """
        Normalize recipe data using the recipe_utils module.
        
        Args:
            recipe: The recipe data to normalize (can be dict or JSON string)
            
        Returns:
            Normalized recipe dictionary or None if invalid
        """
        return recipe_utils.normalize_recipe(recipe)
        # Add cooking method keywords from instructions
        instructions = recipe.get('instructions', '').lower()
        cooking_methods = ['bake', 'fry', 'grill', 'roast', 'boil', 'steam', 'saute']
        for method in cooking_methods:
            if method in instructions:
                terms.append(method)
        
        # Join all terms and create searchable text
        return ' '.join(filter(None, terms)).lower()

    def get_cached_recipes(self, query: str = "", ingredient: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[Any, Any]]:
        """Retrieve cached recipes for the given search parameters with TTL support"""
        if not self.recipe_collection or not self.search_collection:
            logger.warning("ChromaDB collections not initialized")
            return []
        
        try:
            # Sanitize inputs
            query = (query or "").strip()
            ingredient = (ingredient or "").strip()
            filters = filters or {}
            
            # Build where clause for filtering
            where = {}
            if filters:
                try:
                    # Handle cuisine filter
                    if filters.get("cuisine"):
                        where["cuisines"] = {"$eq": filters["cuisine"]}
                    
                    # Handle other filters...
                    if filters.get("max_cooking_time"):
                        try:
                            max_time = int(filters["max_cooking_time"])
                            where["cooking_time"] = {"$lte": max_time}
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid max_cooking_time value: {filters['max_cooking_time']}")
                    
                    if filters.get("max_calories"):
                        try:
                            max_cal = int(filters["max_calories"])
                            where["calories"] = {"$lte": max_cal}
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid max_calories value: {filters['max_calories']}")
                    
                    if filters.get("min_rating"):
                        try:
                            min_rating = float(filters["min_rating"])
                            where["avg_rating"] = {"$gte": min_rating}
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid min_rating value: {filters['min_rating']}")
                except Exception as e:
                    logger.error(f"Error building where clause: {e}")
                    # Continue with empty where clause rather than failing
                    where = {}
            
            # Combine query and ingredient for search
            search_text = f"{query} {ingredient}".strip()
            print("search text: ", search_text)
            # If we have a search query, use semantic search
            if search_text:
                try:
                    # Search in search collection with error handling - return up to 1000 results
                    search_results = self.search_collection.query(
                        query_texts=[search_text],
                        where=where if where else None,
                        n_results=1000,  # Increased to return up to 1000 results
                        include=["metadatas", "distances"]
                    )
                except Exception as e:
                    logger.error(f"Error during semantic search: {e}")
                    return []
                
                if not search_results.get('metadatas'):
                    return []
                
                # Get recipe IDs from search results
                recipe_ids = []
                recipe_scores = {}  # Store scores by recipe ID
                
                for i, metadata in enumerate(search_results['metadatas']):
                    try:
                        recipe_id = metadata.get('id')
                        if not recipe_id:
                            continue
                            
                        if self._is_cache_valid(metadata.get('cached_at')):
                            recipe_ids.append(recipe_id)
                            # Get distance from first query result
                            distances = search_results.get('distances', [])
                            if distances and len(distances) > 0 and i < len(distances[0]):
                                distance = distances[0][i]
                                recipe_scores[recipe_id] = 1 - distance  # Convert distance to similarity
                            else:
                                recipe_scores[recipe_id] = 1.0  # Default score if no distance
                    except Exception as e:
                        logger.error(f"Error processing search result metadata: {e}")
                        continue
                
                if not recipe_ids:
                    return []
                
                try:
                    # Get full recipe data
                    recipe_results = self.recipe_collection.get(
                        ids=recipe_ids,
                        include=["documents", "metadatas"]
                    )
                except Exception as e:
                    logger.error(f"Error fetching recipe details: {e}")
                    return []
                
                # Process results
                all_recipes = []
                seen_ids = set()
                
                if not recipe_results.get('documents'):
                    return []
                
                for i, doc in enumerate(recipe_results['documents']):
                    try:
                        if not doc:
                            continue
                            
                        # Try to parse as JSON if it's a string
                        if isinstance(doc, str):
                            try:
                                recipe = json.loads(doc)
                            except json.JSONDecodeError:
                                # If it's not JSON, try to use it as a document directly
                                recipe = {'title': doc, 'ingredients': []}
                        else:
                            recipe = doc
                            
                        if not isinstance(recipe, dict):
                            continue
                            
                        metadata = recipe_results['metadatas'][i] if i < len(recipe_results['metadatas']) else {}
                        
                        # Generate a default ID if not present
                        if 'id' not in recipe:
                            recipe['id'] = f"recipe_{hash(str(recipe))}"
                            
                        recipe_id = recipe['id']
                            
                        if recipe_id in seen_ids or not self._is_cache_valid(metadata.get('cached_at')):
                            continue
                        
                        # Calculate relevance score
                        try:
                            score = self._calculate_relevance_score(1.0, recipe, query, ingredient)
                        except Exception as e:
                            logger.error(f"Error calculating relevance score: {e}")
                            score = 1.0
                        
                        # Add score to recipe
                        recipe['relevance_score'] = score
                        all_recipes.append(recipe)
                        seen_ids.add(recipe_id)
                        
                    except Exception as e:
                        logger.error(f"Error processing recipe result: {e}")
                        continue
                
                # Sort by relevance score
                try:
                    all_recipes.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                except Exception as e:
                    logger.error(f"Error sorting recipes: {e}")
                
                logger.info(f"Found {len(all_recipes)} matching recipes")
                return all_recipes
                
            else:
                # Just get all recipes matching filters
                try:
                    recipe_results = self.recipe_collection.get(
                        where=where if where else None,
                        include=["documents", "metadatas"]
                    )
                except Exception as e:
                    logger.error(f"Error fetching all recipes: {e}")
                    return []
                
                if not recipe_results.get('documents'):
                    return []
                
                # Process results
                all_recipes = []
                seen_ids = set()
                
                for i, doc in enumerate(recipe_results['documents']):
                    try:
                        if not doc:
                            continue
                            
                        # Try to parse as JSON if it's a string
                        if isinstance(doc, str):
                            try:
                                recipe = json.loads(doc)
                            except json.JSONDecodeError:
                                # If it's not JSON, try to use it as a document directly
                                recipe = {'title': doc, 'ingredients': []}
                        else:
                            recipe = doc
                            
                        if not isinstance(recipe, dict):
                            continue
                            
                        metadata = recipe_results['metadatas'][i] if i < len(recipe_results['metadatas']) else {}
                        
                        # Generate a default ID if not present
                        if 'id' not in recipe:
                            recipe['id'] = f"recipe_{hash(str(recipe))}"
                            
                        recipe_id = recipe['id']
                            
                        if recipe_id in seen_ids or not self._is_cache_valid(metadata.get('cached_at')):
                            continue
                        
                        all_recipes.append(recipe)
                        seen_ids.add(recipe_id)
                        
                    except Exception as e:
                        logger.error(f"Error processing recipe result: {e}")
                        continue
                
                logger.info(f"Found {len(all_recipes)} matching recipes")
                return all_recipes
            
        except Exception as e:
            logger.error(f"Error retrieving cached recipes: {e}")
            return []

    def _calculate_relevance_score(self, base_score: float, recipe: Dict[str, Any], query: str, ingredient: str) -> float:
        """Calculate recipe relevance score"""
        score = base_score
        
        # Boost exact title matches
        if query and query.lower() in recipe.get('title', '').lower():
            score += 0.3
        
        # Boost ingredient matches
        if ingredient:
            recipe_ingredients = [ing.get('name', '').lower() for ing in recipe.get('ingredients', [])]
            if ingredient.lower() in recipe_ingredients:
                score += 0.2
        
        # Boost by rating
        if recipe.get('avg_rating'):
            score += (float(recipe['avg_rating']) / 5.0) * 0.1
        
        # Normalize score
        return min(max(score, 0.0), 1.0)

    def cache_recipes(self, recipes: List[Dict[Any, Any]], query: str = "", ingredient: str = "", filters: Optional[Dict[str, Any]] = None) -> bool:
        """
        Cache recipes in ChromaDB with TTL support
        
        Args:
            recipes: List of recipe dictionaries to cache
            query: Search query that resulted in these recipes (for search context)
            ingredient: Ingredient filter that was used (for search context)
            filters: Dictionary of filters that were applied
            
        Returns:
            bool: True if caching was successful, False otherwise
        """
        if not self.recipe_collection or not recipes:
            return False
            
        try:
            # Process filters if provided
            where = {}
            if filters:
                try:
                    if "min_rating" in filters and filters["min_rating"] is not None:
                        min_rating = float(filters["min_rating"])
                        where["avg_rating"] = {"$gte": min_rating}
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid min_rating value: {filters.get('min_rating')}")
            
            # Process each recipe
            for recipe in recipes:
                try:
                    recipe_id = str(recipe.get('id'))
                    if not recipe_id:
                        logger.warning("Skipping recipe with missing ID")
                        continue
                        
                    # Extract metadata and search terms
                    metadata = self._extract_recipe_metadata(recipe)
                    search_terms = self._extract_search_terms(recipe)
                    
                    # Store the full recipe
                    self.recipe_collection.upsert(
                        ids=[recipe_id],
                        documents=[json.dumps(recipe)],
                        metadatas=[metadata]
                    )
                    
                    # If we have a search query, index the search terms
                    search_context = f"{query} {ingredient}".strip()
                    if search_context:
                        self.search_collection.upsert(
                            ids=[f"{recipe_id}_{hash(search_context) % 10**8}"],
                            documents=[search_terms],
                            metadatas=[{
                                "recipe_id": recipe_id,
                                "search_context": search_context,
                                "indexed_at": datetime.now().isoformat()
                            }]
                        )
                        
                    logger.debug(f"Cached recipe: {recipe.get('title', 'Untitled')} (ID: {recipe_id})")
                    
                except Exception as recipe_error:
                    logger.error(f"Error caching recipe {recipe.get('id')}: {recipe_error}")
                    continue
            
            logger.info(f"Successfully cached {len(recipes)} recipes")
            return True
            
        except Exception as e:
            logger.error(f"Error in cache_recipes: {e}")
            return False

    def get_recipes_by_ids(self, recipe_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple recipes by their IDs from the cache
        
        Args:
            recipe_ids: List of recipe IDs to retrieve
            
        Returns:
            List of recipe dictionaries (or None for missing recipes)
        """
        if not self.recipe_collection or not recipe_ids:
            return []
            
        try:
            results = self.recipe_collection.get(
                ids=recipe_ids,
                include=['documents', 'metadatas']
            )
            
            recipes = []
            for doc, meta in zip(results['documents'], results['metadatas']):
                try:
                    recipe = json.loads(doc)
                    recipes.append(recipe)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse cached recipe: {doc[:100]}...")
                    recipes.append(None)
                    
            return recipes
            
        except Exception as e:
            logger.error(f"Error getting recipes by IDs: {e}")
            return []
            
    def cache_recipe(self, recipe: Dict[Any, Any]) -> bool:
        """Cache a single recipe in ChromaDB with TTL support"""
        if not self.recipe_collection or not recipe:
            return False
        
        try:
            recipe_id = str(recipe['id'])
            
            # Check if recipe already exists in cache
            existing = self.recipe_collection.get(ids=[recipe_id])
            if existing and existing.get('documents'):
                logger.debug(f"Recipe {recipe_id} already in cache, skipping")
                return True
                
            metadata = self._extract_recipe_metadata(recipe)
            search_terms = self._extract_search_terms(recipe)
            
            self.recipe_collection.upsert(
                ids=[recipe_id],
                documents=[json.dumps(recipe)],
                metadatas=[metadata],
                embeddings=[search_terms]
            )
            
            logger.debug(f"Cached recipe: {recipe.get('title', 'Untitled')} (ID: {recipe_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error caching recipe: {e}")
            return False

    def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict[Any, Any]]:
        """Get a recipe by ID from cache with TTL support"""
        if not self.recipe_collection:
            return None
        
        try:
            results = self.recipe_collection.get(
                ids=[recipe_id],
                include=["documents", "metadatas"]
            )
            
            if results['documents']:
                metadata = results['metadatas'][0]
                # Check if cache is still valid
                if self._is_cache_valid(metadata.get('cached_at')):
                    recipe = json.loads(results['documents'][0])
                    logger.info(f"Found valid cached recipe: {recipe.get('title', 'Untitled')}")
                    return recipe
                else:
                    # Remove expired recipe from cache
                    self.recipe_collection.delete(ids=[recipe_id])
                    logger.info(f"Removed expired cache entry for recipe ID: {recipe_id}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving recipe by ID: {e}")
            return None

    def clear_expired_cache(self) -> int:
        """Clear expired cache entries and return number of entries cleared"""
        cleared_count = 0
        try:
            # Clear expired search results
            search_results = self.search_collection.get(
                include=["metadatas", "ids"]
            )
            for i, metadata in enumerate(search_results['metadatas']):
                if not self._is_cache_valid(metadata.get('cached_at')):
                    self.search_collection.delete(ids=[search_results['ids'][i]])
                    cleared_count += 1
            
            # Clear expired recipes
            recipe_results = self.recipe_collection.get(
                include=["metadatas", "ids"]
            )
            for i, metadata in enumerate(recipe_results['metadatas']):
                if not self._is_cache_valid(metadata.get('cached_at')):
                    self.recipe_collection.delete(ids=[recipe_results['ids'][i]])
                    cleared_count += 1
            
            logger.info(f"Cleared {cleared_count} expired cache entries")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            return cleared_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics including TTL information"""
        stats = {
            "total_recipes": 0,
            "total_searches": 0,
            "valid_recipes": 0,
            "valid_searches": 0,
            "expired_entries": 0,
            "cache_ttl_days": self.cache_ttl.days,
            "last_cleanup": None
        }
        
        try:
            # Get recipe stats
            recipe_results = self.recipe_collection.get(
                include=["metadatas"]
            )
            stats["total_recipes"] = len(recipe_results['metadatas'])
            stats["valid_recipes"] = sum(
                1 for m in recipe_results['metadatas'] 
                if self._is_cache_valid(m.get('cached_at'))
            )
            
            # Get search stats
            search_results = self.search_collection.get(
                include=["metadatas"]
            )
            stats["total_searches"] = len(search_results['metadatas'])
            stats["valid_searches"] = sum(
                1 for m in search_results['metadatas']
                if self._is_cache_valid(m.get('cached_at'))
            )
            
            stats["expired_entries"] = (
                (stats["total_recipes"] - stats["valid_recipes"]) +
                (stats["total_searches"] - stats["valid_searches"])
            )
            
            # Get last cleanup time if available
            cleanup_meta = self.client.get_collection("recipe_details_cache").get()
            if cleanup_meta and cleanup_meta.get("last_cleanup"):
                stats["last_cleanup"] = cleanup_meta["last_cleanup"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return stats 