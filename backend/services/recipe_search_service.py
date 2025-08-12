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
        'american', 'british', 'chinese', 'french', 'greek', 'indian', 'irish', 
        'italian', 'japanese', 'mexican', 'moroccan', 'spanish', 'thai', 'vietnamese',
        'mediterranean', 'korean', 'caribbean', 'cajun', 'southern', 'nordic',
        'eastern european', 'jewish', 'latin american', 'african', 'middle eastern', 'asian'
    ]
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        # Use the recipe_search_cache collection which contains the actual recipes
        self.recipe_collection = self.client.get_collection("recipe_search_cache")
        print("Using recipe_search_cache collection for search")
        
        try:
            # Initialize sentence transformer for better embeddings
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Using SentenceTransformer for enhanced embeddings")
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer, falling back to ChromaDB default: {e}")
            self.encoder = None
    
    def get_recipe_recommendations(self, user_preferences: Dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
        """
        Get personalized recipe recommendations with fair distribution across cuisines
        """
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

        # Define helper functions
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
            
            # Check each food to avoid
            for food in foods_to_avoid:
                if not food:  # Skip empty foods
                    continue
                    
                # Check for exact word matches
                if f' {food} ' in f' {search_text} ' or \
                   search_text.startswith(f'{food} ') or \
                   search_text.endswith(f' {food}') or \
                   search_text == food:
                    return True
                    
                # Check for partial matches (for foods like "beef" in "beef broth")
                if food in search_text:
                    return True
                    
                # Also check for plural/singular forms
                if food.endswith('s') and (f' {food[:-1]} ' in f' {search_text} ' or
                                         search_text.startswith(f'{food[:-1]} ')):
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
        
        # Search for recipes based on preferences
        candidates = []
        
        # Always search for favorite foods first if present
        if favorite_foods:
            print(f"Searching for favorite foods: {favorite_foods}")
            query = " ".join(favorite_foods)
            print(f"Food search query: {query}")
            
            # Get more candidates since we're searching for specific foods
            food_candidates = self.semantic_search(query, filters, limit * 30)
            print(f"Found {len(food_candidates)} candidates with favorite foods")
            
            # If no results, try searching for each food individually
            if not food_candidates:
                print("No results with combined search, trying individual food searches...")
                for food in favorite_foods:
                    food_candidates = self.semantic_search(food, filters, limit * 10)
                    candidates.extend(food_candidates)
                    print(f"Found {len(food_candidates)} candidates for '{food}'")
            else:
            # Filter to only include recipes that actually contain at least one favorite food
                food_candidates = [r for r in food_candidates if has_fav_food(r)]
                print(f"After filtering for actual food matches: {len(food_candidates)} candidates")
                candidates.extend(food_candidates)
            
        # If we have cuisines, also search within those cuisines
        if favorite_cuisines:
            print(f"Searching for recipes in selected cuisines: {favorite_cuisines}")
            
            # Check if any of the cuisines are "International" or similar broad terms
            has_broad_cuisine = any(c.lower() in ['international', 'global', 'world', 'fusion'] for c in favorite_cuisines)
            
            if has_broad_cuisine:
                # For broad cuisines like "International", get popular recipes
                print(f"Broad cuisine detected, getting popular recipes")
                cuisine_candidates = self.semantic_search("popular recipes", filters, limit * 10)
            else:
                # Search for each selected cuisine separately to ensure we get recipes from those cuisines
                all_cuisine_candidates = []
                for cuisine in favorite_cuisines:
                    print(f"Searching for recipes in cuisine: {cuisine}")
                    search_terms = [cuisine]
                    
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
                    all_cuisine_candidates.extend(filtered_candidates)
                
                cuisine_candidates = all_cuisine_candidates
            
            candidates.extend(cuisine_candidates)
        
        # If no specific preferences, get popular recipes
        if not candidates:
            print("No specific preferences, getting popular recipes")
            query = "popular recipes"
            candidates = self.semantic_search(query, filters, limit * 10)
            
        # If we have BOTH favorite foods AND cuisines, also search for foods across all cuisines
        if favorite_foods and favorite_cuisines:
            print(f"User has both favorite foods and cuisines - searching for foods across all cuisines")
            
            # Search for favorite foods across all cuisines
            food_query = " ".join(favorite_foods)
            food_candidates = self.semantic_search(food_query, filters, limit * 20)
            print(f"Found {len(food_candidates)} candidates for favorite foods across all cuisines")
            
            # Filter for actual food matches
            food_candidates = [r for r in food_candidates if has_fav_food(r)]
            print(f"After filtering for actual food matches: {len(food_candidates)} candidates")
            
            # Combine with existing candidates
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

        print(f"Total candidates after filtering: {len(candidates)}")

        # Remove foods to avoid
        candidates = [r for r in candidates if not has_foods_to_avoid(r)]
        print(f"Candidates after removing foods to avoid: {len(candidates)}")

        # Score each recipe based on multiple factors
        def score_recipe(recipe):
            if not recipe:
                return 0
                
            score = 0
            
            # HIGH priority: matching favorite foods (5 points per match)
            food_matches = count_matching_foods(recipe)
            score += food_matches * 5
            
            # HIGH priority: matching cuisine (5 points per match)
            if favorite_cuisines and in_fav_cuisine(recipe):
                score += 5
            
            # If we only have favorite foods (no cuisines), give a moderate boost
            if not favorite_cuisines and favorite_foods:
                score += 6
                
                # Extra boost if multiple favorite foods match
                if food_matches > 1:
                    score += (food_matches - 1) * 2
            
            # Bonus for food matches in title/name (3 points)
            title = str(recipe.get('title', '') or '') + ' ' + str(recipe.get('name', '') or '')
            title = title.lower()
            for food in favorite_foods:
                if food and food in title:
                    score += 3
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
        
        # Implement fair distribution across cuisines (ensuring even representation)
        if favorite_cuisines:
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
            
            # Calculate how many recipes per cuisine for fair distribution
            recipes_per_cuisine = max(1, limit // len(favorite_cuisines))
            print(f"Target: {recipes_per_cuisine} recipes per cuisine")
            
            # Build fair distribution ensuring each cuisine gets equal representation
            fair_recommendations = []
            
            # First pass: take the top recipes from each cuisine
            for cuisine in favorite_cuisines:
                if cuisine in cuisine_groups and len(cuisine_groups[cuisine]) > 0:
                # Sort recipes in this cuisine by score and take the best ones
                    sorted_recipes = sorted(cuisine_groups[cuisine], key=score_recipe, reverse=True)
                    top_recipes = sorted_recipes[:recipes_per_cuisine]
                    fair_recommendations.extend(top_recipes)
                # Remove used recipes
                for recipe in top_recipes:
                    cuisine_groups[cuisine].remove(recipe)
            
            # Second pass: if we have room for more recipes, fill with remaining high-scored recipes
            # but maintain balance across cuisines
            remaining_slots = limit - len(fair_recommendations)
            if remaining_slots > 0:
                # Collect all remaining recipes and sort by score
                remaining_recipes = []
            for cuisine_recipes in cuisine_groups.values():
                remaining_recipes.extend(cuisine_recipes)
            
            remaining_recipes.sort(key=score_recipe, reverse=True)
                
                # Fill remaining slots while trying to maintain balance
            for i, recipe in enumerate(remaining_recipes):
                if len(fair_recommendations) >= limit:
                    break
                
                # Check if adding this recipe would unbalance the distribution too much
                recipe_cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe).lower()
                current_cuisine_counts = {}
                    
                    # Count current distribution
                for r in fair_recommendations:
                    r_cuisine = self._normalize_cuisine(r.get('cuisine', ''), r).lower()
                    for fav_c in favorite_cuisines:
                        if (r_cuisine == fav_c.lower() or 
                            fav_c.lower() in r_cuisine or 
                            r_cuisine in fav_c.lower()):
                            current_cuisine_counts[fav_c] = current_cuisine_counts.get(fav_c, 0) + 1
                            break
                    
                    # Find which cuisine this recipe belongs to
                    recipe_fav_cuisine = None
                    for fav_c in favorite_cuisines:
                        if (recipe_cuisine == fav_c.lower() or 
                            fav_c.lower() in recipe_cuisine or 
                            recipe_cuisine in fav_c.lower()):
                            recipe_fav_cuisine = fav_c
                            break
                    
                    if recipe_fav_cuisine:
                        # Check if adding this recipe would make the distribution too uneven
                        current_count = current_cuisine_counts.get(recipe_fav_cuisine, 0)
                        max_count = max(current_cuisine_counts.values()) if current_cuisine_counts else 0
                        
                        # Allow adding if it doesn't create too much imbalance
                        if current_count + 1 <= max_count + 1:
                            fair_recommendations.append(recipe)
                        elif len(fair_recommendations) < limit - 1:  # Still have room
                            # Only add if this cuisine is significantly underrepresented
                            if current_count < recipes_per_cuisine - 1:
                                fair_recommendations.append(recipe)
            
            recommendations = fair_recommendations[:limit]
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
            
            # Verify distribution is fair
            if cuisine_counts:
                min_count = min(cuisine_counts.values())
                max_count = max(cuisine_counts.values())
                print(f"Distribution range: {min_count} to {max_count} recipes per cuisine")
                if max_count - min_count > 2:
                    print("⚠️ Warning: Distribution is not very even")
                else:
                    print("✅ Distribution is fairly even")
        
        # Debug: Print top 10 scored recipes
        print("\nTop 10 Scored Recipes:")
        for i, r in enumerate(recommendations[:10], 1):
            rid = r.get('recipe_id') or r.get('id')
            title = r.get('title', 'No title')
            cuisine = self._normalize_cuisine(r.get('cuisine', ''), r)
            score = score_recipe(r)
            print(f"{i}. {title} | Cuisine: {cuisine} | Score: {score}")
        
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

    # Add other necessary methods here (semantic_search, _normalize_cuisine, etc.)
    def semantic_search(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Placeholder for semantic search - implement as needed"""
        # This is a simplified version - you'll need to implement the full semantic search
        return []
        
    def _normalize_cuisine(self, cuisine: str, recipe: Optional[Dict] = None) -> str:
        """Placeholder for cuisine normalization - implement as needed"""
        if not cuisine:
            return ""
        return cuisine.strip().title()
    
    def _detect_cuisine_from_ingredients(self, recipe: Dict[str, Any]) -> str:
        """Placeholder for cuisine detection - implement as needed"""
        return ""