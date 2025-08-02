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
    
    # Define valid cuisines for proper filtering
    VALID_CUISINES = [
        'american', 'british', 'canadian', 'chinese', 'dutch', 'french', 'greek', 
        'indian', 'irish', 'italian', 'jamaican', 'japanese', 'kenyan', 'malaysian', 
        'mexican', 'moroccan', 'russian', 'spanish', 'thai', 'tunisian', 'turkish', 
        'vietnamese', 'lebanese', 'polish', 'german', 'swedish', 'lithuanian', 
        'ethiopian', 'nigerian', 'south african', 'brazilian', 'australian', 
        'hawaiian', 'north african', 'west african', 'east african', 'southern african',
        'mediterranean'
    ]
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        # Use the same collection as RecipeCacheService which is working
        self.recipe_collection = self.client.get_collection("recipe_details_cache")
        print("Using recipe_details_cache collection for search")
        
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
            "cuisine": self._normalize_cuisine(recipe.get("cuisine", "")), # Use normalized cuisine
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
                ids=[str(recipe.get('id'))],  # Use recipe ID directly, not prefixed
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
            print(f"Searching with query: '{expanded_query}'")
            print(f"Where clause: {where_clause}")
            
            # First, try to get all documents to see what's available
            all_docs = self.recipe_collection.get(limit=5)
            print(f"Collection has {len(all_docs['documents'])} documents available")
            
            # Show sample documents to debug
            if all_docs['documents']:
                print("Sample documents:")
                for i, (doc, metadata) in enumerate(zip(all_docs['documents'], all_docs['metadatas'])):
                    print(f"  Doc {i+1}: {metadata.get('name', 'No name')} - {doc[:100]}...")
            
            # Try multiple search strategies
            results = None
            
            # Strategy 1: Try the expanded query
            try:
                results = self.recipe_collection.query(
                    query_texts=[expanded_query],
                    n_results=min(limit * 3, 1000),
                    where=where_clause if where_clause else None,
                    include=['documents', 'metadatas', 'distances']
                )
                print(f"Strategy 1 (expanded query) found {len(results['documents'][0]) if results and results['documents'] else 0} results")
            except Exception as e:
                print(f"Strategy 1 failed: {e}")
            
            # Strategy 2: If no results, try the original query
            if not results or not results['documents'] or len(results['documents'][0]) == 0:
                try:
                    results = self.recipe_collection.query(
                        query_texts=[query],
                        n_results=min(limit * 3, 1000),
                        where=where_clause if where_clause else None,
                        include=['documents', 'metadatas', 'distances']
                    )
                    print(f"Strategy 2 (original query) found {len(results['documents'][0]) if results and results['documents'] else 0} results")
                except Exception as e:
                    print(f"Strategy 2 failed: {e}")
            
            # Strategy 3: If still no results, try a generic search
            if not results or not results['documents'] or len(results['documents'][0]) == 0:
                try:
                    results = self.recipe_collection.query(
                        query_texts=["recipe"],
                        n_results=min(limit * 3, 1000),
                        where=where_clause if where_clause else None,
                        include=['documents', 'metadatas', 'distances']
                    )
                    print(f"Strategy 3 (generic search) found {len(results['documents'][0]) if results and results['documents'] else 0} results")
                except Exception as e:
                    print(f"Strategy 3 failed: {e}")
            
            # Strategy 4: If still no results, try without any filters
            if not results or not results['documents'] or len(results['documents'][0]) == 0:
                try:
                    results = self.recipe_collection.query(
                        query_texts=[expanded_query],
                        n_results=min(limit * 3, 1000),
                        include=['documents', 'metadatas', 'distances']
                    )
                    print(f"Strategy 4 (no filters) found {len(results['documents'][0]) if results and results['documents'] else 0} results")
                except Exception as e:
                    print(f"Strategy 4 failed: {e}")
            
            # Strategy 5: If still no results, try with just the first word of the query
            if not results or not results['documents'] or len(results['documents'][0]) == 0:
                try:
                    first_word = query.split()[0] if query else "recipe"
                    results = self.recipe_collection.query(
                        query_texts=[first_word],
                        n_results=min(limit * 3, 1000),
                        include=['documents', 'metadatas', 'distances']
                    )
                    print(f"Strategy 5 (first word: {first_word}) found {len(results['documents'][0]) if results and results['documents'] else 0} results")
                except Exception as e:
                    print(f"Strategy 5 failed: {e}")
            
            if not results or not results['documents'] or len(results['documents'][0]) == 0:
                print("All search strategies failed - no results found")
                return []
            
            print(f"Final search found {len(results['documents'][0])} results")
            
            # Process and rank results
            processed_results = []
            for i, doc in enumerate(results['documents'][0]):
                try:
                    metadata = results['metadatas'][0][i]
                    base_score = 1 - results['distances'][0][i]  # Convert distance to similarity
                    
                    # Try to parse the document as JSON first
                    recipe_data = {}
                    try:
                        if doc.startswith('{'):
                            # Parse JSON document
                            doc_recipe = json.loads(doc)
                            recipe_data = {
                                'id': doc_recipe.get('id', metadata.get('recipe_id', '')),
                                'name': doc_recipe.get('name', doc_recipe.get('title', '')),
                                'title': doc_recipe.get('title', doc_recipe.get('name', '')),
                                'cuisine': doc_recipe.get('cuisine', ''),
                                'description': doc_recipe.get('description', ''),
                                'ingredients': doc_recipe.get('ingredients', []),
                                'instructions': doc_recipe.get('instructions', ''),
                                'difficulty': doc_recipe.get('difficulty', ''),
                                'meal_type': doc_recipe.get('mealType', ''),
                                'cooking_time': doc_recipe.get('cookingTime', ''),
                                'calories': doc_recipe.get('nutrition', {}).get('calories', 0),
                                'protein': doc_recipe.get('nutrition', {}).get('protein', 0),
                                'servings': doc_recipe.get('servings', 0),
                                'avg_rating': doc_recipe.get('avg_rating', 0),
                                'ingredient_count': len(doc_recipe.get('ingredients', [])),
                                'is_vegetarian': "vegetarian" in doc_recipe.get('dietaryRestrictions', []),
                                'is_vegan': "vegan" in doc_recipe.get('dietaryRestrictions', []),
                                'is_gluten_free': "gluten-free" in doc_recipe.get('dietaryRestrictions', []),
                                'similarity_score': base_score,
                                # Add missing fields with proper image handling
                                'image': doc_recipe.get('image', doc_recipe.get('imageUrl', '')),
                                'imageUrl': doc_recipe.get('imageUrl', doc_recipe.get('image', '')),
                                'dietaryRestrictions': doc_recipe.get('dietaryRestrictions', []),
                                'cuisines': doc_recipe.get('cuisines', [doc_recipe.get('cuisine', '')]),
                                'diets': doc_recipe.get('diets', []),
                                'readyInMinutes': doc_recipe.get('readyInMinutes', doc_recipe.get('cookingTime', 30)),
                                'ready_in_minutes': doc_recipe.get('readyInMinutes', doc_recipe.get('cookingTime', 30)),
                                'sourceUrl': doc_recipe.get('sourceUrl', ''),
                                'summary': doc_recipe.get('summary', doc_recipe.get('description', '')),
                                # Add additional fields for better frontend compatibility
                                'strMeal': doc_recipe.get('strMeal', doc_recipe.get('name', '')),
                                'strMealThumb': doc_recipe.get('strMealThumb', doc_recipe.get('image', '')),
                                'strInstructions': doc_recipe.get('strInstructions', doc_recipe.get('instructions', '')),
                                'strCategory': doc_recipe.get('strCategory', doc_recipe.get('cuisine', '')),
                                'strArea': doc_recipe.get('strArea', doc_recipe.get('cuisine', ''))
                            }
                        else:
                            # Fallback to metadata-based recipe data
                            recipe_data = {
                                'id': metadata.get('recipe_id', metadata.get('id', '')),
                                'name': metadata.get('name', metadata.get('title', '')),
                                'title': metadata.get('name', metadata.get('title', '')),
                                'cuisine': metadata.get('cuisine', ''),
                                'description': doc[:200] + '...' if len(doc) > 200 else doc,
                                'difficulty': metadata.get('difficulty', ''),
                                'meal_type': metadata.get('meal_type', ''),
                                'cooking_time': metadata.get('cooking_time', ''),
                                'calories': metadata.get('calories', 0),
                                'protein': metadata.get('protein', 0),
                                'servings': metadata.get('servings', 0),
                                'avg_rating': metadata.get('avg_rating', 0),
                                'ingredient_count': metadata.get('ingredient_count', 0),
                                'is_vegetarian': metadata.get('is_vegetarian', False),
                                'is_vegan': metadata.get('is_vegan', False),
                                'is_gluten_free': metadata.get('is_gluten_free', False),
                                'similarity_score': base_score,
                                # Add missing fields with better defaults
                                'image': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=400&h=300&q=80',
                                'imageUrl': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=400&h=300&q=80',
                                'dietaryRestrictions': [],
                                'cuisines': [metadata.get('cuisine', '')],
                                'diets': [],
                                'readyInMinutes': 30,
                                'ready_in_minutes': 30,
                                'sourceUrl': '',
                                'summary': doc[:200] + '...' if len(doc) > 200 else doc
                            }
                    except json.JSONDecodeError:
                        # If JSON parsing fails, use metadata-based approach
                        recipe_data = {
                            'id': metadata.get('recipe_id', metadata.get('id', '')),
                            'name': metadata.get('name', metadata.get('title', '')),
                            'title': metadata.get('name', metadata.get('title', '')),
                            'cuisine': metadata.get('cuisine', ''),
                            'description': doc[:200] + '...' if len(doc) > 200 else doc,
                            'difficulty': metadata.get('difficulty', ''),
                            'meal_type': metadata.get('meal_type', ''),
                            'cooking_time': metadata.get('cooking_time', ''),
                            'calories': metadata.get('calories', 0),
                            'protein': metadata.get('protein', 0),
                            'servings': metadata.get('servings', 0),
                            'avg_rating': metadata.get('avg_rating', 0),
                            'ingredient_count': metadata.get('ingredient_count', 0),
                            'is_vegetarian': metadata.get('is_vegetarian', False),
                            'is_vegan': metadata.get('is_vegan', False),
                            'is_gluten_free': metadata.get('is_gluten_free', False),
                            'similarity_score': base_score,
                            # Add missing fields with better defaults
                            'image': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=400&h=300&q=80',
                            'imageUrl': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=400&h=300&q=80',
                            'dietaryRestrictions': [],
                            'cuisines': [metadata.get('cuisine', '')],
                            'diets': [],
                            'readyInMinutes': 30,
                            'ready_in_minutes': 30,
                            'sourceUrl': '',
                            'summary': doc[:200] + '...' if len(doc) > 200 else doc
                        }
                    
                    # Calculate final ranking score incorporating multiple factors
                    final_score = self._calculate_ranking_score(
                        base_score=base_score,
                        metadata=metadata,
                        query=query  # Use original query for ranking
                    )
                    
                    recipe_data["similarity_score"] = final_score
                    processed_results.append(recipe_data)
                    
                except Exception as e:
                    print(f"Error processing result {i}: {e}")
                    continue
            
            # Sort by final score and return top results
            processed_results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            return processed_results[:limit]
            
        except Exception as e:
            print(f"Error during semantic search: {e}")
            import traceback
            traceback.print_exc()
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
            ids=[str(recipe_id)],  # Use recipe ID directly, not prefixed
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
        favorite_foods = [f.lower() for f in user_preferences.get("favoriteFoods", []) if f]
        favorite_cuisines = set(self._normalize_cuisine(c, None).lower() for c in user_preferences.get("favoriteCuisines", []) if c)
        foods_to_avoid = set(f.lower() for f in user_preferences.get("foodsToAvoid", []) if f)
        dietary_restrictions = [d.lower() for d in user_preferences.get("dietaryRestrictions", [])]

        print(f"User selected cuisines: {favorite_cuisines}")
        print(f"User favorite foods: {favorite_foods}")

        filters = {}
        if "vegetarian" in dietary_restrictions:
            filters["is_vegetarian"] = True
        if "vegan" in dietary_restrictions:
            filters["is_vegan"] = True
        if "gluten-free" in dietary_restrictions:
            filters["is_gluten_free"] = True

        # Define helper functions first
        def has_fav_food(recipe):
            if not recipe:
                return False
                
            # Get all searchable text from the recipe
            text_parts = [
                str(recipe.get('name', '') or ''),
                str(recipe.get('title', '') or ''),
                str(recipe.get('description', '') or ''),
                str(recipe.get('cuisine', '') or '')
            ]
            
            # Also check ingredients if available
            ingredients = recipe.get('ingredients', [])
            if ingredients:
                for ing in ingredients:
                    if isinstance(ing, dict):
                        if 'name' in ing:
                            text_parts.append(str(ing['name']))
                        elif 'ingredient' in ing:
                            text_parts.append(str(ing['ingredient']))
                    else:
                        text_parts.append(str(ing))
            
            # Create a single lowercase string for searching
            search_text = ' '.join(text_parts).lower()
            
            # Check each favorite food
            for food in favorite_foods:
                if not food:  # Skip empty foods
                    continue
                    
                # Check for exact word matches
                if f' {food} ' in f' {search_text} ' or \
                   search_text.startswith(f'{food} ') or \
                   search_text.endswith(f' {food}') or \
                   search_text == food:
                    return True
                    
                # Check for partial matches (for foods like "burger" in "hamburger")
                if food in search_text:
                    return True
                    
                # Also check for plural/singular forms
                if food.endswith('s') and (f' {food[:-1]} ' in f' {search_text} ' or
                                         search_text.startswith(f'{food[:-1]} ')):
                    return True
                    
                # Check for common variations
                if food == 'burger':
                    if 'hamburger' in search_text or 'beef' in search_text or 'patty' in search_text:
                        return True
                        
            return False

        def in_fav_cuisine(recipe):
            if not recipe or not favorite_cuisines:
                return False
                
            # Try multiple ways to get cuisine
            recipe_cuisine = ''
            
            # First try the normalized cuisine field
            if recipe.get('cuisine'):
                recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe).lower()
            
            # If no cuisine found, try cuisines array
            if not recipe_cuisine and recipe.get('cuisines'):
                cuisines = recipe.get('cuisines', [])
                if isinstance(cuisines, list) and cuisines:
                    for cuisine in cuisines:
                        if cuisine:
                            recipe_cuisine = self._normalize_cuisine(cuisine, recipe).lower()
                            if recipe_cuisine:
                                break
            
            # If still no cuisine, try to detect from recipe content
            if not recipe_cuisine:
                recipe_cuisine = self._detect_cuisine_from_ingredients(recipe).lower()
            
            # Check if any favorite cuisine matches
            for fav_cuisine in favorite_cuisines:
                if fav_cuisine and fav_cuisine.lower() == recipe_cuisine:
                    return True
                    
                # For broad cuisines like "International", be more flexible
                if fav_cuisine.lower() in ['international', 'global', 'world', 'fusion']:
                    # If the recipe has any recognizable cuisine, it's considered "international"
                    if recipe_cuisine and recipe_cuisine not in ['', 'none', 'unknown', 'n/a']:
                        return True
                        
            return False

        def has_foods_to_avoid(recipe):
            if not recipe or not foods_to_avoid:
                return False
            # Get all searchable text from the recipe
            text_parts = [
                str(recipe.get('name', '') or ''),
                str(recipe.get('title', '') or ''),
                str(recipe.get('description', '') or ''),
                str(recipe.get('cuisine', '') or '')
            ]
            
            # Create a single lowercase string for searching
            search_text = ' '.join(text_parts).lower()
            
            # Check each food to avoid
            for food in foods_to_avoid:
                if not food:  # Skip empty foods
                    continue
                if food in search_text:
                    return True
            return False

        def count_matching_foods(recipe):
            if not recipe:
                return 0
                
            count = 0
            # Get all searchable text from the recipe
            text_parts = [
                str(recipe.get('name', '') or ''),
                str(recipe.get('title', '') or ''),
                str(recipe.get('description', '') or ''),
                str(recipe.get('cuisine', '') or '')
            ]
            
            # Also check ingredients if available
            ingredients = recipe.get('ingredients', [])
            if ingredients:
                for ing in ingredients:
                    if isinstance(ing, dict):
                        if 'name' in ing:
                            text_parts.append(str(ing['name']))
                        elif 'ingredient' in ing:
                            text_parts.append(str(ing['ingredient']))
                    else:
                        text_parts.append(str(ing))
            
            # Create a single lowercase string for searching
            search_text = ' '.join(text_parts).lower()
            
            # Check each favorite food
            for food in favorite_foods:
                if not food:  # Skip empty foods
                    continue
                    
                # Check for exact word matches
                if f' {food} ' in f' {search_text} ' or \
                   search_text.startswith(f'{food} ') or \
                   search_text.endswith(f' {food}') or \
                   search_text == food:
                    count += 1
                    continue
                    
                # Check for partial matches (for foods like "burger" in "hamburger")
                if food in search_text:
                    count += 1
                    continue
                    
                # Also check for plural/singular forms
                if food.endswith('s') and (f' {food[:-1]} ' in f' {search_text} ' or
                                         search_text.startswith(f'{food[:-1]} ')):
                    count += 1
                    continue
                    
                # Check for common variations
                if food == 'burger':
                    if 'hamburger' in search_text or 'beef' in search_text or 'patty' in search_text:
                        count += 1
                        continue
                    
            return count
        
        # Always search for favorite foods first if present
        if favorite_foods:
            print(f"Searching for favorite foods: {favorite_foods}")
            # Build a query that looks for any of the favorite foods
            # Use space-separated format instead of OR operators for ChromaDB
            query = " ".join(favorite_foods)
            print(f"Food search query: {query}")
            
            # Get more candidates since we're searching for specific foods
            candidates = self.semantic_search(query, filters, limit * 30)
            print(f"Found {len(candidates)} candidates with favorite foods")
            
            # If no results, try searching for each food individually
            if not candidates:
                print("No results with combined search, trying individual food searches...")
                for food in favorite_foods:
                    food_candidates = self.semantic_search(food, filters, limit * 10)
                    candidates.extend(food_candidates)
                    print(f"Found {len(food_candidates)} candidates for '{food}'")
            
            # Filter to only include recipes that actually contain at least one favorite food
            candidates = [r for r in candidates if has_fav_food(r)]
            print(f"After filtering for actual food matches: {len(candidates)} candidates")
            
        # If we have cuisines, also search within those cuisines
        elif favorite_cuisines:
            # Check if any of the cuisines are "International" or similar broad terms
            has_broad_cuisine = any(c.lower() in ['international', 'global', 'world', 'fusion'] for c in favorite_cuisines)
            
            if has_broad_cuisine:
                # For broad cuisines like "International", get popular recipes
                print(f"Broad cuisine detected, getting popular recipes")
                candidates = self.semantic_search("popular recipes", filters, limit * 10)
            else:
                # Search for each selected cuisine separately to ensure we get recipes from those cuisines
                all_candidates = []
                for cuisine in favorite_cuisines:
                    print(f"Searching for recipes in cuisine: {cuisine}")
                    # Search with cuisine-specific terms
                    search_terms = [cuisine]  # Use simple terms instead of quoted terms
                    
                    query = " ".join(search_terms)
                    print(f"Cuisine search query: {query}")
                    cuisine_candidates = self.semantic_search(query, filters, limit * 10)
                    
                    # More flexible cuisine matching - include recipes that match the cuisine
                    filtered_candidates = []
                    for recipe in cuisine_candidates:
                        recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe).lower()
                        
                        # Check for exact match
                        if recipe_cuisine == cuisine:
                            filtered_candidates.append(recipe)
                            continue
                            
                        # Check for partial match (e.g., "spanish" in "spanish paella")
                        if cuisine in recipe_cuisine or recipe_cuisine in cuisine:
                            filtered_candidates.append(recipe)
                            continue
                            
                        # Check if the recipe title/name contains the cuisine
                        recipe_name = (recipe.get('name', '') or recipe.get('title', '')).lower()
                        if cuisine in recipe_name:
                            filtered_candidates.append(recipe)
                            continue
                            
                        # Check if the recipe description contains the cuisine
                        recipe_desc = (recipe.get('description', '')).lower()
                        if cuisine in recipe_desc:
                            filtered_candidates.append(recipe)
                            continue
                            
                        # For broad cuisines like "International", include any recipe with a recognizable cuisine
                        if cuisine.lower() in ['international', 'global', 'world', 'fusion']:
                            if recipe_cuisine and recipe_cuisine not in ['', 'none', 'unknown', 'n/a']:
                                filtered_candidates.append(recipe)
                                continue
                    
                    print(f"Found {len(filtered_candidates)} recipes from {cuisine} cuisine")
                    all_candidates.extend(filtered_candidates)
                
                candidates = all_candidates
        else:
            # If no cuisines or favorite foods, just get popular recipes
            print("No specific preferences, getting popular recipes")
            query = "popular recipes"
            candidates = self.semantic_search(query, filters, limit * 10)
            
        # If we have BOTH favorite foods AND cuisines, also search for foods across all cuisines
        if favorite_foods and favorite_cuisines:
            print(f"User has both favorite foods and cuisines, also searching for foods: {favorite_foods}")
            
            # Search for favorite foods across all cuisines
            food_query = " ".join(favorite_foods)
            food_candidates = self.semantic_search(food_query, filters, limit * 20)
            print(f"Found {len(food_candidates)} candidates for favorite foods across all cuisines")
            
            # Filter for actual food matches
            food_candidates = [r for r in food_candidates if has_fav_food(r)]
            print(f"After filtering for actual food matches: {len(food_candidates)} candidates")
            
            # Combine with existing candidates, prioritizing food matches
            all_candidates = food_candidates + candidates
            
            # Remove duplicates while preserving order
            seen_ids = set()
            unique_candidates = []
            for candidate in all_candidates:
                candidate_id = candidate.get('id', candidate.get('recipe_id', ''))
                if candidate_id not in seen_ids:
                    seen_ids.add(candidate_id)
                    unique_candidates.append(candidate)
            
            candidates = unique_candidates
            print(f"Combined candidates (foods + cuisines): {len(candidates)}")

        print(f"Total candidates after cuisine filtering: {len(candidates)}")

        # Remove foods to avoid first
        candidates = [r for r in candidates if not has_foods_to_avoid(r)]
        print(f"Candidates after removing foods to avoid: {len(candidates)}")

        # Score each recipe based on multiple factors
        def score_recipe(recipe):
            if not recipe:
                return 0
                
            score = 0
            
            # Medium priority: matching favorite foods (reduced from 5 to 3 points)
            food_matches = count_matching_foods(recipe)
            score += food_matches * 3  # Reduced from 5 to 3 points per matching favorite food
            
            # Medium priority: matching cuisine (increased from 3 to 4 points)
            if favorite_cuisines and in_fav_cuisine(recipe):
                score += 4  # Increased from 3 to 4 points for cuisine matches
            
            # If we only have favorite foods (no cuisines), give a small boost
            if not favorite_cuisines and favorite_foods:
                score += 5  # Reduced from 10 to 5 points
                
                # Extra boost if multiple favorite foods match
                if food_matches > 1:
                    score += (food_matches - 1) * 2  # Reduced from 3 to 2 points
            
            # Bonus for food matches in title/name (reduced from 3 to 2 points)
            title = str(recipe.get('title', '') or '') + ' ' + str(recipe.get('name', '') or '')
            title = title.lower()
            for food in favorite_foods:
                if food and food in title:
                    score += 2  # Reduced from 3 to 2 points for title matches
                    # Extra bonus if multiple foods in title
                    if food_matches > 1:
                        score += 1
                    break
            
            return score
        
        # Sort candidates by score (highest first)
        candidates.sort(key=score_recipe, reverse=True)
        
        # Get unique recipes by ID, maintaining score-based order
        seen = set()
        recommendations = []
        for r in candidates:
            rid = r.get('recipe_id') or r.get('id')
            if rid and rid not in seen:
                recommendations.append(r)
                seen.add(rid)
        
        # Implement fair distribution across cuisines
        if favorite_cuisines and not favorite_foods:
            print(f"Implementing fair distribution across {len(favorite_cuisines)} cuisines")
            
            # Group recipes by cuisine
            cuisine_groups = {}
            for recipe in recommendations:
                recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe).lower()
                
                # Find which favorite cuisine this recipe matches
                matched_cuisine = None
                for fav_cuisine in favorite_cuisines:
                    if (recipe_cuisine == fav_cuisine.lower() or 
                        fav_cuisine.lower() in recipe_cuisine or 
                        recipe_cuisine in fav_cuisine.lower()):
                        matched_cuisine = fav_cuisine
                        break
                
                if matched_cuisine:
                    if matched_cuisine not in cuisine_groups:
                        cuisine_groups[matched_cuisine] = []
                    cuisine_groups[matched_cuisine].append(recipe)
            
            # Calculate how many recipes per cuisine
            recipes_per_cuisine = max(1, limit // len(favorite_cuisines))
            print(f"Target: {recipes_per_cuisine} recipes per cuisine")
            
            # Build fair distribution
            fair_recommendations = []
            cuisine_index = 0
            
            # Round-robin distribution
            while len(fair_recommendations) < limit and cuisine_index < recipes_per_cuisine * len(favorite_cuisines):
                for cuisine in favorite_cuisines:
                    if cuisine in cuisine_groups and len(cuisine_groups[cuisine]) > 0:
                        # Take the highest scored recipe from this cuisine
                        best_recipe = max(cuisine_groups[cuisine], key=score_recipe)
                        fair_recommendations.append(best_recipe)
                        cuisine_groups[cuisine].remove(best_recipe)
                        
                        if len(fair_recommendations) >= limit:
                            break
                
                cuisine_index += 1
            
            # If we don't have enough recipes, fill with remaining high-scored recipes
            remaining_recipes = []
            for cuisine_recipes in cuisine_groups.values():
                remaining_recipes.extend(cuisine_recipes)
            
            remaining_recipes.sort(key=score_recipe, reverse=True)
            fair_recommendations.extend(remaining_recipes[:limit - len(fair_recommendations)])
            
            recommendations = fair_recommendations
            print(f"Fair distribution complete: {len(recommendations)} recipes")
            
            # Log distribution
            cuisine_counts = {}
            for recipe in recommendations:
                recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe).lower()
                for fav_cuisine in favorite_cuisines:
                    if (recipe_cuisine == fav_cuisine.lower() or 
                        fav_cuisine.lower() in recipe_cuisine or 
                        recipe_cuisine in fav_cuisine.lower()):
                        cuisine_counts[fav_cuisine] = cuisine_counts.get(fav_cuisine, 0) + 1
                        break
            
            print(f"Final distribution by cuisine: {cuisine_counts}")
        
        # Debug: Print top 10 scored recipes
        print("\nTop 10 Scored Recipes:")
        for i, r in enumerate(recommendations[:10], 1):
            rid = r.get('recipe_id') or r.get('id')
            title = r.get('title', 'No title')
            cuisine = self._normalize_cuisine(r.get('cuisine', ''), r)
            score = score_recipe(r)
            print(f"{i}. {title} | Cuisine: {cuisine} | Score: {score}")
            
            # Debug: Show searchable text for top recipes
            if i <= 5:
                # Get the actual recipe data for debugging
                recipe_name = r.get('name', '') or r.get('title', '')
                recipe_description = r.get('description', '')
                recipe_ingredients = r.get('ingredients', [])
                
                # Create searchable text from actual recipe data
                text_parts = [
                    str(recipe_name),
                    str(recipe_description)
                ]
                
                # Add ingredients if available
                if recipe_ingredients:
                    for ing in recipe_ingredients:
                        if isinstance(ing, dict):
                            if 'name' in ing:
                                text_parts.append(str(ing['name']))
                            elif 'ingredient' in ing:
                                text_parts.append(str(ing['ingredient']))
                        else:
                            text_parts.append(str(ing))
                
                search_text = ' '.join(text_parts).lower()
                print(f"   Searchable text: {search_text[:100]}...")
                print(f"   Has burger: {'burger' in search_text}")
                print(f"   Has beef: {'beef' in search_text}")
                print(f"   Recipe name: {recipe_name}")
                print(f"   Recipe cuisine: {r.get('cuisine', 'N/A')}")
            
            # Show matching favorite foods for top recipes
            if i <= 5:
                matches = []
                for food in favorite_foods:
                    if (food in title.lower() or 
                        any(food in str(ing).lower() for ing in r.get('ingredients', []))):
                        matches.append(food)
                if matches:
                    print(f"   Matching foods: {', '.join(matches)}")
        
        # Remove duplicates while preserving order
        seen = set()
        final = []
        for r in recommendations:
            rid = r.get('recipe_id') or r.get('id')
            if rid and rid not in seen:
                final.append(r)
                seen.add(rid)
            if len(final) >= limit:
                break
        
        # Debug logging - categorize recommendations
        both = []
        food_only = []
        cuisine_only = []
        others = []
        
        for r in final:
            has_food = has_fav_food(r) if favorite_foods else False
            has_cuisine = in_fav_cuisine(r) if favorite_cuisines else False
            
            if has_food and has_cuisine:
                both.append(r)
            elif has_food:
                food_only.append(r)
            elif has_cuisine:
                cuisine_only.append(r)
            else:
                others.append(r)
        
        print(f"Recommendations breakdown:")
        print(f"- Both fav food and cuisine: {len(both)}")
        print(f"- Fav food only: {len(food_only)}")
        print(f"- Fav cuisine only: {len(cuisine_only)}")
        print(f"- Others: {len(others)}")
        print(f"- Final recommendations: {len(final)}")
        
        # Log the cuisines of final recommendations
        if final:
            final_cuisines = {}
            for r in final:
                cuisine = self._normalize_cuisine(r.get('cuisine', ''), r).lower()
                final_cuisines[cuisine] = final_cuisines.get(cuisine, 0) + 1
            print(f"Final recommendations by cuisine: {final_cuisines}")
        
        return final

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
            # Use space-separated format for ChromaDB compatibility
            query_parts.append(" ".join(favorite_foods))
        
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
            # Use space-separated format for ChromaDB compatibility
            query_parts.append(" ".join(meal_types))
            
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
        
    def _normalize_cuisine(self, cuisine: str, recipe: Optional[Dict] = None) -> str:
        """
        Normalize cuisine names to standard format with flexible matching.
        Returns empty string if no clear match is found.
        """
        if not cuisine or not isinstance(cuisine, str):
            return ""
            
        cuisine = cuisine.strip().lower()
        
        # Handle broad/general cuisines
        broad_cuisines = {
            'international': 'International',
            'global': 'Global',
            'world': 'World',
            'fusion': 'Fusion',
            'mixed': 'Mixed',
            'various': 'Various',
            'general': 'General'
        }
        
        # Check for broad cuisines first
        if cuisine in broad_cuisines:
            return broad_cuisines[cuisine]
            
        # Flexible cuisine mappings (exact and partial matches)
        cuisine_mappings = {
            'indian': 'Indian',
            'vietnamese': 'Vietnamese',
            'thai': 'Thai',
            'japanese': 'Japanese',
            'chinese': 'Chinese',
            'italian': 'Italian',
            'mexican': 'Mexican',
            'greek': 'Greek',
            'spanish': 'Spanish',
            'french': 'French',
            'korean': 'Korean',
            'lebanese': 'Lebanese',
            'turkish': 'Turkish',
            'moroccan': 'Moroccan',
            'american': 'American',
            'british': 'British',
            'caribbean': 'Caribbean',
            'mediterranean': 'Mediterranean',
            'middle eastern': 'Middle Eastern',
            'eastern european': 'Eastern European',
            'irish': 'Irish',
            'german': 'German',
            'dutch': 'Dutch',
            'swedish': 'Swedish',
            'polish': 'Polish',
            'russian': 'Russian',
            'brazilian': 'Brazilian',
            'australian': 'Australian',
            'hawaiian': 'Hawaiian',
            'african': 'African',
            'north african': 'North African',
            'west african': 'West African',
            'east african': 'East African',
            'south african': 'South African',
            'southern african': 'Southern African',
            'canadian': 'Canadian',
            'jamaican': 'Jamaican',
            'kenyan': 'Kenyan',
            'malaysian': 'Malaysian',
            'tunisian': 'Tunisian',
            'vietnamese': 'Vietnamese',
            'lithuanian': 'Lithuanian',
            'ethiopian': 'Ethiopian',
            'nigerian': 'Nigerian'
        }
        
        # Check for exact match first
        if cuisine in cuisine_mappings:
            return cuisine_mappings[cuisine]
            
        # Check for partial matches
        for key, value in cuisine_mappings.items():
            if key in cuisine or cuisine in key:
                return value
                
        # Check for specific cuisine markers with high confidence
        if 'pho' in cuisine or 'banh mi' in cuisine or 'viet' in cuisine:
            return 'Vietnamese'
        if 'curry' in cuisine and ('indian' in cuisine or 'masala' in cuisine):
            return 'Indian'
        if 'sushi' in cuisine or 'ramen' in cuisine or 'teriyaki' in cuisine:
            return 'Japanese'
        if 'pad thai' in cuisine or 'tom yum' in cuisine or 'thai' in cuisine:
            return 'Thai'
        if 'taco' in cuisine or 'burrito' in cuisine or 'enchilada' in cuisine:
            return 'Mexican'
        if 'pasta' in cuisine or 'pizza' in cuisine or 'risotto' in cuisine:
            return 'Italian'
        if 'baguette' in cuisine or 'brie' in cuisine or 'provençal' in cuisine:
            return 'French'
        if 'kimchi' in cuisine or 'bulgogi' in cuisine or 'bibimbap' in cuisine:
            return 'Korean'
        if 'paella' in cuisine or 'chorizo' in cuisine or 'tapas' in cuisine:
            return 'Spanish'
        if 'feta' in cuisine or 'tzatziki' in cuisine or 'gyro' in cuisine:
            return 'Greek'
        if 'burger' in cuisine or 'hot dog' in cuisine or 'barbecue' in cuisine:
            return 'American'
            
        # Check for recipe content if available
        if recipe:
            # Get all searchable text
            text = ' '.join([
                str(recipe.get('name', '')),
                str(recipe.get('title', '')),
                str(recipe.get('description', '')),
                ' '.join([ing['name'] if isinstance(ing, dict) and 'name' in ing 
                         else str(ing) for ing in recipe.get('ingredients', [])])
            ]).lower()
            
            # Check for specific cuisine markers in recipe content
            if 'pho' in text or 'banh mi' in text or 'viet' in text:
                return 'Vietnamese'
            if 'curry' in text and ('indian' in text or 'masala' in text):
                return 'Indian'
            if 'sushi' in text or 'ramen' in text or 'teriyaki' in text:
                return 'Japanese'
            if 'pad thai' in text or 'tom yum' in text or 'thai' in text:
                return 'Thai'
            if 'taco' in text or 'burrito' in text or 'enchilada' in text:
                return 'Mexican'
            if 'pasta' in text or 'pizza' in text or 'risotto' in text:
                return 'Italian'
            if 'baguette' in text or 'brie' in text or 'provençal' in text:
                return 'French'
            if 'kimchi' in text or 'bulgogi' in text or 'bibimbap' in text:
                return 'Korean'
            if 'paella' in text or 'chorizo' in text or 'tapas' in text:
                return 'Spanish'
            if 'feta' in text or 'tzatziki' in text or 'gyro' in text:
                return 'Greek'
            if 'burger' in text or 'hot dog' in text or 'barbecue' in text:
                return 'American'
                
        # Return the original cuisine if it looks reasonable
        if len(cuisine) > 2 and cuisine not in ['', 'none', 'unknown', 'n/a']:
            return cuisine.title()
            
        return ""
    
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
            ids.append(str(recipe.get('id')))  # Use recipe ID directly, not prefixed
            
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
        # Ensure we have a valid query
        if not query or not query.strip():
            return "recipe"
        
        # For now, just return the original query to ensure we get results
        # We can add expansion later once basic search is working
        return query.strip() 

    def _create_searchable_text(self, recipe: Dict[str, Any]) -> str:
        """
        Create a comprehensive searchable text representation of a recipe
        """
        text_parts = []
        
        # Add basic recipe info
        if recipe.get('name'):
            text_parts.append(recipe['name'])
        if recipe.get('title'):
            text_parts.append(recipe['title'])
        if recipe.get('description'):
            text_parts.append(recipe['description'])
            
        # Add ingredients
        ingredients = recipe.get('ingredients', [])
        if ingredients:
            ingredient_texts = []
            for ing in ingredients:
                if isinstance(ing, dict):
                    if 'name' in ing:
                        ingredient_texts.append(ing['name'])
                    elif 'ingredient' in ing:
                        ingredient_texts.append(ing['ingredient'])
                else:
                    ingredient_texts.append(str(ing))
            text_parts.append(' '.join(ingredient_texts))
            
        # Add instructions
        instructions = recipe.get('instructions', '')
        if instructions:
            if isinstance(instructions, list):
                text_parts.append(' '.join(instructions))
            else:
                text_parts.append(str(instructions))
                
        # Add cuisine and tags
        if recipe.get('cuisine'):
            text_parts.append(recipe['cuisine'])
        if recipe.get('tags'):
            if isinstance(recipe['tags'], list):
                text_parts.extend(recipe['tags'])
            else:
                text_parts.append(str(recipe['tags']))
                
        return ' '.join(text_parts) 