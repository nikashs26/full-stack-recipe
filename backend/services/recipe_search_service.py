import chromadb
import json
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime
import logging

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
                embedding = self.encoder.encode(searchable_text).tolist()
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
        
        # Store in ChromaDB
        try:
            self.recipe_collection.upsert(
                documents=[searchable_text],
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
                
                # Safely access metadata fields with defaults
                recipe_id = metadata.get("recipe_id", f"unknown_{i}")
                name = metadata.get("name", "Unknown Recipe")
                cuisine = metadata.get("cuisine", "")
                difficulty = metadata.get("difficulty", "")
                meal_type = metadata.get("meal_type", "")
                cooking_time = metadata.get("cooking_time", "")
                avg_rating = metadata.get("avg_rating", 0)
                calories = metadata.get("calories", 0)
                protein = metadata.get("protein", 0)
                servings = metadata.get("servings", 0)
                
                # Calculate final ranking score incorporating multiple factors
                final_score = self._calculate_ranking_score(
                    base_score=base_score,
                    metadata=metadata,
                    query=query  # Use original query for ranking
                )
                
                processed_results.append({
                    "recipe_id": recipe_id,
                    "name": name,
                    "cuisine": cuisine,
                    "difficulty": difficulty,
                    "meal_type": meal_type,
                    "cooking_time": cooking_time,
                    "avg_rating": avg_rating,
                    "calories": calories,
                    "protein": protein,
                    "servings": servings,
                    "similarity_score": final_score,
                    "metadata": metadata
                })
            
            # Sort by final score and return top results
            processed_results.sort(key=lambda x: x["similarity_score"], reverse=True)
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
        if metadata.get("name", "").lower() == query_lower:
            score *= 1.5
        elif query_lower in metadata.get("name", "").lower():
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
    
    def get_recipe_recommendations(self, user_preferences: Dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
        """
        Get personalized recipe recommendations with fair distribution across favorite cuisines.
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

        # Helper: extract a stable id from a recipe dict
        def _get_recipe_key(recipe: Dict[str, Any]) -> str:
            return str(
                recipe.get('recipe_id')
                or recipe.get('id')
                or recipe.get('_id')
                or recipe.get('metadata', {}).get('recipe_id')
                or recipe.get('metadata', {}).get('id')
                or recipe.get('metadata', {}).get('_id')
                or hash(json.dumps(recipe, sort_keys=True)[:128])
            )

        # If no cuisines selected, just return top results by favorite foods first, then popular
        if not favorite_cuisines:
            aggregated: List[Dict[str, Any]] = []
            used = set()

            # Try to satisfy with favorite foods first
            if favorite_foods:
                for food in favorite_foods:
                    q = f"delicious {food} recipes"
                    res = self.semantic_search(query=q, filters=filters, limit=limit * 2)
                    for r in res:
                        k = _get_recipe_key(r)
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

            # Fallback to popular only when we have no favorite-food matches
            if len(aggregated) < limit:
                query = "popular delicious recipes"
                pop = self.semantic_search(query=query, filters=filters, limit=limit * 2)
                for r in pop:
                    k = _get_recipe_key(r)
                    if k in used:
                        continue
                    aggregated.append(r)
                    used.add(k)
                    if len(aggregated) >= limit:
                        break
            return aggregated[:limit]
        
        # Get recipes for each favorite cuisine
        recipes_by_cuisine: Dict[str, List[Dict[str, Any]]] = {}
        total_recipes_needed = limit
        
        # Calculate how many recipes to get per cuisine for even distribution
        recipes_per_cuisine = max(1, total_recipes_needed // len(favorite_cuisines))
        extra_recipes = total_recipes_needed % len(favorite_cuisines)
        
        logger.info(f"Distributing {total_recipes_needed} recipes across {len(favorite_cuisines)} cuisines: {recipes_per_cuisine} per cuisine + {extra_recipes} extra")
        
        # For each cuisine, try favorite foods within cuisine first, then general cuisine queries
        for i, cuisine in enumerate(favorite_cuisines):
            current_limit = recipes_per_cuisine + (1 if i < extra_recipes else 0)

            # Accumulator for this cuisine
            valid_cuisine_recipes: List[Dict[str, Any]] = []
            seen_ids_for_cuisine: set = set()

            # 1) Prioritize favorite foods WITHIN cuisine
            if favorite_foods:
                for food in favorite_foods:
                    if len(valid_cuisine_recipes) >= current_limit:
                        break
                    fav_cuisine_query = f"{cuisine} {food} recipes"
                    fav_results = self.semantic_search(query=fav_cuisine_query, filters=filters, limit=current_limit * 3)
                    for recipe in fav_results:
                        if len(valid_cuisine_recipes) >= current_limit:
                            break
                        # Normalize cuisine and check match
                        recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe) or self._detect_cuisine_from_ingredients(recipe)
                        if not recipe_cuisine:
                            continue
                        recipe['cuisine'] = recipe_cuisine
                        target_cuisine_normalized = self._normalize_cuisine(cuisine)
                        if recipe_cuisine.lower() != target_cuisine_normalized.lower():
                            continue
                        k = _get_recipe_key(recipe)
                        if k in seen_ids_for_cuisine:
                            continue
                        valid_cuisine_recipes.append(recipe)
                        seen_ids_for_cuisine.add(k)

            # 2) General cuisine searches if still short
            if len(valid_cuisine_recipes) < current_limit:
                # Strategy 1: Direct cuisine search
                cuisine_query = f"delicious {cuisine} recipes"
                cuisine_results = self.semantic_search(query=cuisine_query, filters=filters, limit=current_limit * 3)

                # Strategy 2: Broader phrasing
                if len(cuisine_results) < current_limit:
                    broader_query = f"{cuisine} food dishes"
                    broader_results = self.semantic_search(query=broader_query, filters=filters, limit=current_limit * 2)
                    # Combine and dedupe
                    all_results = cuisine_results + broader_results
                    unique, seen_local = [], set()
                    for r in all_results:
                        kk = _get_recipe_key(r)
                        if kk in seen_local:
                            continue
                        unique.append(r)
                        seen_local.add(kk)
                    cuisine_results = unique

                # Filter by target cuisine and append
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
                    k = _get_recipe_key(recipe)
                    if k in seen_ids_for_cuisine:
                        continue
                    valid_cuisine_recipes.append(recipe)
                    seen_ids_for_cuisine.add(k)

            recipes_by_cuisine[cuisine] = valid_cuisine_recipes[:current_limit]
            logger.info(f"Found {len(recipes_by_cuisine[cuisine])} recipes for {cuisine} cuisine (with favorite food priority)")
        
        # Combine recipes with even distribution (round-robin across cuisines)
        final_recommendations: List[Dict[str, Any]] = []
        max_recipes_per_cuisine = max(len(recipes) for recipes in recipes_by_cuisine.values()) if recipes_by_cuisine else 0
        
        logger.info(f"Recipes found per cuisine: {[(cuisine, len(recipes)) for cuisine, recipes in recipes_by_cuisine.items()]}")
        
        for i in range(max_recipes_per_cuisine):
            for cuisine in favorite_cuisines:
                if i < len(recipes_by_cuisine.get(cuisine, [])):
                    final_recommendations.append(recipes_by_cuisine[cuisine][i])
                    if len(final_recommendations) >= limit:
                        break
            if len(final_recommendations) >= limit:
                break
        
        logger.info(f"After distribution: {len(final_recommendations)} recipes distributed")
        
        # If we don't have enough recipes, try FAVORITE FOODS OUTSIDE CUISINES next
        if len(final_recommendations) < limit and favorite_foods:
            remaining_slots = limit - len(final_recommendations)
            logger.info(f"Need {remaining_slots} more recipes, trying favorite foods outside cuisines")
            
            existing_ids = { _get_recipe_key(r) for r in final_recommendations }
            added = 0
            for food in favorite_foods:
                if added >= remaining_slots:
                    break
                q = f"delicious {food} recipes"
                res = self.semantic_search(query=q, filters=filters, limit=remaining_slots * 3)
                for r in res:
                    if added >= remaining_slots:
                        break
                    k = _get_recipe_key(r)
                    if k in existing_ids:
                        continue
                    # Normalize cuisine for consistency (not restricting here)
                    recipe_cuisine = self._normalize_cuisine(r.get('cuisine', ''), r) or self._detect_cuisine_from_ingredients(r)
                    if recipe_cuisine:
                        r['cuisine'] = recipe_cuisine
                    final_recommendations.append(r)
                    existing_ids.add(k)
                    added += 1
        
        # If we still don't have enough, fill with additional popular results
        if len(final_recommendations) < limit:
            remaining_slots = limit - len(final_recommendations)
            logger.info(f"Still need {remaining_slots} more recipes, searching for additional popular results")
            
            additional_query = "popular delicious recipes"
            additional_results = self.semantic_search(query=additional_query, filters=filters, limit=remaining_slots * 3)
            existing_ids = { _get_recipe_key(r) for r in final_recommendations }
            for recipe in additional_results:
                if len(final_recommendations) >= limit:
                    break
                k = _get_recipe_key(recipe)
                if k in existing_ids:
                    continue
                recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe) or self._detect_cuisine_from_ingredients(recipe)
                if recipe_cuisine:
                    recipe['cuisine'] = recipe_cuisine
                final_recommendations.append(recipe)
                existing_ids.add(k)
        
        # Final logging of distribution
        final_cuisine_counts: Dict[str, int] = {}
        for recipe in final_recommendations:
            cuisine = recipe.get('cuisine', 'Unknown')
            final_cuisine_counts[cuisine] = final_cuisine_counts.get(cuisine, 0) + 1
        
        logger.info(f"Final cuisine distribution: {final_cuisine_counts}")
        logger.info(f"Final recommendations: {len(final_recommendations)} recipes distributed across {len(favorite_cuisines)} cuisines (fav foods prioritized)")
        return final_recommendations[:limit]

    
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
                return self._detect_cuisine_from_ingredients(recipe) or 'American'
            return 'American'
            
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
        
        # If we still don't have a match, default to American
        return 'American'
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
            searchable_text = self._create_searchable_text(recipe)
            documents.append(searchable_text)
            
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