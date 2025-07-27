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
        
        return similar_recipes[:limit]
    
    def get_recipe_recommendations(self, user_preferences: Dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
        """
        Get personalized recipe recommendations based on user preferences
        """
        # Create a query based on user preferences
        query_parts = []
        
        # Get and normalize favorite cuisines
        favorite_cuisines = set()
        if user_preferences.get("favoriteCuisines"):
            favorite_cuisines = {
                self._normalize_cuisine(cuisine) 
                for cuisine in user_preferences["favoriteCuisines"]
                if self._normalize_cuisine(cuisine)  # Only include valid cuisines
            }
            
            if favorite_cuisines:
                query_parts.append(f"cuisine: {', '.join(favorite_cuisines)}")
        
        # Add other preferences to the query
        if user_preferences.get("cookingSkillLevel"):
            query_parts.append(f"difficulty: {user_preferences['cookingSkillLevel']}")
        
        if user_preferences.get("dietaryRestrictions"):
            query_parts.append(f"dietary: {', '.join(user_preferences['dietaryRestrictions'])}")
        
        if user_preferences.get("healthGoals"):
            query_parts.append(f"healthy: {', '.join(user_preferences['healthGoals'])}")
        
        # If we have favorite cuisines, boost their importance in the search
        if favorite_cuisines:
            for cuisine in favorite_cuisines:
                query_parts.append(cuisine)  # Add cuisine as a standalone term for better matching
        
        query = " ".join(query_parts) if query_parts else "popular delicious recipes"
        
        # Build filters
        filters = {}
        if "vegetarian" in user_preferences.get("dietaryRestrictions", []):
            filters["is_vegetarian"] = True
        if "vegan" in user_preferences.get("dietaryRestrictions", []):
            filters["is_vegan"] = True
        if "gluten-free" in user_preferences.get("dietaryRestrictions", []):
            filters["is_gluten_free"] = True
        
        # Perform semantic search with a higher limit to ensure we get enough results
        results = self.semantic_search(query, filters, limit * 3)  # Overfetch more to ensure quality

        # Filter out recipes with empty or invalid cuisines if we have favorite cuisines
        if favorite_cuisines:
            valid_results = []
            other_results = []
            
            for recipe in results:
                # Pass the entire recipe for better cuisine detection
                recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe)
                if not recipe_cuisine:
                    # If we can't determine a valid cuisine, skip or add to other results
                    other_results.append(recipe)
                    continue
                    
                # Update the recipe's cuisine with the normalized version
                recipe['cuisine'] = recipe_cuisine
                
                if recipe_cuisine in favorite_cuisines:
                    valid_results.append(recipe)
                else:
                    other_results.append(recipe)
            
            # If we have enough matches from favorite cuisines, return them
            if len(valid_results) >= limit:
                return valid_results[:limit]
                
            # Otherwise, fill the remaining slots with other results
            remaining_slots = limit - len(valid_results)
            return valid_results + other_results[:remaining_slots]
            
        # If no favorite cuisines, return top results with valid cuisines
        filtered_results = []
        for recipe in results[:limit]:
            # Pass the entire recipe for better cuisine detection
            recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe)
            if recipe_cuisine:
                # Update the recipe's cuisine with the normalized version
                recipe['cuisine'] = recipe_cuisine
                filtered_results.append(recipe)
                
        return filtered_results

    
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
        Normalize and validate cuisine string
        
        Args:
            cuisine: The cuisine string to normalize
            recipe: Optional recipe dictionary for additional context
            
        Returns:
            Normalized cuisine string or empty string if invalid
        """
        if not cuisine or not isinstance(cuisine, str):
            if recipe:
                # Try to detect cuisine from recipe details if no cuisine provided
                detected = self._detect_cuisine_from_ingredients(recipe)
                if detected:
                    return detected
            return ""
            
        # Common cuisine normalization
        cuisine = cuisine.lower().strip()
        
        # Map common variations to standard names
        cuisine_map = {
            'american': ['american', 'usa', 'united states', 'us'],
            'italian': ['italian', 'italy'],
            'mexican': ['mexican', 'mexico'],
            'chinese': ['chinese', 'china'],
            'indian': ['indian', 'india'],
            'thai': ['thai', 'thailand'],
            'japanese': ['japanese', 'japan'],
            'french': ['french', 'france'],
            'mediterranean': ['mediterranean', 'mediterranean'],
            'greek': ['greek', 'greece'],
            'spanish': ['spanish', 'spain'],
            'vietnamese': ['vietnamese', 'vietnam'],
            'korean': ['korean', 'korea']
        }
        
        # Check for matches in the map
        for standard_name, variations in cuisine_map.items():
            if cuisine in variations:
                return standard_name
                
        # If we have a recipe and cuisine is not recognized, try to detect from ingredients
        if recipe and cuisine in ['international', 'fusion', 'global', '']:
            detected = self._detect_cuisine_from_ingredients(recipe)
            if detected:
                return detected
                
        # If still no match, return empty string for invalid cuisines
        return "" if cuisine in ['international', 'fusion', 'global', ''] else cuisine
        
    def _create_searchable_text(self, recipe: Dict[str, Any]) -> str:
        """
        Create a rich text representation of the recipe for embedding
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