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
        'mediterranean', 'korean', 'caribbean', 'cajun', 'southern',
        'eastern european', 'latin american', 'african', 'middle eastern', 'asian'
    ]
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        # Try to get the correct collection - check what's available
        try:
            # First try the recipe_details_cache collection (which we know exists)
            self.recipe_collection = self.client.get_collection("recipe_details_cache")
            print("Using recipe_details_cache collection for search")
        except Exception as e:
            try:
                # Fallback to recipe_search_cache
                self.recipe_collection = self.client.get_collection("recipe_search_cache")
                print("Using recipe_search_cache collection for search")
            except Exception as e2:
                print(f"Error getting collections: {e2}")
                # Try to list available collections
                try:
                    collections = self.client.list_collections()
                    print(f"Available collections: {[c.name for c in collections]}")
                    if collections:
                        self.recipe_collection = collections[0]
                        print(f"Using first available collection: {collections[0].name}")
                    else:
                        print("No collections found!")
                        self.recipe_collection = None
                except Exception as e3:
                    print(f"Could not list collections: {e3}")
                    self.recipe_collection = None
        
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
        # Preserve input order and ensure uniqueness for cuisines
        raw_fav_cuisines = [self._normalize_cuisine(c, None).lower() for c in user_preferences.get("favoriteCuisines", []) if c]
        seen_c = set()
        favorite_cuisines = [c for c in raw_fav_cuisines if not (c in seen_c or seen_c.add(c))]
        foods_to_avoid = set(f.lower() for f in user_preferences.get("foodsToAvoid", []) if f)
        dietary_restrictions = [d.lower() for d in user_preferences.get("dietaryRestrictions", [])]

        print(f"User selected cuisines (ordered): {favorite_cuisines}")
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
            recipe_cuisines = []
            
            # First try the normalized cuisine field
            if recipe.get('cuisine'):
                recipe_cuisines.append(self._normalize_cuisine(recipe.get('cuisine', ''), recipe).lower())
            
            # If no cuisine found, try cuisines array
            if recipe.get('cuisines'):
                cuisines = recipe.get('cuisines', [])
                if isinstance(cuisines, list) and cuisines:
                    for cuisine in cuisines:
                        if cuisine:
                            normalized_cuisine = self._normalize_cuisine(cuisine, recipe).lower()
                            if normalized_cuisine and normalized_cuisine not in recipe_cuisines:
                                recipe_cuisines.append(normalized_cuisine)
            
            # If still no cuisine, try to detect from recipe content
            if not recipe_cuisines:
                detected_cuisine = self._detect_cuisine_from_ingredients(recipe).lower()
                if detected_cuisine:
                    recipe_cuisines.append(detected_cuisine)
            
            # Check if any favorite cuisine matches any of the recipe's cuisines
            for fav_cuisine in favorite_cuisines:
                if not fav_cuisine:
                    continue
                    
                fav_cuisine_lower = fav_cuisine.lower()
                
                for recipe_cuisine in recipe_cuisines:
                    # Exact match
                    if fav_cuisine_lower == recipe_cuisine:
                        return True
                    
                    # Partial match (e.g., "chinese" in "chinese takeout")
                    if fav_cuisine_lower in recipe_cuisine or recipe_cuisine in fav_cuisine_lower:
                        return True
                    
                    # For broad cuisines like "International", be more flexible
                    if fav_cuisine_lower in ['international', 'global', 'world', 'fusion']:
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
                        # Try multiple ways to get cuisine
                        recipe_cuisines = []
                        
                        # First try the normalized cuisine field
                        if recipe.get('cuisine'):
                            recipe_cuisines.append(self._normalize_cuisine(recipe.get('cuisine', ''), recipe).lower())
                        
                        # If no cuisine found, try cuisines array
                        if recipe.get('cuisines'):
                            cuisines = recipe.get('cuisines', [])
                            if isinstance(cuisines, list) and cuisines:
                                for recipe_cuisine in cuisines:
                                    if recipe_cuisine:
                                        normalized_cuisine = self._normalize_cuisine(recipe_cuisine, recipe).lower()
                                        if normalized_cuisine and normalized_cuisine not in recipe_cuisines:
                                            recipe_cuisines.append(normalized_cuisine)
                        
                        # Check if any of the recipe's cuisines match
                        cuisine_matched = False
                        for recipe_cuisine in recipe_cuisines:
                            # Check for exact match
                            if recipe_cuisine == cuisine:
                                filtered_candidates.append(recipe)
                                cuisine_matched = True
                                break
                                
                            # Check for partial match (e.g., "spanish" in "spanish paella")
                            if cuisine in recipe_cuisine or recipe_cuisine in cuisine:
                                filtered_candidates.append(recipe)
                                cuisine_matched = True
                                break
                        
                        if cuisine_matched:
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
                            if recipe_cuisines and any(cuisine not in ['', 'none', 'unknown', 'n/a'] for cuisine in recipe_cuisines):
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
            
            # Initialize cuisine groups with empty lists
            cuisine_groups = {cuisine: [] for cuisine in favorite_cuisines}
            uncategorized = []
            
            # Categorize each recipe into cuisine groups
            for recipe in candidates:
                recipe_cuisines = set()
                
                # Extract cuisines from all possible fields
                if recipe.get('cuisine'):
                    cuisine = self._normalize_cuisine(recipe.get('cuisine', ''), recipe).lower()
                    if cuisine:
                        recipe_cuisines.add(cuisine)
                
                if recipe.get('cuisines'):
                    cuisines = recipe.get('cuisines', [])
                    if isinstance(cuisines, list):
                        for cuisine in cuisines:
                            if cuisine:
                                normalized = self._normalize_cuisine(cuisine, recipe).lower()
                                if normalized:
                                    recipe_cuisines.add(normalized)
                
                # Try to match with user's favorite cuisines
                matched = False
                for fav_cuisine in favorite_cuisines:
                    fav_lower = fav_cuisine.lower()
                    for recipe_cuisine in recipe_cuisines:
                        if (recipe_cuisine == fav_lower or 
                            fav_lower in recipe_cuisine or 
                            recipe_cuisine in fav_lower):
                            cuisine_groups[fav_cuisine].append(recipe)
                            matched = True
                            break
                    if matched:
                        break
                
                if not matched and recipe_cuisines:
                    uncategorized.append(recipe)
            
            # Helper: does a recipe match a specific favorite cuisine?
            def matches_cuisine(recipe: Dict[str, Any], fav_cuisine: str) -> bool:
                fl = fav_cuisine.lower()
                # Check explicit cuisine field
                rc = recipe.get('cuisine')
                if rc:
                    norm = self._normalize_cuisine(rc, recipe).lower()
                    if norm and (norm == fl or fl in norm or norm in fl):
                        return True
                # Check cuisines array
                cuisines = recipe.get('cuisines', [])
                if isinstance(cuisines, list):
                    for c in cuisines:
                        if not c:
                            continue
                        norm = self._normalize_cuisine(c, recipe).lower()
                        if norm and (norm == fl or fl in norm or norm in fl):
                            return True
                # Check title/description as a last resort
                text = ' '.join([
                    str(recipe.get('title', '')),
                    str(recipe.get('name', '')),
                    str(recipe.get('description', ''))
                ]).lower()
                return fl in text

            # Debug: Show what cuisines were found
            print(f"\nCuisine grouping results:")
            for cuisine in favorite_cuisines:
                count = len(cuisine_groups[cuisine])
                print(f"  {cuisine}: {count} recipes")
            
            # Ensure we have at least one recipe per selected cuisine.
            # First try from overall candidates based on matches_cuisine to avoid relying only on 'uncategorized'.
            grouped_ids = set()
            for lst in cuisine_groups.values():
                for r in lst:
                    rid = r.get('recipe_id') or r.get('id')
                    if rid:
                        grouped_ids.add(rid)
            for cuisine in favorite_cuisines:
                if not cuisine_groups[cuisine]:
                    # Look in all candidates for a match not yet grouped
                    for r in candidates:
                        rid = r.get('recipe_id') or r.get('id')
                        if rid and rid in grouped_ids:
                            continue
                        if matches_cuisine(r, cuisine):
                            cuisine_groups[cuisine].append(r)
                            if rid:
                                grouped_ids.add(rid)
                            break
            # As a final fallback, use uncategorized text heuristics to fill empty cuisines
            for cuisine in favorite_cuisines:
                if not cuisine_groups[cuisine] and uncategorized:
                    for i, r in enumerate(uncategorized):
                        if matches_cuisine(r, cuisine):
                            cuisine_groups[cuisine].append(r)
                            uncategorized.pop(i)
                            rid = r.get('recipe_id') or r.get('id')
                            if rid:
                                grouped_ids.add(rid)
                            break
            
            # Calculate how many recipes per cuisine for fair distribution
            recipes_per_cuisine = max(1, limit // len(favorite_cuisines))
            print(f"Target: {recipes_per_cuisine} recipes per cuisine")
            
            # Sort recipes within each cuisine by score
            for cuisine in cuisine_groups:
                cuisine_groups[cuisine].sort(key=score_recipe, reverse=True)

            # Build fair distribution using explicit per-cuisine targets
            n_cuisines = max(1, len(favorite_cuisines))
            base = limit // n_cuisines
            remainder = limit % n_cuisines
            targets = {}
            for idx, cuisine in enumerate(favorite_cuisines):
                targets[cuisine] = base + (1 if idx < remainder else 0)
            print(f"Per-cuisine targets: {targets}")

            fair_recommendations = []
            slots_remaining = limit

            # First pass: take up to target per cuisine
            for cuisine in favorite_cuisines:
                want = targets.get(cuisine, 0)
                take = min(want, len(cuisine_groups[cuisine]))
                for _ in range(take):
                    if slots_remaining <= 0:
                        break
                    fair_recommendations.append(cuisine_groups[cuisine].pop(0))
                    slots_remaining -= 1

            # Second pass: if some cuisines lacked enough items, redistribute remaining slots
            while slots_remaining > 0 and any(cuisine_groups.values()):
                for cuisine in favorite_cuisines:
                    if slots_remaining <= 0:
                        break
                    if cuisine_groups[cuisine]:
                        fair_recommendations.append(cuisine_groups[cuisine].pop(0))
                        slots_remaining -= 1
            
            # If we still have slots to fill, add high-scored uncategorized recipes
            if slots_remaining > 0 and uncategorized:
                uncategorized.sort(key=score_recipe, reverse=True)
                fair_recommendations.extend(uncategorized[:slots_remaining])
            
            # Ensure we don't exceed the limit
            fair_recommendations = fair_recommendations[:limit]
            
            # Update the recommendations list with our fairly distributed recipes
            recommendations = fair_recommendations
            
            # Optional: simple distribution log for debugging
            try:
                cuisine_counts = {}
                for r in recommendations:
                    r_cuisines = []
                    if r.get('cuisine'):
                        norm = self._normalize_cuisine(r.get('cuisine', ''), r).lower()
                        if norm:
                            r_cuisines.append(norm)
                    cuisines = r.get('cuisines', [])
                    if isinstance(cuisines, list):
                        for c in cuisines:
                            if c:
                                norm = self._normalize_cuisine(c, r).lower()
                                if norm and norm not in r_cuisines:
                                    r_cuisines.append(norm)
                    for fav in favorite_cuisines:
                        fl = fav.lower()
                        if any(fl == rc or fl in rc or rc in fl for rc in r_cuisines):
                            cuisine_counts[fav] = cuisine_counts.get(fav, 0) + 1
                            break
                print(f"Final distribution by cuisine: {cuisine_counts}")
            except Exception as e:
                print(f"Distribution logging error: {e}")
        
        # Debug: Print top 10 scored recipes
        print("\nTop 10 Scored Recipes:")
        for i, r in enumerate(recommendations[:10], 1):
            rid = r.get('recipe_id') or r.get('id')
            title = r.get('title', 'No title')
            
            # Try multiple ways to get cuisine for display
            display_cuisine = 'Unknown'
            if r.get('cuisine'):
                display_cuisine = self._normalize_cuisine(r.get('cuisine', ''), r)
            elif r.get('cuisines'):
                cuisines = r.get('cuisines', [])
                if isinstance(cuisines, list) and cuisines:
                    display_cuisine = ', '.join(cuisines)
            
            score = score_recipe(r)
            print(f"{i}. {title} | Cuisine: {display_cuisine} | Score: {score}")
        
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
                # Try multiple ways to get cuisine
                recipe_cuisines = []
                
                # First try the normalized cuisine field
                if r.get('cuisine'):
                    recipe_cuisines.append(self._normalize_cuisine(r.get('cuisine', ''), r).lower())
                
                # If no cuisine found, try cuisines array
                if r.get('cuisines'):
                    cuisines = r.get('cuisines', [])
                    if isinstance(cuisines, list) and cuisines:
                        for cuisine in cuisines:
                            if cuisine:
                                normalized_cuisine = self._normalize_cuisine(cuisine, r).lower()
                                if normalized_cuisine and normalized_cuisine not in recipe_cuisines:
                                    recipe_cuisines.append(normalized_cuisine)
                
                # Count each cuisine found
                for recipe_cuisine in recipe_cuisines:
                    final_cuisines[recipe_cuisine] = final_cuisines.get(recipe_cuisine, 0) + 1
                
                # If no cuisine found, mark as unknown
                if not recipe_cuisines:
                    final_cuisines['unknown'] = final_cuisines.get('unknown', 0) + 1
                    
            print(f"Final recommendations by cuisine: {final_cuisines}")
        
        return final

    # Add other necessary methods here (semantic_search, _normalize_cuisine, etc.)
    def semantic_search(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Basic semantic search using ChromaDB"""
        if not self.recipe_collection:
            print("No recipe collection available for search")
            return []
            
        try:
            # Get all recipes from the collection
            results = self.recipe_collection.get()
            
            if not results or not results.get('documents'):
                print(f"No recipes found in collection for query: {query}")
                return []
            
            recipes = []
            for i, doc in enumerate(results['documents']):
                try:
                    # Parse the JSON document
                    recipe = json.loads(doc)
                    recipes.append(recipe)
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Error parsing recipe {i}: {e}")
                    continue
            
            print(f"Found {len(recipes)} total recipes in database")
            
            # Simple text-based filtering based on query
            if query and query.strip():
                query_lower = query.lower().strip()
                filtered_recipes = []
                
                for recipe in recipes:
                    # Check title, description, cuisines, ingredients
                    searchable_text = []
                    
                    if recipe.get('title'):
                        searchable_text.append(str(recipe['title']).lower())
                    if recipe.get('name'):
                        searchable_text.append(str(recipe['name']).lower())
                    if recipe.get('description'):
                        searchable_text.append(str(recipe['description']).lower())
                    if recipe.get('cuisines'):
                        for cuisine in recipe['cuisines']:
                            searchable_text.append(str(cuisine).lower())
                    if recipe.get('cuisine'):
                        searchable_text.append(str(recipe['cuisine']).lower())
                    if recipe.get('ingredients'):
                        for ing in recipe['ingredients']:
                            if isinstance(ing, dict) and ing.get('name'):
                                searchable_text.append(str(ing['name']).lower())
                            elif isinstance(ing, str):
                                searchable_text.append(ing.lower())
                    
                    # Check if query appears in any searchable text
                    if any(query_lower in text for text in searchable_text):
                        filtered_recipes.append(recipe)
                
                print(f"Query '{query}' matched {len(filtered_recipes)} recipes")
                recipes = filtered_recipes
            
            # Apply filters if provided
            if filters:
                filtered_recipes = []
                for recipe in recipes:
                    include_recipe = True
                    
                    if filters.get('is_vegetarian') and not self._is_vegetarian(recipe):
                        include_recipe = False
                    if filters.get('is_vegan') and not self._is_vegan(recipe):
                        include_recipe = False
                    if filters.get('is_gluten_free') and not self._is_gluten_free(recipe):
                        include_recipe = False
                    
                    if include_recipe:
                        filtered_recipes.append(recipe)
                
                recipes = filtered_recipes
                print(f"After applying filters: {len(recipes)} recipes")
            
            # Limit results
            return recipes[:limit]
            
        except Exception as e:
            print(f"Error in semantic_search: {e}")
            return []
    
    def _is_vegetarian(self, recipe: Dict[str, Any]) -> bool:
        """Check if recipe is vegetarian"""
        # Simple check - can be enhanced
        avoid_ingredients = ['beef', 'pork', 'chicken', 'fish', 'shrimp', 'lamb', 'meat']
        ingredients = recipe.get('ingredients', [])
        
        for ing in ingredients:
            if isinstance(ing, dict) and ing.get('name'):
                ing_name = str(ing['name']).lower()
                if any(avoid in ing_name for avoid in avoid_ingredients):
                    return False
            elif isinstance(ing, str):
                ing_name = ing.lower()
                if any(avoid in ing_name for avoid in avoid_ingredients):
                    return False
        
        return True
    
    def _is_vegan(self, recipe: Dict[str, Any]) -> bool:
        """Check if recipe is vegan"""
        # Simple check - can be enhanced
        avoid_ingredients = ['beef', 'pork', 'chicken', 'fish', 'shrimp', 'lamb', 'meat', 'cheese', 'milk', 'eggs', 'butter', 'cream']
        ingredients = recipe.get('ingredients', [])
        
        for ing in ingredients:
            if isinstance(ing, dict) and ing.get('name'):
                ing_name = str(ing['name']).lower()
                if any(avoid in ing_name for avoid in avoid_ingredients):
                    return False
            elif isinstance(ing, str):
                ing_name = ing.lower()
                if any(avoid in ing_name for avoid in avoid_ingredients):
                    return False
        
        return True
    
    def _is_gluten_free(self, recipe: Dict[str, Any]) -> bool:
        """Check if recipe is gluten-free"""
        # Simple check - can be enhanced
        gluten_ingredients = ['wheat', 'flour', 'bread', 'pasta', 'noodles', 'soy sauce', 'barley', 'rye']
        ingredients = recipe.get('ingredients', [])
        
        for ing in ingredients:
            if isinstance(ing, dict) and ing.get('name'):
                ing_name = str(ing['name']).lower()
                if any(gluten in ing_name for gluten in gluten_ingredients):
                    return False
            elif isinstance(ing, str):
                ing_name = ing.lower()
                if any(gluten in ing_name for gluten in gluten_ingredients):
                    return False
        
        return True
    
    def _normalize_cuisine(self, cuisine: str, recipe: Optional[Dict] = None) -> str:
        """Placeholder for cuisine normalization - implement as needed"""
        if not cuisine:
            return ""
        return cuisine.strip().title()
    
    def _detect_cuisine_from_ingredients(self, recipe: Dict[str, Any]) -> str:
        """Placeholder for cuisine detection - implement as needed"""
        return ""