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
        self.recipe_collection = self.client.get_or_create_collection(
            name="recipes",
            metadata={"description": "Recipe collection with semantic search capabilities"}
        )
        
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
        metadata = {
            "recipe_id": str(recipe.get("id", "")),
            "name": recipe.get("name", ""),
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
                ids=[f"recipe_{recipe.get('id')}"],
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
                
                # Calculate final ranking score incorporating multiple factors
                final_score = self._calculate_ranking_score(
                    base_score=base_score,
                    metadata=metadata,
                    query=query  # Use original query for ranking
                )
                
                processed_results.append({
                    "recipe_id": metadata["recipe_id"],
                    "name": metadata["name"],
                    "cuisine": metadata["cuisine"],
                    "difficulty": metadata["difficulty"],
                    "meal_type": metadata["meal_type"],
                    "cooking_time": metadata["cooking_time"],
                    "avg_rating": metadata["avg_rating"],
                    "calories": metadata["calories"],
                    "protein": metadata["protein"],
                    "servings": metadata["servings"],
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
            
            # Sort by similarity score (descending) and limit results
            similar_recipes.sort(key=lambda x: x["similarity_score"], reverse=True)
            similar_recipes = similar_recipes[:limit]
            
        return similar_recipes
    
    def get_recipe_recommendations(self, user_preferences: Dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
        """
        Get personalized recipe recommendations based on user preferences.
        Prioritizes recipes matching both favorite cuisine and favorite food, then fills with favorite food (any cuisine), then favorite cuisine (any food), then others. Always includes at least one favorite food recipe if possible.
        """
        favorite_foods = [f.lower() for f in user_preferences.get("favoriteFoods", [])]
        favorite_cuisines = set(self._normalize_cuisine(c).lower() for c in user_preferences.get("favoriteCuisines", []))
        dietary_restrictions = [d.lower() for d in user_preferences.get("dietaryRestrictions", [])]
        health_goals = user_preferences.get("healthGoals", [])
        meal_types = user_preferences.get("mealTypes", [])
        skill_level = user_preferences.get("cookingSkillLevel", None)

        # Build a broad query to get a large pool of candidates
        query_parts = []
        if favorite_foods:
            food_terms = [f'"{food}"' for food in favorite_foods]
            query_parts.append(f"({' OR '.join(food_terms)})")
        if dietary_restrictions:
            query_parts.append(" AND ".join(dietary_restrictions))
        if health_goals:
            query_parts.append(" ".join(health_goals))
        if meal_types:
            query_parts.append(f"({' OR '.join(meal_types)})")
        if skill_level:
            query_parts.append(f"difficulty: {skill_level.lower()}")
        query = " ".join(query_parts) if query_parts else "popular delicious recipes"

        # Build filters
        filters = {}
        if "vegetarian" in dietary_restrictions:
            filters["is_vegetarian"] = True
        if "vegan" in dietary_restrictions:
            filters["is_vegan"] = True
        if "gluten-free" in dietary_restrictions:
            filters["is_gluten_free"] = True
        # Don't filter by cuisine yet; we'll do that in post-processing

        # Get a large pool of candidates (broad query)
        candidates = self.semantic_search(query, filters, limit * 10)

        # If favorite foods are present, also get candidates with just favorite food(s) as the query (no cuisine restriction)
        food_candidates = []
        if favorite_foods:
            for food in favorite_foods:
                food_results = self.semantic_search(food, filters, limit * 5)
                food_candidates.extend(food_results)

        # Merge and deduplicate candidates by recipe_id
        seen_ids = set()
        all_candidates = []
        for r in candidates + food_candidates:
            rid = r.get('recipe_id') or r.get('id')
            if rid and rid not in seen_ids:
                all_candidates.append(r)
                seen_ids.add(rid)

        if not all_candidates:
            return []

        # Helper to check for favorite food in a recipe
        def has_fav_food(recipe):
            text = ' '.join([
                str(recipe.get('name', '')),
                str(recipe.get('description', '')),
                ' '.join([ing['name'] if isinstance(ing, dict) and 'name' in ing else str(ing) for ing in recipe.get('ingredients', [])]),
                str(recipe.get('instructions', ''))
            ]).lower()
            return any(food in text for food in favorite_foods)

        # Helper to check for favorite cuisine in a recipe
        def has_fav_cuisine(recipe):
            cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe).lower()
            return cuisine in favorite_cuisines

        # Partition candidates
        both = []  # Matches both favorite food and cuisine
        food_only = []  # Matches favorite food (any cuisine)
        cuisine_only = []  # Matches favorite cuisine (any food)
        others = []
        for recipe in all_candidates:
            food = has_fav_food(recipe)
            cuisine = has_fav_cuisine(recipe)
            if food and cuisine:
                both.append(recipe)
            elif food:
                food_only.append(recipe)
            elif cuisine:
                cuisine_only.append(recipe)
            else:
                others.append(recipe)

        # Build recommendations
        recommendations = []
        # 1. Fill with both-matches
        recommendations.extend(both[:limit])
        # 2. Fill with food-only matches
        if len(recommendations) < limit:
            needed = limit - len(recommendations)
            recommendations.extend(food_only[:needed])
        # 3. Fill with cuisine-only matches
        if len(recommendations) < limit:
            needed = limit - len(recommendations)
            recommendations.extend(cuisine_only[:needed])
        # 4. Fill with others
        if len(recommendations) < limit:
            needed = limit - len(recommendations)
            recommendations.extend(others[:needed])
        # 5. Guarantee at least one favorite food recipe if possible
        if favorite_foods:
            if not any(has_fav_food(r) for r in recommendations) and (food_only or both):
                # Replace last with a favorite food recipe
                recommendations[-1] = (food_only or both)[0]
        return recommendations[:limit]

    def _build_recipe_query(self, user_preferences: Dict[str, Any]) -> tuple[str, dict]:
        """
        Build query parts from user preferences.
        
        Returns:
            A tuple of (query_string, filters) where:
            - query_string: The search query string
            - filters: Dictionary of filters to apply
        """
        query_parts = []
        filters = {}
        
        # 1. Add favorite foods (if any) with high priority
        favorite_foods = user_preferences.get("favoriteFoods", [])
        if favorite_foods:
            food_terms = [f'"{food}"' for food in favorite_foods]  # Exact match
            query_parts.append(f"({' OR '.join(food_terms)})")
        
        # 2. Add dietary restrictions (high priority)
        dietary_restrictions = user_preferences.get("dietaryRestrictions", [])
        if dietary_restrictions:
            query_parts.append(" AND ".join(dietary_restrictions))
        
        # 3. Add health goals
        health_goals = user_preferences.get("healthGoals", [])
        if health_goals:
            query_parts.append(" ".join(health_goals))
        
        # 4. Add meal type preferences
        meal_types = user_preferences.get("mealTypes", [])
        if meal_types:
            query_parts.append(f"({' OR '.join(meal_types)})")
            
        # 5. Add favorite cuisines as a filter
        if "favoriteCuisines" in user_preferences and user_preferences["favoriteCuisines"]:
            favorite_cuisines = {
                self._normalize_cuisine(cuisine).lower()
                for cuisine in user_preferences["favoriteCuisines"]
                if self._normalize_cuisine(cuisine)
            }
            if favorite_cuisines:
                filters["cuisine"] = {"$in": list(favorite_cuisines)}
        
        # 6. Add cooking skill level as a filter
        if user_preferences.get("cookingSkillLevel"):
            skill_level = user_preferences["cookingSkillLevel"].lower()
            filters["difficulty"] = skill_level
            
        # Combine all query parts with spaces
        query_string = " ".join(query_parts)
        
        return query_string, filters
        query = " ".join(query_parts) if query_parts else "popular delicious recipes"
        
        # Build filters with strict dietary requirements
        filters = {}
        if "vegetarian" in [d.lower() for d in dietary_restrictions]:
            filters["is_vegetarian"] = True
        if "vegan" in [d.lower() for d in dietary_restrictions]:
            filters["is_vegan"] = True
        if "gluten-free" in [d.lower() for d in dietary_restrictions]:
            filters["is_gluten_free"] = True
        
        # Apply cuisine filter if present
        if cuisine_filter:
            filters = {**filters, **cuisine_filter}
        
        # Perform initial semantic search
        results = self.semantic_search(query, filters, limit * 3)
        
        # If no results with cuisine filter but we have favorite foods, try without cuisine filter
        if not results and favorite_foods and cuisine_filter:
            filters = {k: v for k, v in filters.items() if k not in cuisine_filter}
            results = self.semantic_search(query, filters, limit * 3)
        
        if not results:
            return []
            
        # Score and sort results based on multiple factors
        scored_results = []
        for recipe in results:
            score = 0.0
            
            # 1. Score based on favorite foods match (highest priority)
            if favorite_foods:
                recipe_text = ' '.join([
                    str(recipe.get('name', '')),
                    str(recipe.get('description', '')),
                    ' '.join(recipe.get('ingredients', [])),
                    str(recipe.get('instructions', ''))
                ]).lower()
                
                for food in favorite_foods:
                    if food.lower() in recipe_text:
                        score += 0.5  # Higher weight for food matches
                        break  # Only count each food once
            
            # 2. Normalize cuisine and score cuisine matches (moderate priority)
            recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe)
            if recipe_cuisine:
                recipe['cuisine'] = recipe_cuisine
                if recipe_cuisine.lower() in favorite_cuisines:
                    score += 0.3  # Moderate weight for cuisine matches
            
            # 3. Score based on meal type match (lower priority)
            if 'meal_type' in recipe and 'mealTypes' in user_preferences:
                if any(mt.lower() in recipe.get('meal_type', '').lower() 
                      for mt in user_preferences['mealTypes'] if recipe.get('meal_type')):
                    score += 0.2
            
            # 4. Score based on cooking time (prefer shorter times)
            if 'cooking_time' in recipe and isinstance(recipe['cooking_time'], (int, float)):
                if recipe['cooking_time'] <= 30:
                    score += 0.1
                elif recipe['cooking_time'] <= 60:
                    score += 0.05
            
            # 5. Score based on rating if available (small boost)
            if 'avg_rating' in recipe and isinstance(recipe['avg_rating'], (int, float)):
                score += recipe['avg_rating'] * 0.05  # Small weight for ratings
            
            scored_results.append((recipe, score))
        
        # Sort by score (descending) and take top results
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # If we don't have enough results, try a more relaxed search
        if len(scored_results) < limit:
            # Try again without any filters except dietary restrictions
            relaxed_filters = {}
            if "vegetarian" in [d.lower() for d in dietary_restrictions]:
                relaxed_filters["is_vegetarian"] = True
            if "vegan" in [d.lower() for d in dietary_restrictions]:
                relaxed_filters["is_vegan"] = True
            if "gluten-free" in [d.lower() for d in dietary_restrictions]:
                relaxed_filters["is_gluten_free"] = True
                
            # Only search again if we have different filters
            if relaxed_filters != filters:
                relaxed_results = self.semantic_search(query, relaxed_filters, limit * 3)
                
                # Add any new results with lower priority
                if relaxed_results:
                    for recipe in relaxed_results:
                        if not any(r[0]['id'] == recipe.get('id') for r in scored_results):
                            # Give relaxed results a lower base score
                            scored_results.append((recipe, -0.5))
                    
                    # Re-sort all results
                    scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results with their scores (remove scores from final output)
        return [r[0] for r in scored_results[:limit]]

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
            'mediterranean': ['olive oil', 'feta', 'hummus', 'falafel', 'pita', 'eggplant'],
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
            Normalized cuisine string, always returns a specific country
        """
        # Map of non-country cuisines to their respective countries
        CUISINE_TO_COUNTRY = {
            # Regional/Continental to Countries
            'southern': 'American',
            'soul food': 'American',
            'cajun': 'American',
            'creole': 'American',
            'southwestern': 'American',
            'mediterranean': 'Greek',  # Most representative country
            'middle eastern': 'Lebanese',  # Most representative country
            'scandinavian': 'Swedish',
            'nordic': 'Swedish',
            'caribbean': 'Jamaican',
            'latin': 'Mexican',
            'latin american': 'Mexican',
            'central american': 'Mexican',
            'south american': 'Brazilian',
            'north american': 'American',
            'eastern european': 'Polish',
            'western european': 'French',
            'northern european': 'German',
            'southern european': 'Italian',
            'balkan': 'Greek',
            'baltic': 'Lithuanian',
            'british isles': 'British',
            'british': 'British',
            'celtic': 'Irish',
            'asian': 'Chinese',
            'southeast asian': 'Thai',
            'south asian': 'Indian',
            'east asian': 'Chinese',
            'central asian': 'Indian',
            'african': 'Moroccan',
            'north african': 'Moroccan',
            'west african': 'Nigerian',
            'east african': 'Ethiopian',
            'southern african': 'South African',
            'oceanic': 'Australian',
            'polynesian': 'Hawaiian',
            'pacific islander': 'Hawaiian',
            'middle eastern': 'Lebanese',
            'international': 'American',  # Default to American for truly global dishes
            'fusion': 'American',         # Default to American for fusion
            'global': 'American',         # Default to American for global
            'western': 'American',
            'other': 'American',
        }
        
        # Common dish to cuisine mappings (checked first)
        DISH_CUISINE_MAP = {
            # British
            'shortbread': 'British',
            'scone': 'British',
            'trifle': 'British',
            'fish and chips': 'British',
            'shepherd': 'British',  # shepherd's pie
            'yorkshire pudding': 'British',
            
            # Italian
            'pasta': 'Italian',
            'risotto': 'Italian',
            'bruschetta': 'Italian',
            'tiramisu': 'Italian',
            'osso buco': 'Italian',
            'risi e bisi': 'Italian',
            
            # French
            'ratatouille': 'French',
            'quiche': 'French',
            'soufflé': 'French',
            'coq au vin': 'French',
            'bouillabaisse': 'French',
            'tarte tatin': 'French',
            
            # Japanese
            'sushi': 'Japanese',
            'ramen': 'Japanese',
            'tempura': 'Japanese',
            'teriyaki': 'Japanese',
            'udon': 'Japanese',
            'miso': 'Japanese',
            
            # Add more dish-specific mappings here
        }
        
        # Common ingredient to cuisine mappings
        INGREDIENT_CUISINE_MAP = {
            # Italian
            'pasta': 'Italian', 'risotto': 'Italian', 'pesto': 'Italian', 'pancetta': 'Italian',
            'prosciutto': 'Italian', 'mozzarella': 'Italian', 'parmesan': 'Italian',
            'bruschetta': 'Italian', 'tiramisu': 'Italian',
            
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
            'hummus': 'Greek', 'falafel': 'Greek', 'tzatziki': 'Greek',
            'tabbouleh': 'Greek', 'pita': 'Greek', 'baba ghanoush': 'Greek',
            
            # American
            'burger': 'American', 'hot dog': 'American', 'barbecue': 'American',
            'mac and cheese': 'American', 'apple pie': 'American', 'fried chicken': 'American',
            'biscuits and gravy': 'American', 'cornbread': 'American',
            'grits': 'American', 'jambalaya': 'American', 'gumbo': 'American',
            'biscuits': 'American', 'fried green tomatoes': 'American'
        }
        
        # Common category to cuisine mappings
        CATEGORY_CUISINE_MAP = {
            'pasta': 'Italian', 'pizza': 'Italian', 'risotto': 'Italian',
            'taco': 'Mexican', 'burrito': 'Mexican', 'enchilada': 'Mexican',
            'curry': 'Indian', 'biryani': 'Indian', 'tikka': 'Indian',
            'dumpling': 'Chinese', 'noodle': 'Chinese', 'stir-fry': 'Chinese',
            'sushi': 'Japanese', 'ramen': 'Japanese', 'tempura': 'Japanese',
            'pad thai': 'Thai', 'tom yum': 'Thai', 'green curry': 'Thai',
            'ratatouille': 'French', 'quiche': 'French', 'crepe': 'French'
        }
        
        # Handle None or empty cuisine
        if not cuisine or not isinstance(cuisine, str) or not cuisine.strip() or cuisine.lower().strip() in ['none', 'null']:
            if recipe:
                # First try to detect from dish name
                title = recipe.get('title', '').lower()
                for dish, dish_cuisine in DISH_CUISINE_MAP.items():
                    if dish in title:
                        return dish_cuisine
                # Then try ingredients
                detected = self._detect_cuisine_from_ingredients(recipe)
                if detected and detected.lower() in CUISINE_TO_COUNTRY:
                    return CUISINE_TO_COUNTRY[detected.lower()]
            return 'American'  # Default fallback
            
        # Clean and normalize the cuisine string
        cuisine = cuisine.strip().lower()
        
        # Check if it's already a specific country cuisine
        if cuisine in self.VALID_CUISINES:
            return cuisine
            
        # Check if it's a known cuisine that needs mapping to a country
        if cuisine in CUISINE_TO_COUNTRY:
            return CUISINE_TO_COUNTRY[cuisine]
            
        # Check if it's in our dish mapping
        if recipe:
            title = recipe.get('title', '').lower()
            for dish, dish_cuisine in DISH_CUISINE_MAP.items():
                if dish in title:
                    return dish_cuisine
                    
        # Try to detect from ingredients as last resort
        if recipe:
            detected = self._detect_cuisine_from_ingredients(recipe)
            if detected and detected.lower() in CUISINE_TO_COUNTRY:
                return CUISINE_TO_COUNTRY[detected.lower()]
                
        # If we still don't have a match, default to American
        return 'American'
    
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