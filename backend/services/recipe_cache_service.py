import chromadb
import json
import hashlib
from typing import List, Dict, Any, Optional
import logging
import time
from datetime import datetime, timedelta

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
        try:
            cached_time = datetime.fromisoformat(cached_at)
            return datetime.now() - cached_time < self.cache_ttl
        except (ValueError, TypeError):
            return False

    def _extract_recipe_metadata(self, recipe: Dict[Any, Any]) -> Dict[str, Any]:
        """Extract searchable metadata from a recipe"""
        return {
            "id": str(recipe.get('id', '')),
            "title": recipe.get('title', ''),
            "cuisines": ','.join(recipe.get('cuisines', [])),
            "diets": ','.join(recipe.get('diets', [])),
            "dish_types": ','.join(recipe.get('dishTypes', [])),
            "ingredients": ','.join([ing.get('name', '') for ing in recipe.get('extendedIngredients', [])]),
            "cached_at": datetime.now().isoformat(),
            "source": recipe.get('source', 'unknown'),
            "calories": recipe.get('nutrition', {}).get('calories', 0),
            "cooking_time": recipe.get('readyInMinutes', 0)
        }

    def _extract_search_terms(self, recipe: Dict[Any, Any]) -> str:
        """Extract searchable terms from a recipe"""
        terms = []
        
        # Add title with higher weight
        title = recipe.get('title', '')
        if title:
            terms.extend([title] * 3)  # Repeat title for higher weight
            
        # Add cuisine types
        terms.extend(recipe.get('cuisines', []))
        
        # Add diet types
        terms.extend(recipe.get('diets', []))
        
        # Add dish types
        terms.extend(recipe.get('dishTypes', []))
        
        # Add main ingredients
        ingredients = [ing.get('name', '') for ing in recipe.get('ingredients', [])]
        terms.extend(ingredients)
        
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
                    # Search in search collection with error handling
                    search_results = self.search_collection.query(
                        query_texts=[search_text],
                        where=where if where else None,
                        n_results=50,  # Get more results for better filtering
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
                        recipe = json.loads(doc) if isinstance(doc, str) else doc
                        if not isinstance(recipe, dict):
                            logger.warning(f"Invalid recipe format: {type(recipe)}")
                            continue
                            
                        metadata = recipe_results['metadatas'][i] if i < len(recipe_results['metadatas']) else {}
                        recipe_id = metadata.get('id')
                        
                        if not recipe_id or recipe_id in seen_ids or not self._is_cache_valid(metadata.get('cached_at')):
                            continue
                        
                        # Get base score from search results
                        score = recipe_scores.get(recipe_id, 1.0)
                        
                        # Boost score based on metadata
                        try:
                            score = self._calculate_relevance_score(score, recipe, query, ingredient)
                        except Exception as e:
                            logger.error(f"Error calculating relevance score: {e}")
                            score = 1.0
                        
                        # Add score to recipe
                        recipe['relevance_score'] = score
                        all_recipes.append(recipe)
                        seen_ids.add(recipe_id)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding recipe JSON: {e}")
                        continue
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
                        recipe = json.loads(doc) if isinstance(doc, str) else doc
                        if not isinstance(recipe, dict):
                            continue
                            
                        metadata = recipe_results['metadatas'][i] if i < len(recipe_results['metadatas']) else {}
                        
                        recipe_id = recipe.get('id')
                        if not recipe_id or recipe_id in seen_ids or not self._is_cache_valid(metadata.get('cached_at')):
                            continue
                        
                        all_recipes.append(recipe)
                        seen_ids.add(recipe_id)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding recipe JSON: {e}")
                        continue
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
        """Cache recipes in ChromaDB with TTL support"""
        if not self.recipe_collection or not recipes:
            return False
        
        try:
            # Store each recipe individually in the recipe collection
            for recipe in recipes:
                recipe_id = str(recipe['id'])
                print("caching recipe", recipe_id)
                metadata = self._extract_recipe_metadata(recipe)
                search_terms = self._extract_search_terms(recipe)
                
                # Store both search terms and full recipe data
                self.recipe_collection.upsert(
                    ids=[recipe_id],
                    documents=[json.dumps(recipe)],  # Store full recipe data
                    metadatas=[metadata]
                )
                print("recipe name: ", recipe['title'])
                
                # Store search terms in a separate collection for semantic search
                self.search_collection.upsert(
                    ids=[recipe_id],
                    documents=[search_terms],  # Store search terms for semantic search
                    metadatas=[metadata]
                )
                
            
            logger.info(f"Cached {len(recipes)} recipes")
            return True
            
        except Exception as e:
            logger.error(f"Error caching recipes: {e}")
            return False

    def cache_recipe(self, recipe: Dict[Any, Any]) -> bool:
        """Cache a single recipe in ChromaDB with TTL support"""
        if not self.recipe_collection or not recipe:
            return False
        
        try:
            recipe_id = str(recipe['id'])
            metadata = self._extract_recipe_metadata(recipe)
            search_terms = self._extract_search_terms(recipe)
            
            self.recipe_collection.upsert(
                ids=[recipe_id],
                documents=[json.dumps(recipe)],
                metadatas=[metadata],
                embeddings=[search_terms]
            )
            
            logger.info(f"Cached recipe: {recipe.get('title', 'Untitled')}")
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