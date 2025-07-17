import requests
import time
import os
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

class RecipeBulkLoader:
    """
    Service to bulk load thousands of high-quality recipes from multiple sources
    """
    
    def __init__(self, recipes_collection=None):
        self.recipes_collection = recipes_collection
        self.spoonacular_api_key = os.getenv("SPOONACULAR_API_KEY", "01f12ed117584307b5cba262f43a8d49")
        self.spoonacular_url = "https://api.spoonacular.com/recipes/complexSearch"
        self.spoonacular_detail_url = "https://api.spoonacular.com/recipes/{id}/information"
        
    def bulk_load_popular_recipes(self, target_count: int = 1000) -> Dict[str, Any]:
        """
        Load thousands of popular recipes from Spoonacular
        """
        logger.info(f"Starting bulk load of {target_count} recipes")
        
        loaded_recipes = []
        errors = []
        cuisines = [
            "italian", "mexican", "indian", "chinese", "japanese", "american",
            "french", "thai", "mediterranean", "greek", "korean", "spanish",
            "german", "british", "african", "middle eastern"
        ]
        
        recipe_types = [
            "breakfast", "lunch", "dinner", "dessert", "snack", "appetizer",
            "main course", "side dish", "salad", "soup", "beverage"
        ]
        
        diet_types = [
            "vegetarian", "vegan", "gluten free", "ketogenic", "paleo",
            "dairy free", "whole30", "pescetarian"
        ]
        
        # Strategy 1: Load by cuisine
        recipes_per_cuisine = min(100, target_count // len(cuisines))
        for cuisine in cuisines:
            try:
                cuisine_recipes = self._fetch_recipes_by_query(
                    query=cuisine, 
                    number=recipes_per_cuisine,
                    add_recipe_info=True
                )
                loaded_recipes.extend(cuisine_recipes)
                logger.info(f"Loaded {len(cuisine_recipes)} recipes for {cuisine} cuisine")
                time.sleep(1)  # Rate limiting
            except Exception as e:
                errors.append(f"Failed to load {cuisine} recipes: {str(e)}")
                logger.error(f"Failed to load {cuisine} recipes: {e}")
        
        # Strategy 2: Load by meal type
        if len(loaded_recipes) < target_count:
            remaining = target_count - len(loaded_recipes)
            recipes_per_type = min(50, remaining // len(recipe_types))
            
            for recipe_type in recipe_types:
                try:
                    type_recipes = self._fetch_recipes_by_query(
                        query=recipe_type,
                        number=recipes_per_type,
                        add_recipe_info=True
                    )
                    loaded_recipes.extend(type_recipes)
                    logger.info(f"Loaded {len(type_recipes)} recipes for {recipe_type}")
                    time.sleep(1)
                except Exception as e:
                    errors.append(f"Failed to load {recipe_type} recipes: {str(e)}")
        
        # Strategy 3: Load by diet type
        if len(loaded_recipes) < target_count:
            remaining = target_count - len(loaded_recipes)
            recipes_per_diet = min(30, remaining // len(diet_types))
            
            for diet in diet_types:
                try:
                    diet_recipes = self._fetch_recipes_by_query(
                        query=diet,
                        number=recipes_per_diet,
                        add_recipe_info=True
                    )
                    loaded_recipes.extend(diet_recipes)
                    logger.info(f"Loaded {len(diet_recipes)} recipes for {diet} diet")
                    time.sleep(1)
                except Exception as e:
                    errors.append(f"Failed to load {diet} recipes: {str(e)}")
        
        # Strategy 4: Load popular/trending recipes
        if len(loaded_recipes) < target_count:
            remaining = target_count - len(loaded_recipes)
            try:
                popular_recipes = self._fetch_popular_recipes(remaining)
                loaded_recipes.extend(popular_recipes)
                logger.info(f"Loaded {len(popular_recipes)} popular recipes")
            except Exception as e:
                errors.append(f"Failed to load popular recipes: {str(e)}")
        
        # Remove duplicates
        unique_recipes = self._remove_duplicates(loaded_recipes)
        
        # Store in database
        stored_count = 0
        if self.recipes_collection:
            stored_count = self._store_recipes(unique_recipes)
        
        return {
            "total_loaded": len(unique_recipes),
            "stored_in_db": stored_count,
            "errors": errors,
            "success": len(errors) == 0 or len(unique_recipes) > 0
        }
    
    def _fetch_recipes_by_query(self, query: str, number: int = 100, add_recipe_info: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch recipes by search query with detailed information
        """
        params = {
            "apiKey": self.spoonacular_api_key,
            "query": query,
            "number": min(number, 100),  # API limit
            "addRecipeInformation": add_recipe_info,
            "fillIngredients": True,
            "instructionsRequired": True,
            "sort": "popularity"
        }
        
        response = requests.get(self.spoonacular_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "results" not in data:
            return []
        
        # Process and validate each recipe
        processed_recipes = []
        for recipe in data["results"]:
            processed_recipe = self._process_and_validate_recipe(recipe)
            if processed_recipe:
                processed_recipes.append(processed_recipe)
        
        return processed_recipes
    
    def _fetch_popular_recipes(self, number: int) -> List[Dict[str, Any]]:
        """
        Fetch trending/popular recipes
        """
        params = {
            "apiKey": self.spoonacular_api_key,
            "number": min(number, 100),
            "addRecipeInformation": True,
            "fillIngredients": True,
            "sort": "popularity",
            "instructionsRequired": True
        }
        
        response = requests.get(self.spoonacular_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        processed_recipes = []
        for recipe in data.get("results", []):
            processed_recipe = self._process_and_validate_recipe(recipe)
            if processed_recipe:
                processed_recipes.append(processed_recipe)
        
        return processed_recipes
    
    def _process_and_validate_recipe(self, raw_recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and validate recipe data to ensure quality
        """
        # Skip recipes without essential data
        if not raw_recipe.get("title") or not raw_recipe.get("id"):
            return None
        
        # If recipe doesn't have detailed info, fetch it
        if not raw_recipe.get("extendedIngredients") or not raw_recipe.get("analyzedInstructions"):
            try:
                detailed_recipe = self._fetch_detailed_recipe(raw_recipe["id"])
                if detailed_recipe:
                    raw_recipe.update(detailed_recipe)
            except Exception as e:
                logger.warning(f"Failed to fetch details for recipe {raw_recipe['id']}: {e}")
        
        # Validate essential fields
        title = raw_recipe.get("title", "").strip()
        if not title or title.lower() in ["untitled", "untitled recipe", ""]:
            return None
        
        # Ensure we have ingredients
        ingredients = raw_recipe.get("extendedIngredients", [])
        if not ingredients or len(ingredients) == 0:
            return None
        
        # Ensure we have instructions
        instructions = raw_recipe.get("analyzedInstructions", [])
        if not instructions or len(instructions) == 0:
            # Try string instructions as fallback
            string_instructions = raw_recipe.get("instructions", "")
            if not string_instructions or len(string_instructions.strip()) < 20:
                return None
        
        # Process and normalize the recipe
        processed = {
            "id": raw_recipe["id"],
            "title": title,
            "image": raw_recipe.get("image", ""),
            "readyInMinutes": raw_recipe.get("readyInMinutes", 30),
            "servings": raw_recipe.get("servings", 4),
            "sourceUrl": raw_recipe.get("sourceUrl", ""),
            "summary": raw_recipe.get("summary", ""),
            "cuisines": raw_recipe.get("cuisines", []),
            "dishTypes": raw_recipe.get("dishTypes", []),
            "diets": raw_recipe.get("diets", []),
            "extendedIngredients": ingredients,
            "analyzedInstructions": instructions,
            "instructions": raw_recipe.get("instructions", ""),
            "spoonacularScore": raw_recipe.get("spoonacularScore", 0),
            "healthScore": raw_recipe.get("healthScore", 0),
            "pricePerServing": raw_recipe.get("pricePerServing", 0),
            "cheap": raw_recipe.get("cheap", False),
            "dairyFree": raw_recipe.get("dairyFree", False),
            "glutenFree": raw_recipe.get("glutenFree", False),
            "vegan": raw_recipe.get("vegan", False),
            "vegetarian": raw_recipe.get("vegetarian", False),
            "veryHealthy": raw_recipe.get("veryHealthy", False),
            "veryPopular": raw_recipe.get("veryPopular", False),
            "gaps": raw_recipe.get("gaps", ""),
            "lowFodmap": raw_recipe.get("lowFodmap", False),
            "sustainable": raw_recipe.get("sustainable", False),
            "whole30": raw_recipe.get("whole30", False),
            "weightWatcherSmartPoints": raw_recipe.get("weightWatcherSmartPoints", 0),
            "creditsText": raw_recipe.get("creditsText", ""),
            "sourceName": raw_recipe.get("sourceName", ""),
            "aggregateLikes": raw_recipe.get("aggregateLikes", 0),
            "nutrition": raw_recipe.get("nutrition", {}),
            "added_at": time.time(),
            "quality_score": self._calculate_quality_score(raw_recipe)
        }
        
        return processed
    
    def _fetch_detailed_recipe(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed recipe information by ID
        """
        url = self.spoonacular_detail_url.format(id=recipe_id)
        params = {
            "apiKey": self.spoonacular_api_key,
            "includeNutrition": True
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _calculate_quality_score(self, recipe: Dict[str, Any]) -> float:
        """
        Calculate a quality score for the recipe
        """
        score = 0.0
        
        # Title quality
        title = recipe.get("title", "")
        if title and len(title) > 5:
            score += 1.0
        
        # Ingredients count
        ingredients = recipe.get("extendedIngredients", [])
        if len(ingredients) >= 3:
            score += 1.0
        if len(ingredients) >= 6:
            score += 0.5
        
        # Instructions quality
        instructions = recipe.get("analyzedInstructions", [])
        if instructions and len(instructions) > 0:
            score += 1.0
            total_steps = sum(len(inst.get("steps", [])) for inst in instructions)
            if total_steps >= 3:
                score += 0.5
        
        # Image quality
        image = recipe.get("image", "")
        if image and "http" in image and "placeholder" not in image.lower():
            score += 0.5
        
        # Cooking time reasonableness
        ready_time = recipe.get("readyInMinutes", 0)
        if 5 <= ready_time <= 180:  # 5 min to 3 hours
            score += 0.5
        
        # Popularity indicators
        if recipe.get("aggregateLikes", 0) > 10:
            score += 0.3
        if recipe.get("spoonacularScore", 0) > 50:
            score += 0.3
        if recipe.get("veryPopular", False):
            score += 0.2
        
        # Nutrition info
        if recipe.get("nutrition") and len(recipe.get("nutrition", {})) > 0:
            score += 0.5
        
        # Source credibility
        if recipe.get("sourceUrl") and len(recipe.get("sourceUrl", "")) > 10:
            score += 0.3
        
        return min(score, 5.0)  # Cap at 5.0
    
    def _remove_duplicates(self, recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate recipes based on ID and title similarity
        """
        seen_ids = set()
        seen_titles = set()
        unique_recipes = []
        
        for recipe in recipes:
            recipe_id = recipe.get("id")
            title = recipe.get("title", "").lower().strip()
            
            # Skip if we've seen this ID
            if recipe_id in seen_ids:
                continue
            
            # Skip if we've seen a very similar title
            title_words = set(title.split())
            is_duplicate = False
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())
                # If 80% of words overlap, consider it a duplicate
                if len(title_words & seen_words) / max(len(title_words), len(seen_words)) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_ids.add(recipe_id)
                seen_titles.add(title)
                unique_recipes.append(recipe)
        
        return unique_recipes
    
    def _store_recipes(self, recipes: List[Dict[str, Any]]) -> int:
        """
        Store recipes in MongoDB, avoiding duplicates
        """
        if not self.recipes_collection:
            return 0
        
        stored_count = 0
        for recipe in recipes:
            try:
                # Check if recipe already exists
                existing = self.recipes_collection.find_one({"id": recipe["id"]})
                if not existing:
                    self.recipes_collection.insert_one(recipe)
                    stored_count += 1
                else:
                    # Update if new recipe has higher quality score
                    new_quality = recipe.get("quality_score", 0)
                    existing_quality = existing.get("quality_score", 0)
                    if new_quality > existing_quality:
                        self.recipes_collection.update_one(
                            {"id": recipe["id"]},
                            {"$set": recipe}
                        )
                        logger.info(f"Updated recipe {recipe['id']} with higher quality version")
            except Exception as e:
                logger.error(f"Failed to store recipe {recipe.get('id')}: {e}")
        
        return stored_count
    
    def load_recipes_by_categories(self, categories: Dict[str, int]) -> Dict[str, Any]:
        """
        Load specific number of recipes for each category
        
        Example:
        categories = {
            "italian": 100,
            "healthy": 50,
            "vegetarian": 75,
            "dessert": 30
        }
        """
        results = {
            "categories": {},
            "total_loaded": 0,
            "errors": []
        }
        
        for category, count in categories.items():
            try:
                logger.info(f"Loading {count} recipes for category: {category}")
                category_recipes = self._fetch_recipes_by_query(
                    query=category,
                    number=count,
                    add_recipe_info=True
                )
                
                # Store in database
                stored_count = 0
                if self.recipes_collection:
                    stored_count = self._store_recipes(category_recipes)
                
                results["categories"][category] = {
                    "requested": count,
                    "fetched": len(category_recipes),
                    "stored": stored_count
                }
                results["total_loaded"] += len(category_recipes)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                error_msg = f"Failed to load {category} recipes: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        return results 