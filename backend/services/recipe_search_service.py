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
        Get personalized recipe recommendations with PROPER favorite food balancing:
        1. Add just 2-3 favorite foods from preferred cuisines (if available)
        2. Add just 1-2 favorite foods from other cuisines (if available) 
        3. Fill the rest with balanced cuisine recommendations
        4. Ensure no cuisine dominates and maintain diversity
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
        
        # NEW BALANCED APPROACH: Proper favorite food + cuisine balancing
        import time
        current_timestamp = int(time.time())
        random_base = random.randint(1000, 9999)
        logger.info(f"Starting BALANCED recommendations generation at timestamp: {current_timestamp}, random base: {random_base}")
        
        final_recommendations: List[Dict[str, Any]] = []
        used_ids = set()
        
        if favorite_cuisines:
            # Step 1: Find and intelligently distribute favorite foods based on cuisine overlap
            if favorite_foods:
                logger.info(f"Phase 1: Intelligently distributing favorite foods based on cuisine overlap")
                
                # First, find all favorite foods and categorize them by cuisine
                favorite_foods_in_preferred_cuisines = []
                favorite_foods_in_other_cuisines = []
                
                # Search for ALL favorite foods and categorize them
                for food in favorite_foods:
                    # Search for this favorite food from any cuisine
                    random_seed = (int(time.time() * 1000) + random_base + random.randint(0, 999)) % 10000
                    search_queries = [
                        f"delicious {food} recipes {random_seed}",
                        f"{food} recipe dishes {random_seed}",
                        f"{food} food recipes {random_seed}"
                    ]
                    
                    for query in search_queries:
                        results = self.semantic_search(query=query, filters=filters, limit=5)
                        
                        for recipe in results:
                            # Check if we already have this recipe
                            k = self._get_recipe_key(recipe)
                            if k in used_ids:
                                continue
                            
                            # Verify this recipe has a cuisine
                            recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe) or self._detect_cuisine_from_ingredients(recipe)
                            if not recipe_cuisine:
                                continue
                            
                            recipe['cuisine'] = recipe_cuisine
                            
                            # Check if recipe should be excluded
                            if self._should_exclude_recipe(recipe, user_preferences):
                                continue
                            
                            # Only include complete recipes
                            if not self._is_recipe_complete(recipe):
                                continue
                            
                            # Categorize by whether it's in a preferred cuisine
                            is_preferred_cuisine = any(c.lower() == recipe_cuisine.lower() for c in favorite_cuisines)
                            
                            if is_preferred_cuisine:
                                favorite_foods_in_preferred_cuisines.append(recipe)
                                logger.info(f"Found favorite food '{food}' in preferred cuisine '{recipe_cuisine}': {recipe.get('name', 'Unknown')}")
                            else:
                                favorite_foods_in_other_cuisines.append(recipe)
                                logger.info(f"Found favorite food '{food}' in other cuisine '{recipe_cuisine}': {recipe.get('name', 'Unknown')}")
                
                # Step 1a: Add favorite foods that are in preferred cuisines (with smart distribution)
                if favorite_foods_in_preferred_cuisines:
                    # Group favorite foods by cuisine for smart distribution
                    fav_foods_by_cuisine = {}
                    
                    for recipe in favorite_foods_in_preferred_cuisines:
                        cuisine = recipe.get('cuisine', '').lower()
                        if cuisine not in fav_foods_by_cuisine:
                            fav_foods_by_cuisine[cuisine] = []
                        fav_foods_by_cuisine[cuisine].append(recipe)
                    
                    # Smart distribution: Add 2-3 favorite foods per cuisine, but don't let them dominate
                    max_fav_foods_per_cuisine = min(3, max(1, limit // len(favorite_cuisines)))
                    
                    for cuisine, recipes in fav_foods_by_cuisine.items():
                        recipes_to_add = min(max_fav_foods_per_cuisine, len(recipes))
                        final_recommendations.extend(recipes[:recipes_to_add])
                        used_ids.update(self._get_recipe_key(r) for r in recipes[:recipes_to_add])
                        logger.info(f"Added {recipes_to_add} favorite foods from {cuisine} cuisine")
                
                # Step 1b: Add favorite foods from other cuisines (limited to prevent domination)
                if favorite_foods_in_other_cuisines:
                    remaining_slots = limit - len(final_recommendations)
                    max_other_cuisine_favs = min(2, max(1, remaining_slots // 3))  # Limit to prevent domination
                    
                    if max_other_cuisine_favs > 0:
                        other_favs_to_add = min(max_other_cuisine_favs, len(favorite_foods_in_other_cuisines))
                        final_recommendations.extend(favorite_foods_in_other_cuisines[:other_favs_to_add])
                        used_ids.update(self._get_recipe_key(r) for r in favorite_foods_in_other_cuisines[:other_favs_to_add])
                        logger.info(f"Added {other_favs_to_add} favorite foods from other cuisines")
                
                logger.info(f"Phase 1 complete: Added {len(final_recommendations)} favorite food recipes")
            
            # Step 2: Fill remaining slots with balanced cuisine recommendations
            remaining_slots = limit - len(final_recommendations)
            if remaining_slots > 0:
                logger.info(f"Phase 2: Filling {remaining_slots} remaining slots with balanced cuisine recommendations")
                
                # Calculate recipes per cuisine for the remaining slots
                recipes_per_cuisine = remaining_slots // len(favorite_cuisines)
                extra_slots = remaining_slots % len(favorite_cuisines)
                
                logger.info(f"Balanced allocation: {recipes_per_cuisine} per cuisine + {extra_slots} extra")
                
                # For each cuisine, get the required number of recipes
                for i, cuisine in enumerate(favorite_cuisines):
                    if len(final_recommendations) >= limit:
                        break
                        
                    # Calculate how many recipes this cuisine needs
                    target_count = recipes_per_cuisine + (1 if i < extra_slots else 0)
                    current_cuisine_count = len([r for r in final_recommendations if r.get('cuisine', '').lower() == cuisine.lower()])
                    needed_count = target_count - current_cuisine_count
                    
                    if needed_count <= 0:
                        continue
                        
                    logger.info(f"Target for {cuisine}: {needed_count} additional recipes (already have {current_cuisine_count})")
                    
                    cuisine_recipes_found = 0
                    search_attempts = 0
                    max_search_attempts = 5  # Prevent excessive searching
                    
                    # Search for additional recipes from this cuisine
                    while cuisine_recipes_found < needed_count and search_attempts < max_search_attempts:
                        search_attempts += 1
                        
                        # Use different search strategies to get variety
                        search_strategies = [
                            f"delicious {cuisine} recipes {random_base + search_attempts}",
                            f"{cuisine} food dishes {random_base + search_attempts}",
                            f"{cuisine} traditional recipes {random_base + search_attempts}",
                            f"{cuisine} popular dishes {random_base + search_attempts}",
                            f"{cuisine} classic recipes {random_base + search_attempts}"
                        ]
                        
                        strategy_index = (search_attempts - 1) % len(search_strategies)
                        query = search_strategies[strategy_index]
                        
                        logger.info(f"Search attempt {search_attempts} for {cuisine}: {query}")
                        
                        # Search with higher limit to get more options
                        search_limit = (needed_count - cuisine_recipes_found) * 3
                        cuisine_results = self.semantic_search(query=query, filters=filters, limit=search_limit)
                        
                        # Process results for this cuisine
                        for recipe in cuisine_results:
                            if cuisine_recipes_found >= needed_count:
                                break
                                
                            # Check if we already have this recipe
                            k = self._get_recipe_key(recipe)
                            if k in used_ids:
                                continue
                            
                            # Verify this recipe is from the target cuisine
                            recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe) or self._detect_cuisine_from_ingredients(recipe)
                            if not recipe_cuisine:
                                continue
                            
                            recipe['cuisine'] = recipe_cuisine
                            
                            # STRICT cuisine matching - must match exactly
                            target_cuisine_normalized = self._normalize_cuisine(cuisine)
                            if recipe_cuisine.lower() != target_cuisine_normalized.lower():
                                continue
                            
                            # Check if recipe should be excluded
                            if self._should_exclude_recipe(recipe, user_preferences):
                                logger.debug(f"Skipping excluded recipe: {recipe.get('name', 'Unknown')}")
                                continue
                            
                            # Only include complete recipes
                            if not self._is_recipe_complete(recipe):
                                logger.debug(f"Skipping incomplete recipe: {recipe.get('name', 'Unknown')}")
                                continue
                            
                            # Add to final recommendations
                            final_recommendations.append(recipe)
                            used_ids.add(k)
                            cuisine_recipes_found += 1
                            logger.info(f"Found {cuisine} recipe {cuisine_recipes_found}/{needed_count}: {recipe.get('name', 'Unknown')}")
                    
                    logger.info(f"Phase 2 complete for {cuisine}: {cuisine_recipes_found}/{needed_count} additional recipes found")
                    
                    # If we couldn't find enough recipes for this cuisine, log a warning
                    if cuisine_recipes_found < needed_count:
                        logger.warning(f"Could only find {cuisine_recipes_found}/{needed_count} additional recipes for {cuisine} cuisine")
        
        logger.info(f"Final recommendations complete: Total recipes: {len(final_recommendations)}")
        
        # Final validation: ensure we don't have too many from any single cuisine
        if len(final_recommendations) > 0:
            cuisine_counts = {}
            for recipe in final_recommendations:
                cuisine = recipe.get('cuisine', 'Unknown')
                cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
            
            logger.info(f"Final cuisine distribution: {cuisine_counts}")
            
            # Check if any cuisine dominates (more than 50% of recommendations)
            max_cuisine_count = max(cuisine_counts.values()) if cuisine_counts else 0
            if max_cuisine_count > len(final_recommendations) * 0.5:
                logger.warning(f"Warning: {max(cuisine_counts, key=cuisine_counts.get)} cuisine dominates with {max_cuisine_count} recipes")
        
        return final_recommendations[:limit]

    
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