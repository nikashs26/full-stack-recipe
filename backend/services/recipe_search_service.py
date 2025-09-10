import chromadb
import json
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime
import logging
import random
from services.recipe_cache_service import RecipeCacheService

# Optional import for enhanced embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("sentence-transformers not available - using ChromaDB default embeddings")

logger = logging.getLogger(__name__)

class RecipeSearchService:
    """
    Advanced recipe search using ChromaDB for semantic similarity
    """
    
    def __init__(self):
        import os
        chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
        
        # For Railway/Render deployment, use persistent volume
        if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
        
        chroma_path = os.path.abspath(chroma_path)
        try:
            os.makedirs(chroma_path, exist_ok=True)
        except PermissionError:
            # Directory might already exist with correct permissions
            if not os.path.exists(chroma_path):
                raise PermissionError(f"Cannot create ChromaDB directory at {chroma_path}. Please ensure the directory exists and has correct permissions.")
        self.client = chromadb.PersistentClient(path=chroma_path)
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
        
        # Initialize sentence transformer for better embeddings (if available)
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Using SentenceTransformer for enhanced embeddings")
            except Exception as e:
                logger.warning(f"Failed to load SentenceTransformer, falling back to ChromaDB default: {e}")
                self.encoder = None
        else:
            logger.info("SentenceTransformer not available - using ChromaDB default embeddings")
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
            "is_vegetarian": (
                "vegetarian" in recipe.get("dietaryRestrictions", []) or
                recipe.get("vegetarian", False) or
                recipe.get("diets") == "vegetarian" or
                (isinstance(recipe.get("diets"), list) and "vegetarian" in recipe.get("diets", []))
            ),
            "is_vegan": (
                "vegan" in recipe.get("dietaryRestrictions", []) or
                recipe.get("vegan", False) or
                recipe.get("diets") == "vegan" or
                (isinstance(recipe.get("diets"), list) and "vegan" in recipe.get("diets", []))
            ),
            "is_gluten_free": (
                "gluten-free" in recipe.get("dietaryRestrictions", []) or
                recipe.get("gluten_free", False) or
                recipe.get("diets") == "gluten-free" or
                (isinstance(recipe.get("diets"), list) and "gluten-free" in recipe.get("diets", []))
            ),
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
                    logger.debug(f"Found cuisine from cuisines array: {cuisine}")
                elif recipe_data.get("cuisine"):
                    cuisine = recipe_data["cuisine"]
                    logger.debug(f"Found cuisine from cuisine field: {cuisine}")
                elif metadata.get("cuisine"):
                    cuisine = metadata["cuisine"]
                    logger.debug(f"Found cuisine from metadata: {cuisine}")
                
                # Debug: Log what cuisine data we found
                logger.debug(f"Recipe {i} cuisine extraction - cuisines: {recipe_data.get('cuisines')}, cuisine: {recipe_data.get('cuisine')}, metadata cuisine: {metadata.get('cuisine')}, final: {cuisine}")
                
                # Debug: Log the full recipe data structure to see what fields are available
                logger.debug(f"Recipe {i} full data structure: {json.dumps(recipe_data, indent=2)}")
                
                # Normalize the cuisine if we have one
                if cuisine:
                    cuisine = self._normalize_cuisine(cuisine, recipe_data)
                    logger.debug(f"After normalization: {cuisine}")
                else:
                    logger.warning(f"No cuisine found for recipe: {name}")
                    # Try to detect cuisine from ingredients as a fallback
                    detected_cuisine = self._detect_cuisine_from_ingredients(recipe_data)
                    if detected_cuisine:
                        cuisine = detected_cuisine
                        logger.info(f"Detected cuisine '{detected_cuisine}' from ingredients for recipe: {name}")
                    else:
                        logger.warning(f"Could not detect cuisine for recipe: {name}")
                
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
                    "cuisines": recipe_data.get("cuisines", []) if recipe_data.get("cuisines") else ([cuisine] if cuisine else []),  # Preserve original cuisines array
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
            
        # Handle cuisine filtering - support both single cuisine and list of cuisines
        if filters.get("cuisine"):
            cuisine_filter = filters["cuisine"]
            if isinstance(cuisine_filter, list):
                # Multiple cuisines - use $in operator for ChromaDB
                where_clause["cuisine"] = {"$in": cuisine_filter}
            else:
                # Single cuisine - use exact match
                where_clause["cuisine"] = cuisine_filter
                
        # Basic filters
        for key in ["difficulty", "meal_type"]:
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

    def get_recipe_recommendations(self, user_preferences: Dict[str, Any], limit: int = 16) -> List[Dict[str, Any]]:
        """
        Get personalized recipe recommendations with FAIR cuisine split and favorite foods:
        1. Reserve 2-3 slots for favorite foods (any cuisine)
        2. Distribute remaining slots equally among preferred cuisines
        3. Ensure each cuisine gets exactly the same number of recipes
        4. Add randomization for variety on each refresh
        """
        import random
        import time
        
        # Add randomization seed based on current time to get different results each time
        random.seed(int(time.time() * 1000) % 1000000)  # Use milliseconds for variety
        
        # Normalize cuisines
        raw_cuisines = user_preferences.get("favoriteCuisines", []) or []
        favorite_cuisines = []
        seen = set()
        for c in raw_cuisines:
            try:
                n = self._normalize_cuisine(c)
            except Exception:
                n = str(c or '').strip().lower()
            # Only add non-empty, valid cuisines
            if n and n not in seen and n.strip():
                seen.add(n)
                favorite_cuisines.append(n)
        
        # Log the normalized cuisines for debugging
        logger.info(f"🔍 Raw cuisines from preferences: {raw_cuisines}")
        logger.info(f"🔍 Normalized cuisines: {favorite_cuisines}")
        logger.info(f"🔍 DEBUG: Normalized cuisine details:")
        for i, raw_cuisine in enumerate(raw_cuisines):
            try:
                normalized = self._normalize_cuisine(raw_cuisine)
                logger.info(f"🔍 DEBUG:   '{raw_cuisine}' -> '{normalized}'")
            except Exception as e:
                logger.info(f"🔍 DEBUG:   '{raw_cuisine}' -> ERROR: {e}")
        
        # Shuffle cuisines to avoid always starting with the same ones
        random.shuffle(favorite_cuisines)

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

        # If no cuisines selected, prioritize favorite foods then variety
        if not favorite_cuisines:
            logger.info("No cuisines selected - prioritizing favorite foods then variety")
            all_recipes = []
            used_ids = set()
            
            # Include favorite foods first (up to 3)
            if favorite_foods:
                for food in favorite_foods[:3]:
                    query = f"delicious {food} recipes"
                    results = self.semantic_search(query=query, filters=filters, limit=2)
                    # Shuffle results for variety
                    random.shuffle(results)
                    for recipe in results:
                        k = self._get_recipe_key(recipe)
                        if k not in used_ids:
                            all_recipes.append(recipe)
                            used_ids.add(k)
                            if len(all_recipes) >= limit:
                                return all_recipes[:limit]
            
            # Fill remaining slots with popular recipes
            remaining = limit - len(all_recipes)
            if remaining > 0:
                popular_query = "popular delicious recipes"
                popular_results = self.semantic_search(query=popular_query, filters=filters, limit=remaining * 2)
                # Shuffle results for variety
                random.shuffle(popular_results)
                for recipe in popular_results:
                    k = self._get_recipe_key(recipe)
                    if k not in used_ids:
                        all_recipes.append(recipe)
                        used_ids.add(k)
                        if len(all_recipes) >= limit:
                            break
            
            return all_recipes[:limit]

        # FAIR SPLIT APPROACH: Ensure equal distribution among cuisines
        logger.info(f"Getting FAIR cuisine split for {len(favorite_cuisines)} cuisines with limit={limit}")
        
        # Reserve slots for favorite foods (2-3 slots)
        favorite_food_slots = min(3, max(2, limit // 4))  # 25% of limit, minimum 2
        cuisine_slots = limit - favorite_food_slots
        
        # Calculate equal distribution for remaining cuisines
        recipes_per_cuisine = cuisine_slots // len(favorite_cuisines)
        extra_slots = cuisine_slots % len(favorite_cuisines)
        
        logger.info(f"Allocation: {favorite_food_slots} favorite foods + {cuisine_slots} cuisine recipes")
        logger.info(f"Base per cuisine: {recipes_per_cuisine}, Extra slots: {extra_slots}")
        
        final_recommendations = []
        used_ids = set()
        
        # PHASE 1: Add favorite foods (any cuisine, but prefer preferred cuisines)
        if favorite_foods and favorite_food_slots > 0:
            logger.info(f"Phase 1: Adding {favorite_food_slots} favorite food recipes")
            
            # First try to find favorite foods in preferred cuisines
            favorite_foods_in_preferred = []
            favorite_foods_other = []
            
            for food in favorite_foods:
                if len(favorite_foods_in_preferred) + len(favorite_foods_other) >= favorite_food_slots:
                    break
                    
                query = f"delicious {food} recipes"
                results = self.semantic_search(query=query, filters=filters, limit=5)
                
                # Shuffle results for variety
                random.shuffle(results)
                
                for recipe in results:
                    if len(favorite_foods_in_preferred) + len(favorite_foods_other) >= favorite_food_slots:
                        break
                        
                    k = self._get_recipe_key(recipe)
                    if k in used_ids:
                        continue
                    
                    if self._should_exclude_recipe(recipe, user_preferences):
                        continue
                    
                    if not self._is_recipe_complete(recipe):
                        continue
                    
                    # Ensure recipe has a cuisine
                    if not recipe.get('cuisine'):
                        # Check both cuisine and cuisines fields
                        detected_cuisine = None
                        
                        # First try the cuisine field
                        if recipe.get('cuisine'):
                            detected_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe)
                        
                        # If no cuisine field, check the cuisines array
                        if not detected_cuisine and recipe.get('cuisines'):
                            cuisines_array = recipe.get('cuisines', [])
                            if isinstance(cuisines_array, list) and cuisines_array:
                                detected_cuisine = self._normalize_cuisine(cuisines_array[0], recipe)
                        
                        # If still no cuisine, try to detect from ingredients
                        if not detected_cuisine:
                            detected_cuisine = self._detect_cuisine_from_ingredients(recipe)
                        
                        # Set the cuisine field
                        recipe['cuisine'] = detected_cuisine or 'Unknown'
                    
                    # Check if it's in a preferred cuisine
                    recipe_cuisine = recipe.get('cuisine', '').lower()
                    is_preferred = any(c.lower() == recipe_cuisine for c in favorite_cuisines)
                    
                    if is_preferred and len(favorite_foods_in_preferred) < favorite_food_slots:
                        favorite_foods_in_preferred.append(recipe)
                        used_ids.add(k)
                        logger.info(f"Added favorite food in preferred cuisine: {recipe.get('title', recipe.get('name', 'Unknown'))} ({recipe_cuisine})")
                    elif not is_preferred and len(favorite_foods_other) < favorite_food_slots - len(favorite_foods_in_preferred):
                        favorite_foods_other.append(recipe)
                        used_ids.add(k)
                        logger.info(f"Added favorite food in other cuisine: {recipe.get('title', recipe.get('name', 'Unknown'))} ({recipe_cuisine})")
            
            # Add favorite foods to final recommendations
            final_recommendations.extend(favorite_foods_in_preferred)
            final_recommendations.extend(favorite_foods_other)
            logger.info(f"Added {len(favorite_foods_in_preferred)} favorite foods from preferred cuisines")
            logger.info(f"Added {len(favorite_foods_other)} favorite foods from other cuisines")
        
        # PHASE 2: Get recipes from the combined cuisine pool and distribute evenly
        remaining_slots = limit - len(final_recommendations)
        if remaining_slots > 0:
            logger.info(f"Phase 2: Filling {remaining_slots} remaining slots with balanced cuisine distribution")
            logger.info(f"🔍 CUISINE DISTRIBUTION DEBUG:")
            logger.info(f"   - Selected cuisines: {favorite_cuisines}")
            logger.info(f"   - Remaining slots: {remaining_slots}")
            
            # IMPROVED APPROACH: Get recipes from the combined cuisine pool first
            # This ensures we're using the full 339 recipes instead of searching each cuisine separately
            logger.info("🔍 Getting recipes from combined cuisine pool...")
            
            # Create a filter for all selected cuisines
            combined_cuisine_filter = {"cuisine": favorite_cuisines}
            
            logger.info(f"🔍 DEBUG: Sending cuisine filter to semantic search: {combined_cuisine_filter}")
            logger.info(f"🔍 DEBUG: This will search ChromaDB for recipes with cuisine in: {favorite_cuisines}")
            
            # Get a larger pool of recipes from all selected cuisines
            pool_size = remaining_slots * 3  # Get 3x more than needed for better distribution
            combined_results = self.semantic_search(
                query="delicious recipes", 
                filters=combined_cuisine_filter, 
                limit=pool_size
            )
            
            # Debug: Show what cuisines we're actually getting back from the search
            if combined_results:
                logger.info(f"🔍 DEBUG: Search returned {len(combined_results)} recipes")
                logger.info(f"🔍 DEBUG: First 10 recipes and their cuisines:")
                for i, recipe in enumerate(combined_results[:10]):
                    cuisine = recipe.get('cuisine', 'None')
                    cuisines = recipe.get('cuisines', 'None')
                    logger.info(f"🔍 DEBUG: Recipe {i+1}: '{recipe.get('title', recipe.get('name', 'Unknown'))}' - Cuisine: '{cuisine}' - Cuisines: {cuisines}")
            
            if combined_results:
                # Group recipes by cuisine
                recipes_by_cuisine = {}
                for recipe in combined_results:
                    k = self._get_recipe_key(recipe)
                    if k in used_ids:
                        continue
                        
                    # Ensure recipe has cuisine information
                    if not recipe.get('cuisine'):
                        # Try to detect cuisine
                        detected_cuisine = None
                        if recipe.get('cuisines') and isinstance(recipe['cuisines'], list) and recipe['cuisines']:
                            detected_cuisine = recipe['cuisines'][0]
                        else:
                            detected_cuisine = self._detect_cuisine_from_ingredients(recipe)
                        
                        if detected_cuisine:
                            recipe['cuisine'] = detected_cuisine
                            recipe['cuisines'] = [detected_cuisine]
                    
                    # Categorize by cuisine
                    recipe_cuisine = recipe.get('cuisine', 'Unknown')
                    
                    # DEBUG: Show what cuisine we're processing
                    logger.info(f"🔍 DEBUG: Processing recipe '{recipe.get('title', recipe.get('name', 'Unknown'))}' with cuisine: '{recipe_cuisine}'")
                    
                    if recipe_cuisine not in recipes_by_cuisine:
                        recipes_by_cuisine[recipe_cuisine] = []
                    recipes_by_cuisine[recipe_cuisine].append(recipe)
                
                logger.info(f"🔍 Recipes grouped by cuisine: {[(c, len(r)) for c, r in recipes_by_cuisine.items()]}")
                
                # Debug: Show what cuisines we're looking for vs what we found
                logger.info(f"🔍 DEBUG: Looking for cuisines: {favorite_cuisines}")
                logger.info(f"🔍 DEBUG: Found cuisines in recipes: {list(recipes_by_cuisine.keys())}")
                
                # Check if we have recipes for each requested cuisine
                for cuisine in favorite_cuisines:
                    count = len(recipes_by_cuisine.get(cuisine, []))
                    logger.info(f"🔍 DEBUG: Cuisine '{cuisine}' has {count} recipes available")
                
                # Now distribute recipes evenly across cuisines
                target_per_cuisine = remaining_slots // len(favorite_cuisines)
                extra_slots = remaining_slots % len(favorite_cuisines)
                
                logger.info(f"   - Target per cuisine: {target_per_cuisine}")
                logger.info(f"   - Extra slots: {extra_slots}")
                
                # Round-robin distribution to ensure fair balance
                cuisine_index = 0
                added_count = 0
                
                logger.info(f"🔍 DEBUG: Starting round-robin distribution for {remaining_slots} slots")
                
                while added_count < remaining_slots and any(len(recipes_by_cuisine.get(c, [])) > 0 for c in favorite_cuisines):
                    cuisine = favorite_cuisines[cuisine_index % len(favorite_cuisines)]
                    cuisine_recipes = recipes_by_cuisine.get(cuisine, [])
                    
                    logger.info(f"🔍 DEBUG: Round {added_count + 1}: Trying cuisine '{cuisine}' (index {cuisine_index % len(favorite_cuisines)})")
                    logger.info(f"🔍 DEBUG: Cuisine '{cuisine}' has {len(cuisine_recipes)} recipes available")
                    
                    if cuisine_recipes:
                        recipe = cuisine_recipes.pop(0)  # Take the first recipe from this cuisine
                        
                        logger.info(f"🔍 DEBUG: Selected recipe: {recipe.get('title', recipe.get('name', 'Unknown'))} from cuisine '{cuisine}'")
                        
                        if self._should_exclude_recipe(recipe, user_preferences):
                            logger.info(f"🔍 DEBUG: Recipe excluded by _should_exclude_recipe")
                            continue
                        
                        if not self._is_recipe_complete(recipe):
                            logger.info(f"🔍 DEBUG: Recipe excluded by _is_recipe_complete")
                            continue
                        
                        final_recommendations.append(recipe)
                        used_ids.add(self._get_recipe_key(recipe))
                        added_count += 1
                        
                        logger.info(f"🌍 Added {cuisine} recipe: {recipe.get('title', recipe.get('name', 'Unknown'))}")
                        
                        if added_count >= remaining_slots:
                            break
                    else:
                        logger.info(f"🔍 DEBUG: No recipes available for cuisine '{cuisine}'")
                    
                    cuisine_index += 1
                
                logger.info(f"🔍 Added {added_count} recipes with balanced cuisine distribution")
            else:
                logger.warning("⚠️ No recipes found from combined cuisine pool, falling back to individual searches")
                # Fall back to the old individual search approach
                self._fill_with_individual_cuisine_searches(final_recommendations, used_ids, favorite_cuisines, remaining_slots, filters, user_preferences)
            
            # DEBUG: If we still don't have enough recipes, try a search without cuisine filters to see what's available
            if len(final_recommendations) < remaining_slots:
                logger.warning(f"⚠️ Only got {len(final_recommendations)} recipes, trying search without cuisine filters")
                try:
                    no_filter_results = self.semantic_search(
                        query="delicious recipes", 
                        filters={},  # No cuisine filter
                        limit=50
                    )
                    if no_filter_results:
                        logger.info(f"🔍 DEBUG: Search without filters returned {len(no_filter_results)} recipes")
                        logger.info(f"🔍 DEBUG: Available cuisines without filters:")
                        available_cuisines = {}
                        for recipe in no_filter_results:
                            cuisine = recipe.get('cuisine', 'Unknown')
                            available_cuisines[cuisine] = available_cuisines.get(cuisine, 0) + 1
                        
                        for cuisine, count in sorted(available_cuisines.items()):
                            logger.info(f"🔍 DEBUG:   {cuisine}: {count} recipes")
                        
                        # Check if our requested cuisines are in the available ones
                        for requested_cuisine in favorite_cuisines:
                            found = any(requested_cuisine.lower() in available_cuisine.lower() or available_cuisine.lower() in requested_cuisine.lower() 
                                      for available_cuisine in available_cuisines.keys())
                            logger.info(f"🔍 DEBUG: Requested cuisine '{requested_cuisine}' found in database: {found}")
                except Exception as e:
                    logger.error(f"🔍 DEBUG: Error in fallback search: {e}")
        
        # FINAL DEBUG: Show the cuisine distribution in the final recommendations
        logger.info(f"🎯 FINAL RECOMMENDATIONS CUISINE DISTRIBUTION:")
        final_cuisine_counts = {}
        for recipe in final_recommendations:
            cuisine = recipe.get('cuisine', 'Unknown')
            final_cuisine_counts[cuisine] = final_cuisine_counts.get(cuisine, 0) + 1
        
        for cuisine, count in final_cuisine_counts.items():
            logger.info(f"   - {cuisine}: {count} recipes")
        
        # DEBUG: Show the actual cuisine data being sent to frontend
        logger.info(f"🔍 DEBUG: Final recommendations cuisine data check:")
        for i, recipe in enumerate(final_recommendations[:5]):  # Check first 5 recipes
            logger.info(f"🔍 DEBUG: Recipe {i+1}: '{recipe.get('title', recipe.get('name', 'Unknown'))}'")
            logger.info(f"🔍 DEBUG:   - cuisine field: '{recipe.get('cuisine', 'None')}'")
            logger.info(f"🔍 DEBUG:   - cuisines array: {recipe.get('cuisines', 'None')}")
            logger.info(f"🔍 DEBUG:   - metadata cuisine: {recipe.get('metadata', {}).get('cuisine', 'None') if recipe.get('metadata') else 'No metadata'}")
        
        return final_recommendations

    def _fill_with_individual_cuisine_searches(self, final_recommendations, used_ids, favorite_cuisines, remaining_slots, filters, user_preferences):
        """Fallback method to fill remaining slots with individual cuisine searches"""
        logger.info("🔄 Using fallback individual cuisine search approach")
        
        # Calculate target for each cuisine - ensure equal distribution
        target_per_cuisine = remaining_slots // len(favorite_cuisines)
        extra_slots = remaining_slots % len(favorite_cuisines)
        
        # Track what we've already added for each cuisine
        cuisine_added_counts = {}
        for cuisine in favorite_cuisines:
            current_count = 0
            for r in final_recommendations:
                recipe_cuisine = r.get('cuisine', '').lower()
                recipe_cuisines = r.get('cuisines', [])
                
                # Check both cuisine and cuisines fields
                if recipe_cuisine == cuisine.lower():
                    current_count += 1
                elif isinstance(recipe_cuisines, list):
                    for c in recipe_cuisines:
                        if c and c.lower() == cuisine.lower():
                            current_count += 1
                            break
            
            cuisine_added_counts[cuisine] = current_count
            logger.info(f"   - {cuisine}: {current_count} recipes already added")
        
        # Fill each cuisine to its target
        for i, cuisine in enumerate(favorite_cuisines):
            if len(final_recommendations) >= len(final_recommendations) + remaining_slots:
                break
                
            logger.info(f"🔍 PROCESSING CUISINE {i+1}/{len(favorite_cuisines)}: {cuisine}")
            
            # This cuisine gets target_per_cuisine + 1 if it's in the extra slots
            target_count = target_per_cuisine + (1 if i < extra_slots else 0)
            current_count = cuisine_added_counts[cuisine]
            needed_count = target_count - current_count
            
            logger.info(f"   - Target count: {target_count}")
            logger.info(f"   - Current count: {current_count}")
            logger.info(f"   - Needed count: {needed_count}")
            
            if needed_count <= 0:
                logger.info(f"✓ {cuisine} already has {current_count} recipes (target: {target_count})")
                continue
            
            logger.info(f"🔍 Getting {needed_count} additional recipes for {cuisine} cuisine")
            
            # Search for recipes from this specific cuisine
            search_queries = [
                f"{cuisine} recipes",
                f"{cuisine} traditional dishes",
                f"{cuisine} food",
                f"{cuisine} cuisine",
                f"{cuisine} dishes"
            ]
            
            cuisine_recipes_found = 0
            max_search_attempts = 3  # Limit search attempts per cuisine
            
            for attempt in range(max_search_attempts):
                if cuisine_recipes_found >= needed_count:
                    break
                    
                # Use different search strategies
                query = search_queries[attempt % len(search_queries)]
                logger.info(f"Search attempt {attempt + 1} for {cuisine}: '{query}'")
                
                # Search with higher limit to get more options
                search_limit = (needed_count - cuisine_recipes_found) * 4
                
                # Create cuisine-specific filters to ensure we get recipes from this cuisine
                cuisine_filters = filters.copy() if filters else {}
                cuisine_filters["cuisine"] = cuisine  # Restrict to this specific cuisine
                
                results = self.semantic_search(query=query, filters=cuisine_filters, limit=search_limit)
                
                if not results:
                    logger.warning(f"No results found for {cuisine} with query: {query}")
                    continue
                
                logger.info(f"Found {len(results)} potential recipes for {cuisine}")
                
                # Process results for this cuisine
                for recipe in results:
                    if cuisine_recipes_found >= needed_count:
                        break
                        
                    k = self._get_recipe_key(recipe)
                    if k in used_ids:
                        continue
                    
                    if self._should_exclude_recipe(recipe, user_preferences):
                        continue
                    
                    if not self._is_recipe_complete(recipe):
                        continue
                    
                    # Ensure recipe has the correct cuisine tag
                    recipe['cuisine'] = cuisine
                    # Also set the cuisines field for frontend compatibility
                    recipe['cuisines'] = [cuisine]
                    final_recommendations.append(recipe)
                    used_ids.add(k)
                    cuisine_recipes_found += 1
                    cuisine_added_counts[cuisine] += 1
                    
                    logger.info(f"✓ Added {cuisine} recipe {cuisine_recipes_found}/{needed_count}: {recipe.get('title', recipe.get('name', 'Unknown'))}")
                
                if cuisine_recipes_found >= needed_count:
                    break
            
            logger.info(f"✓ {cuisine}: Added {cuisine_recipes_found}/{needed_count} recipes")
    
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
        if 'title' in recipe:
            text_parts.append(recipe['title'].lower())
        if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
            for ingredient in recipe['ingredients']:
                if isinstance(ingredient, dict):
                    # Handle ingredient objects with 'name' field
                    if 'name' in ingredient:
                        text_parts.append(str(ingredient['name']).lower())
                    elif 'original' in ingredient:
                        text_parts.append(str(ingredient['original']).lower())
                else:
                    # Handle string ingredients
                    text_parts.append(str(ingredient).lower())
        if 'instructions' in recipe:
            text_parts.append(str(recipe['instructions']).lower())
            
        text = ' '.join(text_parts)
        
        # Enhanced cuisine indicators with more comprehensive coverage
        cuisine_indicators = {
            'italian': ['pasta', 'pizza', 'risotto', 'prosciutto', 'parmesan', 'mozzarella', 'basil', 'oregano', 'bolognese', 'carbonara', 'pesto', 'bruschetta', 'tiramisu', 'gnocchi', 'ravioli', 'lasagna'],
            'mexican': ['taco', 'tortilla', 'salsa', 'guacamole', 'queso', 'cilantro', 'jalapeno', 'enchilada', 'burrito', 'quesadilla', 'mole', 'tamale', 'pozole', 'churros'],
            'chinese': ['soy sauce', 'hoisin', 'szechuan', 'wok', 'stir-fry', 'dumpling', 'bok choy', 'kung pao', 'sweet and sour', 'chow mein', 'lo mein', 'peking duck', 'char siu', 'bao'],
            'indian': ['curry', 'masala', 'tikka', 'naan', 'samosas', 'tandoori', 'garam masala', 'biryani', 'dal', 'vindaloo', 'paneer', 'chutney', 'roti', 'bharta', 'handi', 'rogan josh', 'biryani', 'curry', 'masala', 'tikka', 'naan', 'samosas', 'tandoori', 'garam masala', 'paneer', 'chutney', 'roti', 'bharta', 'handi', 'rogan josh'],
            'thai': ['curry', 'coconut milk', 'lemongrass', 'thai basil', 'fish sauce', 'pad thai', 'tom yum', 'green curry', 'massaman', 'satay', 'papaya salad', 'mango sticky rice'],
            'japanese': ['sushi', 'ramen', 'miso', 'wasabi', 'teriyaki', 'tempura', 'dashi', 'udon', 'sashimi', 'bento', 'kaiseki', 'washoku'],
            'french': ['baguette', 'brie', 'provençal', 'ratatouille', 'béchamel', 'au vin', 'coq au vin', 'quiche', 'crepe', 'croissant', 'bouillabaisse', 'escargot'],
            'mediterranean': ['olive oil', 'feta', 'hummus', 'tzatziki', 'falafel', 'pita', 'eggplant', 'tabbouleh', 'baba ghanoush', 'dolma'],
            'greek': ['feta', 'tzatziki', 'gyro', 'dolma', 'moussaka', 'kalamata', 'spanakopita', 'baklava', 'souvlaki'],
            'spanish': ['paella', 'chorizo', 'saffron', 'tapas', 'manchego', 'gazpacho', 'tortilla', 'pulpo', 'jamón'],
            'vietnamese': ['pho', 'banh mi', 'fish sauce', 'lemongrass', 'rice paper', 'hoisin', 'nuoc cham', 'bun cha'],
            'korean': ['kimchi', 'gochujang', 'bulgogi', 'bibimbap', 'korean bbq', 'soju', 'tteokbokki', 'samgyeopsal'],
            'american': ['burger', 'hot dog', 'barbecue', 'mac and cheese', 'apple pie', 'buffalo wings', 'fried chicken', 'cornbread', 'biscuits', 'grits', 'jambalaya', 'gumbo']
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
            detected_cuisine = top_cuisines[0]  # Return first if tie
            logger.debug(f"Detected cuisine '{detected_cuisine}' from text: {text[:100]}...")
            return detected_cuisine
            
        logger.debug(f"No cuisine detected from text: {text[:100]}...")
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