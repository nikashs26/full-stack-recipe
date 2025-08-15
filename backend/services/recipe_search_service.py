import chromadb
import json
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime
import logging
import random
from services.recipe_cache_service import RecipeCacheService

logger = logging.getLogger(__name__)

class RecipeSearchService:
    """
    Advanced recipe search using ChromaDB for semantic similarity
    """
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        # Prefer existing, populated collections to avoid empty search results
        selected = None
        try:
            # Try common existing collections used previously
            for name in ("recipe_details_cache", "recipe_search_cache"):
                try:
                    col = self.client.get_collection(name)
                    try:
                        cnt = col.count()
                    except Exception:
                        # Fallback if count unsupported
                        cnt = 0
                    if cnt and cnt > 0:
                        selected = col
                        logger.info(f"Using existing collection '{name}' with {cnt} items")
                        break
                except Exception:
                    continue

            # If none selected yet, pick the first non-empty available collection
            if selected is None:
                try:
                    cols = self.client.list_collections()
                    for c in cols:
                        try:
                            cnt = c.count()
                        except Exception:
                            cnt = 0
                        if cnt and cnt > 0:
                            selected = c
                            logger.info(f"Using available collection '{c.name}' with {cnt} items")
                            break
                except Exception as e:
                    logger.warning(f"Could not list collections: {e}")

            # As a last resort, create or use an empty 'recipes' collection
            if selected is None:
                selected = self.client.get_or_create_collection(
                    name="recipes",
                    metadata={"description": "Recipe collection with semantic search capabilities"}
                )
                logger.warning("No populated collection found; created/using empty 'recipes' collection")
        except Exception as e:
            logger.error(f"Error selecting recipe collection: {e}")
            selected = self.client.get_or_create_collection(name="recipes")

        self.recipe_collection = selected
        # Initialize cache service for hydration of full recipe data
        try:
            self.cache_service = RecipeCacheService()
        except Exception as e:
            logger.warning(f"Failed to initialize RecipeCacheService: {e}")
            self.cache_service = None
        
        try:
            # Initialize sentence transformer for better embeddings
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Using SentenceTransformer for enhanced embeddings")
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer, falling back to ChromaDB default: {e}")
            self.encoder = None
    
    def index_recipe(self, recipe: Dict[str, Any]) -> None:
        """
        Index a recipe for semantic search with enhanced metadata
        """
        # Create rich text representation for embedding
        searchable_text = self._create_searchable_text(recipe)
        
        # Create comprehensive metadata for filtering
        recipe_id = recipe.get("id") or recipe.get("_id") or str(hash(str(recipe)))
        metadata = {
            "recipe_id": str(recipe_id),
            "name": recipe.get("name", recipe.get("title", "Unknown Recipe")),
            "cuisine": recipe.get("cuisine", ""),
            "difficulty": recipe.get("difficulty", ""),
            "meal_type": recipe.get("mealType", ""),
            "cooking_time": recipe.get("cookingTime", ""),
            "dietary_restrictions": json.dumps(recipe.get("dietaryRestrictions", [])),
            "ingredient_count": len(recipe.get("ingredients", [])),
            "avg_rating": self._calculate_avg_rating(recipe.get("ratings", [])),
            "has_reviews": len(recipe.get("comments", [])) > 0,
            "is_vegetarian": "vegetarian" in recipe.get("dietaryRestrictions", []),
            "is_vegan": "vegan" in recipe.get("dietaryRestrictions", []),
            "is_gluten_free": "gluten-free" in recipe.get("dietaryRestrictions", []),
            "calories": recipe.get("nutrition", {}).get("calories", 0),
            "protein": recipe.get("nutrition", {}).get("protein", 0),
            "total_time": recipe.get("totalTime", 0),
            "servings": recipe.get("servings", 0),
            "indexed_at": datetime.now().isoformat()
        }
        
        # Generate embedding using SentenceTransformer if available
        embedding = None
        if self.encoder:
            try:
                # Use searchable text for better semantic search while keeping full recipe in documents
                embedding = self.encoder.encode(searchable_text).tolist()
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
        
        # Store in ChromaDB
        try:
            # Store the full recipe JSON as the document for complete data access
            recipe_document = json.dumps(recipe)
            
            self.recipe_collection.upsert(
                documents=[recipe_document],  # Store full recipe data
                metadatas=[metadata],
                ids=[f"recipe_{recipe_id}"],
                embeddings=[embedding] if embedding else None
            )
            logger.info(f"Successfully indexed recipe: {metadata['name']}")
        except Exception as e:
            logger.error(f"Failed to index recipe: {e}")

    def semantic_search(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform enhanced semantic search on recipes with improved filtering and ranking
        """
        # Expand the query for better semantic matching
        expanded_query = self._expand_query(query)
        
        where_clause = self._build_where_clause(filters)
        
        try:
            # Perform semantic search with expanded query
            results = self.recipe_collection.query(
                query_texts=[expanded_query],
                n_results=min(limit * 3, 1000),  # Fetch more for post-ranking
                where=where_clause if where_clause else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            if not results or not results['documents']:
                return []
            
            # Process and rank results
            processed_results = []
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                base_score = 1 - results['distances'][0][i]  # Convert distance to similarity
                
                # Parse the full recipe document
                try:
                    if isinstance(doc, str):
                        recipe_data = json.loads(doc)
                    else:
                        recipe_data = doc
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse recipe document at index {i}")
                    continue
                
                # Debug: Log the raw recipe data from ChromaDB
                logger.debug(f"Recipe {i} raw data from ChromaDB: {recipe_data}")
                logger.debug(f"Recipe {i} metadata from ChromaDB: {metadata}")
                logger.debug(f"Recipe {i} document type: {type(doc)}, document content: {doc}")
                
                # Safely access recipe fields with defaults
                recipe_id = recipe_data.get("id") or recipe_data.get("_id") or metadata.get("recipe_id", f"unknown_{i}")
                
                # Ensure recipe_id is never undefined or empty
                if not recipe_id or recipe_id == "unknown_0":
                    recipe_id = f"recipe_{i}_{hash(str(recipe_data))}"
                
                # Look for name in multiple possible fields
                name = (recipe_data.get("name") or 
                       recipe_data.get("title") or 
                       metadata.get("name") or 
                       "Unknown Recipe")
                
                # Ensure name is never undefined or empty
                if not name or name.strip() == "":
                    name = "Untitled Recipe"
                
                # Get cuisine from recipe data first, fallback to metadata
                # Handle both singular 'cuisine' and plural 'cuisines' fields
                cuisine = ""
                if recipe_data.get("cuisines") and isinstance(recipe_data["cuisines"], list) and len(recipe_data["cuisines"]) > 0:
                    cuisine = recipe_data["cuisines"][0]  # Take first cuisine from array
                elif recipe_data.get("cuisine"):
                    cuisine = recipe_data["cuisine"]
                elif metadata.get("cuisine"):
                    cuisine = metadata["cuisine"]
                
                # Normalize the cuisine if we have one
                if cuisine:
                    cuisine = self._normalize_cuisine(cuisine, recipe_data)
                
                # Get other fields from recipe data
                difficulty = recipe_data.get("difficulty", metadata.get("difficulty", ""))
                meal_type = recipe_data.get("mealType", metadata.get("meal_type", ""))
                cooking_time = recipe_data.get("cookingTime", metadata.get("cooking_time", ""))
                avg_rating = metadata.get("avg_rating", 0)
                calories = recipe_data.get("nutrition", {}).get("calories", metadata.get("calories", 0))
                protein = recipe_data.get("nutrition", {}).get("protein", metadata.get("protein", 0))
                servings = recipe_data.get("servings", metadata.get("servings", 0))
                
                # Calculate final ranking score incorporating multiple factors
                final_score = self._calculate_ranking_score(
                    base_score=base_score,
                    metadata=metadata,
                    query=query  # Use original query for ranking
                )
                
                # Create a complete recipe object for the frontend
                recipe_obj = {
                    "id": recipe_id,
                    "title": name,  # Frontend expects 'title'
                    "name": name,    # Also include 'name' for compatibility
                    "cuisine": cuisine,
                    "cuisines": [cuisine] if cuisine else [],  # Frontend expects 'cuisines' array
                    "difficulty": difficulty,
                    "meal_type": meal_type,
                    "cooking_time": cooking_time,
                    "avg_rating": avg_rating,
                    "calories": calories,
                    "protein": protein,
                    "servings": servings,
                    "similarity_score": final_score,
                    "metadata": metadata,
                    # Add additional fields that the frontend might need
                    "readyInMinutes": recipe_data.get("ready_in_minutes"),
                    "description": recipe_data.get("description"),
                    "summary": recipe_data.get("summary"),
                    "dietaryRestrictions": recipe_data.get("dietaryRestrictions", []),
                    "diets": recipe_data.get("diets", []),
                    "tags": recipe_data.get("tags", [])
                }
                
                # Add all the important fields from the full recipe data
                if recipe_data.get("image"):
                    recipe_obj["image"] = recipe_data["image"]
                if recipe_data.get("ingredients"):
                    recipe_obj["ingredients"] = recipe_data["ingredients"]
                if recipe_data.get("instructions"):
                    recipe_obj["instructions"] = recipe_data["instructions"]
                if recipe_data.get("tags"):
                    recipe_obj["tags"] = recipe_data["tags"]
                if recipe_data.get("description"):
                    recipe_obj["description"] = recipe_data["description"]
                if recipe_data.get("ready_in_minutes"):
                    recipe_obj["ready_in_minutes"] = recipe_data["ready_in_minutes"]
                
                # Basic validation - just ensure we have a name
                if name and name != "Unknown Recipe":
                    processed_results.append(recipe_obj)
                else:
                    logger.debug(f"Skipping recipe with missing name: {name}")

            # Sort by final score and return top results
            processed_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Return the processed results directly since we already have full recipe data
            return processed_results[:limit]
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return []

    def _build_where_clause(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build advanced where clause for filtering"""
        where_clause = {}
        if not filters:
            return where_clause
            
        # Basic filters
        for key in ["cuisine", "difficulty", "meal_type"]:
            if filters.get(key):
                where_clause[key] = filters[key]
                
        # Dietary restrictions
        for restriction in ["is_vegetarian", "is_vegan", "is_gluten_free"]:
            if filters.get(restriction):
                where_clause[restriction] = True
                
        # Numeric range filters
        if filters.get("max_cooking_time"):
            where_clause["cooking_time"] = {"$lte": filters["max_cooking_time"]}
            
        if filters.get("max_calories"):
            where_clause["calories"] = {"$lte": filters["max_calories"]}
            
        if filters.get("min_rating"):
            where_clause["avg_rating"] = {"$gte": filters["min_rating"]}
            
        if filters.get("max_ingredients"):
            where_clause["ingredient_count"] = {"$lte": filters["max_ingredients"]}
            
        return where_clause

    def _calculate_ranking_score(self, base_score: float, metadata: Dict[str, Any], query: str) -> float:
        """
        Calculate a comprehensive ranking score for a recipe based on multiple factors
        """
        score = base_score
        query_lower = query.lower()
        
        # Boost exact matches in title
        recipe_name = (metadata.get("name") or metadata.get("title") or "")
        if recipe_name.lower() == query_lower:
            score *= 1.5
        elif query_lower in recipe_name.lower():
            score *= 1.2
            
        # Boost based on ratings
        avg_rating = float(metadata.get("avg_rating", 0))
        if avg_rating > 4.5:
            score *= 1.3
        elif avg_rating > 4.0:
            score *= 1.2
        elif avg_rating > 3.5:
            score *= 1.1
            
        # Boost recipes with complete information
        completeness_score = 1.0
        key_fields = ["ingredients", "instructions", "cooking_time", "difficulty", "nutrition"]
        for field in key_fields:
            if metadata.get(field):
                completeness_score += 0.05
        score *= completeness_score
        
        # Context-specific boosts
        if "quick" in query_lower or "fast" in query_lower:
            cooking_time = metadata.get("cooking_time", "")
            if isinstance(cooking_time, str) and ("minute" in cooking_time.lower() or "min" in cooking_time.lower()):
                try:
                    time_value = int(''.join(filter(str.isdigit, cooking_time)))
                    if time_value <= 30:
                        score *= 1.3
                    elif time_value <= 45:
                        score *= 1.2
                except ValueError:
                    pass
                    
        if "easy" in query_lower or "simple" in query_lower:
            if metadata.get("difficulty", "").lower() in ["easy", "beginner"]:
                score *= 1.25
                
        if "healthy" in query_lower:
            nutrition = metadata.get("nutrition", {})
            if nutrition and isinstance(nutrition, dict):
                calories = nutrition.get("calories", 1000)
                if isinstance(calories, (int, float)) and calories < 500:
                    score *= 1.2
                    
        # Boost based on ingredient count for different contexts
        ingredient_count = metadata.get("ingredient_count", 0)
        if "simple" in query_lower and ingredient_count <= 5:
            score *= 1.2
        elif "gourmet" in query_lower and ingredient_count > 10:
            score *= 1.15
            
        # Normalize final score to be between 0 and 1
        return min(max(score, 0), 1)
    
    def find_similar_recipes(self, recipe_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find recipes similar to a given recipe
        """
        # Get the recipe document
        recipe_doc = self.recipe_collection.get(
            ids=[f"recipe_{recipe_id}"],
            include=['documents']
        )
        
        if not recipe_doc or not recipe_doc['documents']:
            return []
        
        # Use the recipe's document as query
        query_text = recipe_doc['documents'][0]
        
        results = self.recipe_collection.query(
            query_texts=[query_text],
            n_results=limit + 1,  # +1 to exclude the original recipe
            include=['documents', 'metadatas', 'distances']
        )
        
        # Filter out the original recipe and process results
        similar_recipes = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                if metadata["recipe_id"] != recipe_id:  # Exclude original
                    similarity_score = 1 - results['distances'][0][i]
                    similar_recipes.append({
                        "recipe_id": metadata["recipe_id"],
                        "name": metadata["name"],
                        "cuisine": metadata["cuisine"],
                        "similarity_score": similarity_score,
                        "metadata": metadata
                    })
        
        return similar_recipes[:limit]
    
    def _get_recipe_key(self, recipe: Dict[str, Any]) -> str:
        """
        Helper: extract a stable id from a recipe dict
        """
        return str(
            recipe.get('recipe_id')
            or recipe.get('id')
            or recipe.get('_id')
            or recipe.get('metadata', {}).get('recipe_id')
            or recipe.get('metadata', {}).get('id')
            or recipe.get('metadata', {}).get('_id')
            or hash(json.dumps(recipe, sort_keys=True)[:128])
        )

    def get_recipe_recommendations(self, user_preferences: Dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
        """
        Get personalized recipe recommendations with improved prioritization:
        1. Balanced distribution across chosen cuisines (highest priority)
        2. Favorite foods distributed evenly across cuisines
        3. Fill remaining slots with variety from chosen cuisines
        """
        # Normalize cuisines while preserving user-provided order and uniqueness
        raw_cuisines = user_preferences.get("favoriteCuisines", []) or []
        norm_ordered = []
        seen = set()
        for c in raw_cuisines:
            try:
                n = self._normalize_cuisine(c)
            except Exception:
                n = str(c or '').strip().lower()
            if not n:
                continue
            if n not in seen:
                seen.add(n)
                norm_ordered.append(n)

        favorite_cuisines = norm_ordered

        # Favorite foods (normalized)
        favorite_foods = [str(f).strip().lower() for f in (user_preferences.get("favoriteFoods") or []) if str(f).strip()]

        # Build base filters from dietary restrictions
        filters = {}
        dr = [d.lower() for d in user_preferences.get("dietaryRestrictions", [])]
        if "vegetarian" in dr:
            filters["is_vegetarian"] = True
        if "vegan" in dr:
            filters["is_vegan"] = True
        if "gluten-free" in dr:
            filters["is_gluten_free"] = True

        # If no cuisines selected, prioritize favorite foods, then popular
        if not favorite_cuisines:
            aggregated: List[Dict[str, Any]] = []
            used = set()

            # Try to satisfy with favorite foods first
            if favorite_foods:
                for food in favorite_foods:
                    # Add random seed to get different results on each refresh
                    import time
                    random_seed = (int(time.time() * 1000) + random.randint(1000, 9999)) % 10000  # Use milliseconds + random for variety
                    q = f"delicious {food} recipes {random_seed}"
                    res = self.semantic_search(query=q, filters=filters, limit=limit * 2)
                    for r in res:
                        k = self._get_recipe_key(r)
                        if k in used:
                            continue
                        aggregated.append(r)
                        used.add(k)
                        if len(aggregated) >= limit:
                            logger.info("Filled recommendations using favorite foods only (no cuisines selected)")
                            return aggregated[:limit]
                # If we found any favorite-food matches, return them without filling with popular
                if len(aggregated) > 0:
                    logger.info(f"Returning {len(aggregated)} favorite-food matches (no cuisines selected)")
                    return aggregated[:limit]

            # If no favorite foods or no matches, return empty (let frontend handle fallback)
            logger.info("No cuisines selected and no favorite food matches found")
            return []
        
        # NEW APPROACH: Start with balanced cuisine distribution, then enhance with favorite foods
        import time
        current_timestamp = int(time.time())
        random_base = random.randint(1000, 9999)  # Add random base for more variety
        logger.info(f"Starting recommendations generation at timestamp: {current_timestamp}, random base: {random_base}")
        
        # PHASE 1: Ensure balanced representation across all chosen cuisines
        # This is now the highest priority to ensure diversity
        cuisine_balanced_recipes: List[Dict[str, Any]] = []
        used_ids = set()
        
        if favorite_cuisines:
            logger.info(f"Phase 1: Ensuring balanced representation across {len(favorite_cuisines)} cuisines")
            
            # Calculate base recipes per cuisine for guaranteed fair distribution
            base_recipes_per_cuisine = max(1, limit // len(favorite_cuisines))
            extra_slots = limit % len(favorite_cuisines)
            
            logger.info(f"Base distribution: {base_recipes_per_cuisine} per cuisine + {extra_slots} extra")
            
            # For each cuisine, get base recipes to ensure representation
            recipes_by_cuisine: Dict[str, List[Dict[str, Any]]] = {}
            
            for i, cuisine in enumerate(favorite_cuisines):
                current_limit = base_recipes_per_cuisine + (1 if i < extra_slots else 0)
                valid_cuisine_recipes: List[Dict[str, Any]] = []
                seen_ids_for_cuisine: set = set()
                
                # Search for general cuisine recipes
                random_seed = (int(time.time() * 1000) + random_base + random.randint(0, 999)) % 10000
                cuisine_query = f"delicious {cuisine} recipes {random_seed}"
                cuisine_results = self.semantic_search(query=cuisine_query, filters=filters, limit=current_limit * 3)
                
                # Filter by target cuisine and avoid duplicates
                for recipe in cuisine_results:
                    if len(valid_cuisine_recipes) >= current_limit:
                        break
                        
                    recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe) or self._detect_cuisine_from_ingredients(recipe)
                    if not recipe_cuisine:
                        continue
                    
                    recipe['cuisine'] = recipe_cuisine
                    
                    target_cuisine_normalized = self._normalize_cuisine(cuisine)
                    if recipe_cuisine.lower() != target_cuisine_normalized.lower():
                        continue
                    
                    # Check if we already have this recipe
                    k = self._get_recipe_key(recipe)
                    if k in used_ids or k in seen_ids_for_cuisine:
                        continue
                    
                    # Check if recipe should be excluded
                    if self._should_exclude_recipe(recipe, user_preferences):
                        logger.debug(f"Skipping excluded recipe: {recipe.get('name', 'Unknown')}")
                        continue
                    
                    # Only include complete recipes (with proper images, tags, etc.)
                    if not self._is_recipe_complete(recipe):
                        logger.debug(f"Skipping incomplete recipe: {recipe.get('name', 'Unknown')} - missing essential data")
                        continue
                        
                    valid_cuisine_recipes.append(recipe)
                    seen_ids_for_cuisine.add(k)
                
                recipes_by_cuisine[cuisine] = valid_cuisine_recipes[:current_limit]
                logger.info(f"Found {len(recipes_by_cuisine[cuisine])} base recipes for {cuisine} cuisine")
            
            # Guarantee fair distribution by taking recipes from each cuisine in rotation
            # This ensures all cuisines are represented even if some have fewer recipes
            for i in range(base_recipes_per_cuisine):
                for cuisine in favorite_cuisines:
                    if len(cuisine_balanced_recipes) >= limit:
                        break
                    if i < len(recipes_by_cuisine.get(cuisine, [])):
                        recipe = recipes_by_cuisine[cuisine][i]
                        k = self._get_recipe_key(recipe)
                        if k not in used_ids:
                            cuisine_balanced_recipes.append(recipe)
                            used_ids.add(k)
                            logger.debug(f"Added base {cuisine} recipe: {recipe.get('name', 'Unknown')}")
                
                if len(cuisine_balanced_recipes) >= limit:
                    break
            
            # Add extra recipes from cuisines that can provide them
            if extra_slots > 0:
                for i, cuisine in enumerate(favorite_cuisines):
                    if i >= extra_slots or len(cuisine_balanced_recipes) >= limit:
                        break
                    if base_recipes_per_cuisine < len(recipes_by_cuisine.get(cuisine, [])):
                        recipe = recipes_by_cuisine[cuisine][base_recipes_per_cuisine]
                        k = self._get_recipe_key(recipe)
                        if k not in used_ids:
                            cuisine_balanced_recipes.append(recipe)
                            used_ids.add(k)
                            logger.debug(f"Added extra {cuisine} recipe: {recipe.get('name', 'Unknown')}")
            
            # Ensure we have at least 1 recipe from each cuisine if possible
            for cuisine in favorite_cuisines:
                cuisine_recipes_in_balanced = [r for r in cuisine_balanced_recipes if r.get('cuisine', '').lower() == cuisine.lower()]
                if len(cuisine_recipes_in_balanced) == 0:
                    # Try to get at least 1 recipe from this cuisine
                    for recipe in recipes_by_cuisine.get(cuisine, []):
                        k = self._get_recipe_key(recipe)
                        if k not in used_ids and len(cuisine_balanced_recipes) < limit:
                            cuisine_balanced_recipes.append(recipe)
                            used_ids.add(k)
                            logger.debug(f"Added minimum {cuisine} recipe to ensure representation: {recipe.get('name', 'Unknown')}")
                            break
        
        logger.info(f"Phase 1 complete: Added {len(cuisine_balanced_recipes)} cuisine-balanced recipes")
        
        # PHASE 2: Enhance with favorite foods while maintaining cuisine balance
        # Now we can add favorite foods, but limit them per cuisine to maintain diversity
        favorite_foods_recipes: List[Dict[str, Any]] = []
        
        if favorite_foods and favorite_cuisines:
            logger.info(f"Phase 2: Enhancing with favorite foods while maintaining cuisine balance")
            
            # Calculate how many favorite food recipes we can add per cuisine
            # We want to maintain the balance we achieved in Phase 1
            max_favorite_foods_per_cuisine = max(1, (limit - len(cuisine_balanced_recipes)) // len(favorite_cuisines))
            total_favorite_foods_allowed = min(len(favorite_foods) * 2, limit - len(cuisine_balanced_recipes))
            
            logger.info(f"Adding up to {max_favorite_foods_per_cuisine} favorite foods per cuisine, total: {total_favorite_foods_allowed}")
            
            # For each cuisine, try to find favorite food recipes
            for cuisine in favorite_cuisines:
                if len(favorite_foods_recipes) >= total_favorite_foods_allowed:
                    break
                    
                cuisine_favorite_count = 0
                cuisine_recipes = [r for r in cuisine_balanced_recipes if r.get('cuisine', '').lower() == cuisine.lower()]
                
                # Don't add too many favorite foods to any single cuisine
                if len(cuisine_recipes) >= max_favorite_foods_per_cuisine + 1:
                    continue
                
                for food in favorite_foods:
                    if cuisine_favorite_count >= max_favorite_foods_per_cuisine:
                        break
                    if len(favorite_foods_recipes) >= total_favorite_foods_allowed:
                        break
                        
                    random_seed = (int(time.time() * 1000) + random_base + random.randint(0, 999)) % 10000
                    
                    # Try to find favorite food in this specific cuisine
                    search_queries = [
                        f"{cuisine} {food} recipe {random_seed}",
                        f"{food} {cuisine} recipe {random_seed}",
                        f"{cuisine} {food} dish {random_seed}"
                    ]
                    
                    for query in search_queries:
                        if cuisine_favorite_count >= max_favorite_foods_per_cuisine:
                            break
                            
                        results = self.semantic_search(query=query, filters=filters, limit=3)
                        
                        for recipe in results:
                            if cuisine_favorite_count >= max_favorite_foods_per_cuisine:
                                break
                            if len(favorite_foods_recipes) >= total_favorite_foods_allowed:
                                break
                                
                            # Check if we already have this recipe
                            k = self._get_recipe_key(recipe)
                            if k in used_ids:
                                continue
                            
                            # Verify this recipe is from the target cuisine
                            recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe) or self._detect_cuisine_from_ingredients(recipe)
                            if not recipe_cuisine or recipe_cuisine.lower() != cuisine.lower():
                                continue
                            
                            recipe['cuisine'] = recipe_cuisine
                            
                            # Check if recipe should be excluded
                            if self._should_exclude_recipe(recipe, user_preferences):
                                continue
                            
                            # Only include complete recipes
                            if not self._is_recipe_complete(recipe):
                                continue
                                
                            favorite_foods_recipes.append(recipe)
                            used_ids.add(k)
                            cuisine_favorite_count += 1
                            logger.info(f"Found favorite food '{food}' from {cuisine}: {recipe.get('name', 'Unknown')}")
                            break  # Only add one recipe per food per cuisine
        
        logger.info(f"Phase 2 complete: Added {len(favorite_foods_recipes)} favorite food recipes")
        
        # PHASE 3: Fill any remaining slots with additional cuisine variety
        remaining_slots = limit - len(cuisine_balanced_recipes) - len(favorite_foods_recipes)
        additional_cuisine_recipes: List[Dict[str, Any]] = []
        
        if remaining_slots > 0 and favorite_cuisines:
            logger.info(f"Phase 3: Filling {remaining_slots} remaining slots with additional cuisine variety")
            
            # Get additional recipes from each cuisine to fill remaining slots
            recipes_per_cuisine = max(1, remaining_slots // len(favorite_cuisines))
            
            for cuisine in favorite_cuisines:
                if len(additional_cuisine_recipes) >= remaining_slots:
                    break
                    
                # Search for more recipes from this cuisine
                random_seed = (int(time.time() * 1000) + random_base + random.randint(0, 999)) % 10000
                cuisine_query = f"{cuisine} food dishes {random_seed}"
                cuisine_results = self.semantic_search(query=cuisine_query, filters=filters, limit=recipes_per_cuisine * 2)
                
                for recipe in cuisine_results:
                    if len(additional_cuisine_recipes) >= remaining_slots:
                        break
                        
                    recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe) or self._detect_cuisine_from_ingredients(recipe)
                    if not recipe_cuisine:
                        continue
                        
                    recipe['cuisine'] = recipe_cuisine
                    
                    target_cuisine_normalized = self._normalize_cuisine(cuisine)
                    if recipe_cuisine.lower() != target_cuisine_normalized.lower():
                        continue
                    
                    # Check if we already have this recipe
                    k = self._get_recipe_key(recipe)
                    if k in used_ids:
                        continue
                    
                    # Check if recipe should be excluded
                    if self._should_exclude_recipe(recipe, user_preferences):
                        logger.debug(f"Skipping excluded recipe: {recipe.get('name', 'Unknown')}")
                        continue
                    
                    # Only include complete recipes (with proper images, tags, etc.)
                    if not self._is_recipe_complete(recipe):
                        logger.debug(f"Skipping incomplete recipe: {recipe.get('name', 'Unknown')} - missing essential data")
                        continue
                        
                    additional_cuisine_recipes.append(recipe)
                    used_ids.add(k)
        
        logger.info(f"Phase 3 complete: Added {len(additional_cuisine_recipes)} additional cuisine recipes")
        
        # Combine all phases
        final_recommendations = (
            cuisine_balanced_recipes + 
            favorite_foods_recipes + 
            additional_cuisine_recipes
        )
        
        # Skip cache hydration since we already have full recipe data from search
        # The cache service returns recipes with missing 'name' field which causes frontend issues
        hydrated = final_recommendations

        # Final validation: ensure all recipes are complete and have proper data
        validated_recommendations: List[Dict[str, Any]] = []
        for recipe in hydrated:
            if self._should_exclude_recipe(recipe, user_preferences):
                continue
            if self._is_recipe_complete(recipe):
                validated_recommendations.append(recipe)

        # Ensure we don't exceed the limit
        final_recommendations = validated_recommendations[:limit]
        
        # Final balancing: ensure fair distribution across cuisines
        if len(final_recommendations) > 0 and favorite_cuisines:
            balanced_recommendations = self._balance_cuisine_distribution(final_recommendations, favorite_cuisines, limit)
            if len(balanced_recommendations) > 0:
                final_recommendations = balanced_recommendations
                logger.info("Applied final cuisine balancing for fair distribution")
        
        logger.info(f"After validation and balancing: {len(final_recommendations)} complete recipes out of {len(validated_recommendations)} total")
        logger.info(f"Total recipes processed: {len(validated_recommendations) + len([r for r in final_recommendations if r not in validated_recommendations])}")
        
        # Final logging of distribution
        final_cuisine_counts: Dict[str, int] = {}
        for recipe in final_recommendations:
            cuisine = recipe.get('cuisine', 'Unknown')
            final_cuisine_counts[cuisine] = final_cuisine_counts.get(cuisine, 0) + 1
        
        logger.info(f"Final cuisine distribution: {final_cuisine_counts}")
        
        # Log the final recommendations for debugging
        for i, recipe in enumerate(final_recommendations):
            logger.info(f"Final recommendation {i+1}: {recipe.get('name', 'Unknown')} ({recipe.get('cuisine', 'Unknown')})")
        
        return final_recommendations

    
    def _should_exclude_recipe(self, recipe: Dict[str, Any], user_preferences: Dict[str, Any] = None) -> bool:
        """
        Check if a recipe should be excluded based on various criteria
        """
        if not isinstance(recipe, dict):
            return True
            
        # Get recipe cuisine
        cuisine = recipe.get('cuisine', '').lower()
        
        # If user has specific cuisine preferences, we're completely flexible now:
        # - Favorite foods can come from any cuisine (handled in main logic)
        # - For non-favorite foods, we still prefer chosen cuisines but don't strictly exclude others
        if user_preferences and user_preferences.get('favoriteCuisines'):
            user_cuisines = [c.lower().strip() for c in user_preferences['favoriteCuisines'] if c]
            if user_cuisines and cuisine not in user_cuisines:
                # Don't exclude - just log for debugging
                logger.debug(f"Recipe {recipe.get('name', 'Unknown')} has cuisine '{cuisine}' not in user preferences {user_cuisines}, but allowing for variety")
                # Return False to allow the recipe (cuisine filtering is now handled in the main recommendation logic)
                return False
        
        # Only exclude American cuisine if user has specific preferences and doesn't want American
        if cuisine == 'american' and user_preferences and user_preferences.get('favoriteCuisines'):
            user_cuisines = [c.lower().strip() for c in user_preferences['favoriteCuisines'] if c]
            if 'american' not in user_cuisines:
                logger.debug(f"Excluding recipe {recipe.get('name', 'Unknown')} - American cuisine not in user preferences")
                return True
        
        return False
    
    def _is_recipe_complete(self, recipe: Dict[str, Any]) -> bool:
        """
        Check if a recipe has complete data (not missing essential fields)
        """
        if not isinstance(recipe, dict):
            return False
            
        # Check for essential fields - must have a title/name
        required_fields = ['title', 'name']
        has_title = any(recipe.get(field) for field in required_fields)
        if not has_title:
            logger.debug(f"Recipe missing title/name: {recipe}")
            return False
            
        # Get the actual title/name for validation
        title = recipe.get('title', recipe.get('name', ''))
        if not title or title.strip() == '':
            logger.debug(f"Recipe has empty title/name: {recipe}")
            return False
            
        # Additional check: ensure recipe has some meaningful content
        if title.lower() in ['untitled', 'unknown recipe', 'recipe']:
            logger.debug(f"Recipe has generic title: {title}")
            return False
            
        return True
    
    def _detect_cuisine_from_ingredients(self, recipe: Dict[str, Any]) -> str:
        """Try to detect cuisine from recipe ingredients and name"""
        if not isinstance(recipe, dict):
            return ""
            
        # Get text to analyze
        text_parts = []
        if 'name' in recipe:
            text_parts.append(recipe['name'].lower())
        if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
            text_parts.extend(str(i).lower() for i in recipe['ingredients'])
        if 'instructions' in recipe:
            text_parts.append(str(recipe['instructions']).lower())
            
        text = ' '.join(text_parts)
        
        # Look for cuisine indicators
        cuisine_indicators = {
            'italian': ['pasta', 'pizza', 'risotto', 'prosciutto', 'parmesan', 'mozzarella', 'basil', 'oregano'],
            'mexican': ['taco', 'tortilla', 'salsa', 'guacamole', 'queso', 'cilantro', 'jalapeno', 'enchilada'],
            'chinese': ['soy sauce', 'hoisin', 'szechuan', 'wok', 'stir-fry', 'dumpling', 'bok choy'],
            'indian': ['curry', 'masala', 'tikka', 'naan', 'samosas', 'tandoori', 'garam masala'],
            'thai': ['curry', 'coconut milk', 'lemongrass', 'thai basil', 'fish sauce', 'pad thai'],
            'japanese': ['sushi', 'ramen', 'miso', 'wasabi', 'teriyaki', 'tempura', 'dashi'],
            'french': ['baguette', 'brie', 'provençal', 'ratatouille', 'béchamel', 'au vin', 'coq au vin'],
            'mediterranean': ['olive oil', 'feta', 'hummus', 'tzatziki', 'falafel', 'pita', 'eggplant'],
            'greek': ['feta', 'tzatziki', 'gyro', 'dolma', 'moussaka', 'kalamata'],
            'spanish': ['paella', 'chorizo', 'saffron', 'tapas', 'manchego', 'gazpacho'],
            'vietnamese': ['pho', 'banh mi', 'fish sauce', 'lemongrass', 'rice paper', 'hoisin'],
            'korean': ['kimchi', 'gochujang', 'bulgogi', 'bibimbap', 'korean bbq', 'soju'],
            'american': ['burger', 'hot dog', 'barbecue', 'mac and cheese', 'apple pie', 'buffalo wings']
        }
        
        # Count matches for each cuisine
        cuisine_scores = {cuisine: 0 for cuisine in cuisine_indicators}
        for cuisine, indicators in cuisine_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    cuisine_scores[cuisine] += 1
        
        # Return cuisine with highest score, if any
        max_score = max(cuisine_scores.values())
        if max_score > 0:
            top_cuisines = [c for c, s in cuisine_scores.items() if s == max_score]
            return top_cuisines[0]  # Return first if tie
            
        return ""
        
    def _normalize_cuisine(self, cuisine: str, recipe: Optional[Dict[str, Any]] = None) -> str:
        """
        Normalize and validate cuisine string, ensuring every recipe gets a specific country.
        
        Args:
            cuisine: The cuisine string to normalize
            recipe: Optional recipe dictionary for additional context
            
        Returns:
            Normalized cuisine string, never returns empty string
        """
        # Common ingredient to cuisine mappings
        INGREDIENT_CUISINE_MAP = {
            # Italian
            'pasta': 'Italian', 'risotto': 'Italian', 'pesto': 'Italian', 'pancetta': 'Italian',
            'prosciutto': 'Italian', 'mozzarella': 'Italian', 'parmesan': 'Italian',
            'risotto': 'Italian', 'bruschetta': 'Italian', 'tiramisu': 'Italian',
            
            # Mexican
            'taco': 'Mexican', 'burrito': 'Mexican', 'quesadilla': 'Mexican',
            'guacamole': 'Mexican', 'salsa': 'Mexican', 'enchilada': 'Mexican',
            'tamale': 'Mexican', 'mole': 'Mexican', 'pico de gallo': 'Mexican',
            
            # Indian
            'curry': 'Indian', 'masala': 'Indian', 'tikka': 'Indian', 'biryani': 'Indian',
            'naan': 'Indian', 'samosas': 'Indian', 'dal': 'Indian', 'vindaloo': 'Indian',
            'tandoori': 'Indian', 'paneer': 'Indian', 'chutney': 'Indian', 'roti': 'Indian',
            
            # Chinese
            'dumpling': 'Chinese', 'wonton': 'Chinese', 'kung pao': 'Chinese',
            'sweet and sour': 'Chinese', 'chow mein': 'Chinese', 'lo mein': 'Chinese',
            'peking duck': 'Chinese', 'char siu': 'Chinese', 'bao': 'Chinese',
            
            # Japanese
            'sushi': 'Japanese', 'sashimi': 'Japanese', 'ramen': 'Japanese',
            'tempura': 'Japanese', 'teriyaki': 'Japanese', 'udon': 'Japanese',
            'miso': 'Japanese', 'wasabi': 'Japanese', 'bento': 'Japanese',
            
            # Thai
            'pad thai': 'Thai', 'tom yum': 'Thai', 'green curry': 'Thai',
            'massaman': 'Thai', 'satay': 'Thai', 'papaya salad': 'Thai',
            
            # French
            'ratatouille': 'French', 'quiche': 'French', 'crepe': 'French',
            'croissant': 'French', 'coq au vin': 'French', 'bouillabaisse': 'French',
            
            # Mediterranean
            'hummus': 'Mediterranean', 'falafel': 'Mediterranean', 'tzatziki': 'Mediterranean',
            'tabbouleh': 'Mediterranean', 'pita': 'Mediterranean', 'baba ghanoush': 'Mediterranean',
            
            # American
            'burger': 'American', 'hot dog': 'American', 'barbecue': 'American',
            'mac and cheese': 'American', 'apple pie': 'American', 'fried chicken': 'American',
            'biscuits and gravy': 'American', 'cornbread': 'American',
            
            # Southern American
            'grits': 'American', 'jambalaya': 'American', 'gumbo': 'American',
            'cornbread': 'American', 'biscuits': 'American', 'fried green tomatoes': 'American'
        }
        
        # Common category to cuisine mappings
        CATEGORY_CUISINE_MAP = {
            'pasta': 'Italian', 'pizza': 'Italian', 'risotto': 'Italian',
            'taco': 'Mexican', 'burrito': 'Mexican', 'enchilada': 'Mexican',
            'curry': 'Indian', 'biryani': 'Indian', 'tikka': 'Indian',
            'dumpling': 'Chinese', 'noodle': 'Chinese', 'stir-fry': 'Chinese',
            'sushi': 'Japanese', 'ramen': 'Japanese', 'tempura': 'Japanese',
            'pad thai': 'Thai', 'tom yum': 'Thai', 'green curry': 'Thai',
            'ratatouille': 'French', 'quiche': 'French', 'crepe': 'French',
            'hummus': 'Mediterranean', 'falafel': 'Mediterranean', 'tzatziki': 'Mediterranean',
            'burger': 'American', 'barbecue': 'American', 'fried chicken': 'American'
        }
        
        # Handle None or empty cuisine
        if not cuisine or not isinstance(cuisine, str) or cuisine.lower().strip() in ['', 'none', 'null']:
            if recipe:
                detected = self._detect_cuisine_from_ingredients(recipe)
                if detected:
                    logger.debug(f"Detected cuisine '{detected}' from ingredients for recipe: {recipe.get('name', 'Unknown')}")
                    return detected
                # If we can't detect cuisine, return empty string instead of defaulting to American
                logger.debug(f"Could not detect cuisine from ingredients for recipe: {recipe.get('name', 'Unknown')}")
                return ""
            logger.debug("No recipe provided for cuisine detection, returning empty string")
            return ""
            
        # Normalize the cuisine string
        cuisine = cuisine.lower().strip()
        
        # Handle common generic terms with better defaults
        generic_mappings = {
            'international': '',  # Will be replaced with detected cuisine
            'fusion': '',
            'global': '',
            'southern': 'American',
            'soul food': 'American',
            'cajun': 'American',
            'creole': 'American',
            'western': 'American',
            'european': 'Italian',  # Most common European cuisine
            'asian': 'Chinese',     # Most common Asian cuisine
            'latin': 'Mexican',    # Most common Latin cuisine
            'mediterranean': 'Greek',  # Most specific Mediterranean cuisine
            'middle eastern': 'Mediterranean',
            'north american': 'American',
            'south american': 'Brazilian',
            'central american': 'Mexican',
            'eastern european': 'Polish',
            'scandinavian': 'Swedish',
            'british isles': 'British'
        }
        
        # Check for generic terms first
        if cuisine in generic_mappings:
            mapped = generic_mappings[cuisine]
            if mapped:  # If we have a direct mapping, use it
                return mapped
            # For truly generic terms like 'international', detect from recipe
            if recipe:
                detected = self._detect_cuisine_from_ingredients(recipe)
                if detected:
                    return detected
                
        # Common cuisine normalization with more comprehensive mapping
        cuisine_map = {
            'american': ['american', 'usa', 'united states', 'us', 'united states of america', 
                        'southern', 'cajun', 'creole', 'soul food'],
            'italian': ['italian', 'italy', 'tuscan', 'sicilian', 'venetian', 'roman', 'napoli', 'milanese'],
            'mexican': ['mexican', 'mexico', 'tex-mex', 'yucatecan', 'oaxacan'],
            'chinese': ['chinese', 'china', 'cantonese', 'szechuan', 'sichuan', 'hunan', 'shanghai'],
            'indian': ['indian', 'india', 'punjabi', 'south indian', 'north indian', 'kerala', 'bengali'],
            'thai': ['thai', 'thailand', 'isan', 'central thai'],
            'japanese': ['japanese', 'japan', 'sushi', 'ramen', 'washoku', 'kaiseki'],
            'french': ['french', 'france', 'provencal', 'provençal', 'lyonnaise', 'parisian'],
            'greek': ['greek', 'greece', 'cretan', 'aegean'],
            'spanish': ['spanish', 'spain', 'catalan', 'basque', 'valencian', 'andalusian'],
            'vietnamese': ['vietnamese', 'vietnam'],
            'korean': ['korean', 'korea'],
            'caribbean': ['caribbean', 'jamaican', 'trinidadian', 'barbadian', 'cuban', 'puerto rican'],
            'latin american': ['latin american', 'latin', 'brazilian', 'peruvian', 'argentinian', 'colombian', 'chilean'],
            'british': ['british', 'english', 'scottish', 'irish', 'welsh', 'cornish'],
            'german': ['german', 'germany', 'bavarian', 'swabian', 'frankish'],
            'african': ['african', 'ethiopian', 'moroccan', 'south african', 'north african', 'nigerian'],
            'turkish': ['turkish', 'turkey', 'ottoman'],
            'lebanese': ['lebanese', 'lebanon'],
            'israeli': ['israeli', 'israel'],
            'russian': ['russian', 'russia'],
            'polish': ['polish', 'poland'],
            'hungarian': ['hungarian', 'hungary'],
            'portuguese': ['portuguese', 'portugal'],
            'filipino': ['filipino', 'philippines'],
            'indonesian': ['indonesian', 'indonesia'],
            'malaysian': ['malaysian', 'malaysia'],
            'singaporean': ['singaporean', 'singapore']
        }
        
        # Check for exact matches first
        for standard_name, variations in cuisine_map.items():
            if cuisine in variations:
                return standard_name
        
        # Check for partial matches (e.g., 'south indian' contains 'indian')
        for standard_name, variations in cuisine_map.items():
            for variation in variations:
                if variation in cuisine or cuisine in variation:
                    return standard_name
        
        # If we have a recipe, try to detect from ingredients and name
        if recipe:
            detected = self._detect_cuisine_from_ingredients(recipe)
            if detected:
                return detected
        
        # Final fallback - check for any cuisine name in the string
        for standard_name in cuisine_map.keys():
            if standard_name in cuisine:
                return standard_name
        
        # If we still don't have a match, return empty string instead of defaulting to American
        # This prevents generic recipes from getting American cuisine when they shouldn't
        return ""
    
    def _create_searchable_text(self, recipe: Dict[str, Any]) -> str:
        """
        Create searchable text representation for a recipe
        """
        parts = []
        
        # Recipe name with high weight
        name = recipe.get('name', '')
        parts.extend([f"Recipe: {name}"] * 3)  # Repeat for higher weight
        
        # Cuisine and meal type with context
        cuisine = self._normalize_cuisine(recipe.get('cuisine', ''))
        meal_type = recipe.get('mealType', '')
        
        # Only include cuisine in the description if it's valid
        if cuisine:
            parts.append(f"This is a {cuisine} {meal_type} dish")
        elif meal_type:
            parts.append(f"This is a {meal_type} dish")
        
        # Dietary info with natural language
        dietary = recipe.get('dietaryRestrictions', [])
        if dietary:
            parts.append(f"Suitable for {', '.join(dietary)} diets")
        
        # Main ingredients with context
        ingredients = recipe.get('ingredients', [])
        if ingredients:
            main_ingredients = ingredients[:5]  # Focus on main ingredients
            parts.append(f"Main ingredients include {', '.join(main_ingredients)}")
            parts.append(f"This recipe uses {len(ingredients)} ingredients in total")
        
        # Cooking method keywords
        instructions = recipe.get('instructions', [])
        if instructions:
            # Extract cooking methods
            cooking_methods = []
            method_keywords = ['bake', 'fry', 'grill', 'roast', 'boil', 'steam', 'saute', 
                             'simmer', 'broil', 'poach', 'stir-fry', 'slow cook']
            instruction_text = ' '.join(instructions).lower()
            for method in method_keywords:
                if method in instruction_text:
                    cooking_methods.append(method)
            if cooking_methods:
                parts.append(f"Cooking methods: {', '.join(cooking_methods)}")
        
        # Difficulty and time with context
        difficulty = recipe.get('difficulty', '')
        cooking_time = recipe.get('cookingTime', '')
        if difficulty and cooking_time:
            parts.append(f"This is a {difficulty} recipe that takes {cooking_time}")
        
        # Add nutritional context if available
        nutrition = recipe.get('nutrition', {})
        if nutrition:
            calories = nutrition.get('calories')
            protein = nutrition.get('protein')
            if calories is not None:
                parts.append(f"Contains {calories} calories per serving")
            if protein is not None:
                parts.append(f"Contains {protein}g of protein per serving")
        
        # Add serving information
        servings = recipe.get('servings')
        if servings:
            parts.append(f"Serves {servings} people")
            
        # Join all parts with natural language
        return " | ".join(parts)
    
    def _calculate_avg_rating(self, ratings: List[float]) -> float:
        """Calculate average rating"""
        if not ratings:
            return 0.0
        return sum(ratings) / len(ratings)
    
    def bulk_index_recipes(self, recipes: List[Dict[str, Any]]) -> None:
        """
        Index multiple recipes at once for better performance
        """
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        
        for recipe in recipes:
            # Store the full recipe JSON as the document for complete data access
            recipe_document = json.dumps(recipe)
            documents.append(recipe_document)
            
            # Normalize cuisine before storing in metadata
            cuisine = self._normalize_cuisine(recipe.get("cuisine", ""))
            
            metadata = {
                "recipe_id": str(recipe.get("id", "")),
                "name": recipe.get("name", ""),
                "cuisine": cuisine,  # Use normalized cuisine
                "difficulty": recipe.get("difficulty", ""),
                "meal_type": recipe.get("mealType", ""),
                "cooking_time": recipe.get("cookingTime", ""),
                "dietary_restrictions": json.dumps(recipe.get("dietaryRestrictions", [])),
                "ingredient_count": len(recipe.get("ingredients", [])),
                "avg_rating": self._calculate_avg_rating(recipe.get("ratings", [])),
                "has_reviews": len(recipe.get("comments", [])) > 0,
                "is_vegetarian": "vegetarian" in recipe.get("dietaryRestrictions", []),
                "is_vegan": "vegan" in recipe.get("dietaryRestrictions", []),
                "is_gluten_free": "gluten-free" in recipe.get("dietaryRestrictions", []),
                "calories": recipe.get("nutrition", {}).get("calories", 0),
                "protein": recipe.get("nutrition", {}).get("protein", 0),
                "total_time": recipe.get("totalTime", 0),
                "servings": recipe.get("servings", 0),
                "indexed_at": datetime.now().isoformat()
            }
            metadatas.append(metadata)
            ids.append(f"recipe_{recipe.get('id')}")
            
            # Generate embedding if we have the encoder
            if self.encoder:
                # Use searchable text for better semantic search while keeping full recipe in documents
                searchable_text = self._create_searchable_text(recipe)
                embedding = self.encoder.encode([searchable_text])[0].tolist()
                embeddings.append(embedding)
        
        # Bulk upsert
        self.recipe_collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings if embeddings else None
        ) 

    def _expand_query(self, query: str) -> str:
        """
        Expand the search query with relevant cooking terms and synonyms
        """
        query_lower = query.lower()
        expanded_terms = []
        
        # Cooking time synonyms
        time_terms = {
            "quick": ["fast", "rapid", "speedy", "quick", "30 minutes", "easy"],
            "fast": ["quick", "rapid", "speedy", "30 minutes", "easy"],
            "instant": ["quick", "fast", "immediate", "rapid", "15 minutes"],
            "slow": ["slow-cooked", "slow cooker", "crockpot", "braised"],
        }
        
        # Cooking method synonyms
        method_terms = {
            "bake": ["roast", "oven-baked", "baked"],
            "grill": ["barbecue", "bbq", "grilled", "chargrilled"],
            "fry": ["pan-fry", "sauté", "stir-fry", "deep-fry"],
            "roast": ["bake", "oven-roasted", "roasted"],
            "steam": ["steamed", "poach"],
            "raw": ["no-cook", "uncooked", "fresh"],
        }
        
        # Dietary terms
        diet_terms = {
            "healthy": ["nutritious", "low-calorie", "light", "lean", "wholesome"],
            "vegetarian": ["meat-free", "plant-based"],
            "vegan": ["plant-based", "dairy-free", "meat-free"],
            "keto": ["low-carb", "high-fat", "ketogenic"],
            "paleo": ["grain-free", "whole30"],
            "gluten-free": ["wheat-free", "celiac-friendly"],
        }
        
        # Meal type synonyms
        meal_terms = {
            "breakfast": ["brunch", "morning meal"],
            "lunch": ["midday meal", "luncheon"],
            "dinner": ["supper", "evening meal"],
            "snack": ["appetizer", "finger food"],
            "dessert": ["sweet", "pudding", "treats"],
        }
        
        # Flavor profile terms
        flavor_terms = {
            "spicy": ["hot", "chili", "peppery", "fiery"],
            "sweet": ["sugary", "dessert", "candied"],
            "savory": ["umami", "hearty", "rich"],
            "tangy": ["sour", "citrus", "zesty"],
        }
        
        # Add original query
        expanded_terms.append(query)
        
        # Check for term matches and add synonyms
        for term_dict in [time_terms, method_terms, diet_terms, meal_terms, flavor_terms]:
            for key, synonyms in term_dict.items():
                if key in query_lower:
                    expanded_terms.extend(synonyms)
        
        # Special handling for common recipe queries
        if "easy" in query_lower:
            expanded_terms.extend(["simple", "beginner", "basic", "quick"])
        if "gourmet" in query_lower:
            expanded_terms.extend(["fancy", "elegant", "sophisticated", "upscale"])
        if "comfort food" in query_lower:
            expanded_terms.extend(["hearty", "homestyle", "warming", "cozy"])
        if "healthy" in query_lower:
            expanded_terms.extend(["nutritious", "light", "fresh", "wholesome"])
            
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in expanded_terms:
            if term not in seen:
                unique_terms.append(term)
                seen.add(term)
        
        # Join terms with weights for more relevant ones
        primary_terms = [query] * 2  # Give original query more weight
        secondary_terms = unique_terms[1:]  # Other terms have normal weight
        
        return " | ".join(primary_terms + secondary_terms)
    
    def _balance_cuisine_distribution(self, recipes: List[Dict[str, Any]], favorite_cuisines: List[str], limit: int) -> List[Dict[str, Any]]:
        """
        Ensure fair distribution of recipes across cuisines by rebalancing the final list
        """
        if not recipes or not favorite_cuisines:
            return recipes
        
        # Count current distribution
        cuisine_counts = {}
        for recipe in recipes:
            cuisine = recipe.get('cuisine', 'Unknown')
            cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
        
        # Calculate target distribution (as even as possible)
        target_per_cuisine = limit // len(favorite_cuisines)
        extra_slots = limit % len(favorite_cuisines)
        
        logger.info(f"Target distribution: {target_per_cuisine} per cuisine + {extra_slots} extra")
        logger.info(f"Current distribution: {cuisine_counts}")
        
        # Reorganize recipes to achieve fair distribution
        balanced_recipes = []
        used_recipe_keys = set()
        
        # First pass: add recipes up to target per cuisine
        for cuisine in favorite_cuisines:
            cuisine_recipes = [r for r in recipes if r.get('cuisine', '').lower() == cuisine.lower()]
            target_count = target_per_cuisine + (1 if extra_slots > 0 else 0)
            extra_slots = max(0, extra_slots - 1)
            
            added_count = 0
            for recipe in cuisine_recipes:
                if added_count >= target_count:
                    break
                    
                recipe_key = self._get_recipe_key(recipe)
                if recipe_key not in used_recipe_keys:
                    balanced_recipes.append(recipe)
                    used_recipe_keys.add(recipe_key)
                    added_count += 1
                    logger.debug(f"Added {cuisine} recipe to balanced list: {recipe.get('name', 'Unknown')}")
        
        # Ensure we have at least 1 recipe from each cuisine if possible
        for cuisine in favorite_cuisines:
            cuisine_recipes_in_balanced = [r for r in balanced_recipes if r.get('cuisine', '').lower() == cuisine.lower()]
            if len(cuisine_recipes_in_balanced) == 0:
                # Try to add at least 1 recipe from this cuisine
                for recipe in recipes:
                    if recipe.get('cuisine', '').lower() == cuisine.lower():
                        recipe_key = self._get_recipe_key(recipe)
                        if recipe_key not in used_recipe_keys and len(balanced_recipes) < limit:
                            balanced_recipes.append(recipe)
                            used_recipe_keys.add(recipe_key)
                            logger.debug(f"Added minimum {cuisine} recipe to ensure representation: {recipe.get('name', 'Unknown')}")
                            break
        
        # Second pass: add remaining recipes from any cuisine to fill remaining slots
        remaining_slots = limit - len(balanced_recipes)
        if remaining_slots > 0:
            for recipe in recipes:
                if len(balanced_recipes) >= limit:
                    break
                    
                recipe_key = self._get_recipe_key(recipe)
                if recipe_key not in used_recipe_keys:
                    balanced_recipes.append(recipe)
                    used_recipe_keys.add(recipe_key)
                    logger.debug(f"Added remaining recipe: {recipe.get('name', 'Unknown')} ({recipe.get('cuisine', 'Unknown')})")
        
        # Final distribution check
        final_cuisine_counts = {}
        for recipe in balanced_recipes:
            cuisine = recipe.get('cuisine', 'Unknown')
            final_cuisine_counts[cuisine] = final_cuisine_counts.get(cuisine, 0) + 1
        
        logger.info(f"Balanced distribution result: {final_cuisine_counts}")
        return balanced_recipes 