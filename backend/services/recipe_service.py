import os
import requests
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import time
import aiohttp
import asyncio
import ssl
import certifi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecipeService:
    def __init__(self, recipe_cache):
        self.recipe_cache = recipe_cache
        
        # Spoonacular configuration
        self.spoonacular_key = os.environ.get('SPOONACULAR_API_KEY')
        self.spoonacular_base_url = os.environ.get('SPOONACULAR_BASE_URL', 'https://api.spoonacular.com')
        self.spoonacular_search_url = f"{self.spoonacular_base_url}/recipes/complexSearch"
        
        # TheMealDB configuration
        self.mealdb_base_url = "https://www.themealdb.com/api/json/v1/1"
        
        # SSL context for API requests
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        logger.info(f"Recipe Service initialized - Spoonacular API Key present: {bool(self.spoonacular_key)}")
        
    def _normalize_spoonacular_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Spoonacular recipe format"""
        try:
            return {
                "id": f"spoonacular_{recipe['id']}",  # Prefix to avoid ID conflicts
                "title": recipe.get('title', ''),
                "image": recipe.get('image', ''),
                "source": "spoonacular",
                "source_url": recipe.get('sourceUrl', ''),
                "servings": recipe.get('servings', 0),
                "ready_in_minutes": recipe.get('readyInMinutes', 0),
                "cuisines": recipe.get('cuisines', []),
                "diets": recipe.get('diets', []),
                "dish_types": recipe.get('dishTypes', []),
                "instructions": recipe.get('instructions', ''),
                "ingredients": [
                    {
                        "name": ing.get('name', ''),
                        "amount": ing.get('amount', 0),
                        "unit": ing.get('unit', '')
                    }
                    for ing in recipe.get('extendedIngredients', [])
                ],
                "cached_at": int(time.time())
            }
        except Exception as e:
            logger.error(f"Error normalizing Spoonacular recipe: {e}")
            return None

    def _normalize_mealdb_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize TheMealDB recipe format"""
        try:
            # Extract ingredients from numbered fields
            ingredients = []
            for i in range(1, 21):  # TheMealDB has up to 20 ingredients
                ingredient = recipe.get(f'strIngredient{i}')
                measure = recipe.get(f'strMeasure{i}')
                if ingredient and ingredient.strip():
                    ingredients.append({
                        "name": ingredient.strip(),
                        "amount": 1,  # Default amount since measure might be like "to taste"
                        "unit": measure.strip() if measure else ""
                    })

            return {
                "id": f"mealdb_{recipe['idMeal']}",  # Prefix to avoid ID conflicts
                "title": recipe.get('strMeal', ''),
                "image": recipe.get('strMealThumb', ''),
                "source": "themealdb",
                "source_url": recipe.get('strSource', ''),
                "servings": 4,  # Default since TheMealDB doesn't provide this
                "ready_in_minutes": 30,  # Default since TheMealDB doesn't provide this
                "cuisines": [recipe.get('strArea', 'International')],
                "diets": [],  # TheMealDB doesn't provide diet info
                "dish_types": [recipe.get('strCategory', '')],
                "instructions": recipe.get('strInstructions', ''),
                "ingredients": ingredients,
                "cached_at": int(time.time())
            }
        except Exception as e:
            logger.error(f"Error normalizing MealDB recipe: {e}")
            return None

    async def search_recipes(self, query: str = "", ingredient: str = "", offset: int = 0) -> List[Dict[str, Any]]:
        """Search recipes from multiple sources"""
        all_recipes = []
        errors = []

        logger.info(f"Starting recipe search - Query: '{query}', Ingredient: '{ingredient}', Offset: {offset}")

        # Try TheMealDB first since it's free and more reliable
        try:
            logger.info("Attempting TheMealDB search...")
            # TheMealDB has different endpoints for search vs ingredient
            if ingredient:
                url = f"{self.mealdb_base_url}/filter.php"
                params = {"i": ingredient}
                logger.info(f"Using TheMealDB ingredient search: {url} with params {params}")
            elif query:
                url = f"{self.mealdb_base_url}/search.php"
                params = {"s": query}
                logger.info(f"Using TheMealDB text search: {url} with params {params}")
            else:
                url = f"{self.mealdb_base_url}/search.php"
                params = {"f": "a"}
                logger.info("No search terms, using default TheMealDB search")

            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params, timeout=10) as response:
                    logger.info(f"TheMealDB response status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        meals = data.get('meals', [])
                        logger.info(f"TheMealDB returned {len(meals) if meals else 0} initial results")
                        
                        if meals:
                            # For ingredient search, we need to fetch full recipe details
                            if ingredient:
                                detailed_meals = []
                                logger.info("Fetching detailed recipe information for ingredient search...")
                                for meal in meals:
                                    async with session.get(
                                        f"{self.mealdb_base_url}/lookup.php",
                                        params={"i": meal['idMeal']},
                                        timeout=10
                                    ) as detail_response:
                                        if detail_response.status == 200:
                                            detail_data = await detail_response.json()
                                            if detail_data.get('meals'):
                                                detailed_meals.extend(detail_data['meals'])
                                meals = detailed_meals
                                logger.info(f"Retrieved {len(detailed_meals)} detailed recipes")

                            mealdb_recipes = [
                                recipe for recipe in [
                                    self._normalize_mealdb_recipe(recipe)
                                    for recipe in meals
                                    if recipe
                                ]
                                if recipe is not None
                            ]
                            logger.info(f"Successfully normalized {len(mealdb_recipes)} TheMealDB recipes")
                            all_recipes.extend(mealdb_recipes)
                            
                            # Cache the recipes
                            if mealdb_recipes:
                                try:
                                    await asyncio.to_thread(
                                        self.recipe_cache.cache_recipes,
                                        mealdb_recipes,
                                        query,
                                        ingredient
                                    )
                                    logger.info(f"Cached {len(mealdb_recipes)} TheMealDB recipes")
                                except Exception as cache_error:
                                    logger.error(f"Failed to cache TheMealDB recipes: {cache_error}")
                    else:
                        error_msg = f"TheMealDB API error: {response.status}"
                        logger.error(error_msg)
                        errors.append(error_msg)
        except Exception as e:
            error_msg = f"TheMealDB API error: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

        # Try Spoonacular second (if we have an API key)
        if self.spoonacular_key:
            try:
                logger.info("Attempting Spoonacular search...")
                params = {
                    "apiKey": self.spoonacular_key,
                    "number": 100,
                    "offset": offset,
                    "addRecipeInformation": "true",
                    "fillIngredients": "true",
                    "instructionsRequired": "true"
                }
                
                if query:
                    params["query"] = query
                if ingredient:
                    params["includeIngredients"] = ingredient

                logger.info(f"Spoonacular search URL: {self.spoonacular_search_url}")
                connector = aiohttp.TCPConnector(ssl=self.ssl_context)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(self.spoonacular_search_url, params=params, timeout=10) as response:
                        logger.info(f"Spoonacular response status: {response.status}")
                        if response.status == 200:
                            data = await response.json()
                            if "results" in data:
                                spoonacular_recipes = [
                                    recipe for recipe in [
                                        self._normalize_spoonacular_recipe(r)
                                        for r in data["results"]
                                    ]
                                    if recipe is not None
                                ]
                                logger.info(f"Successfully normalized {len(spoonacular_recipes)} Spoonacular recipes")
                                all_recipes.extend(spoonacular_recipes)
                                
                                # Cache the recipes
                                if spoonacular_recipes:
                                    try:
                                        await asyncio.to_thread(
                                            self.recipe_cache.cache_recipes,
                                            spoonacular_recipes,
                                            query,
                                            ingredient
                                        )
                                        logger.info(f"Cached {len(spoonacular_recipes)} Spoonacular recipes")
                                    except Exception as cache_error:
                                        logger.error(f"Failed to cache Spoonacular recipes: {cache_error}")
                        else:
                            error_msg = f"Spoonacular API error: {response.status}"
                            logger.error(error_msg)
                            errors.append(error_msg)
            except Exception as e:
                error_msg = f"Spoonacular API error: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Log final results
        logger.info(f"Search complete - Found {len(all_recipes)} total recipes")
        if errors:
            logger.warning("Search errors encountered: " + "; ".join(errors))

        if not all_recipes and errors:
            # Only raise an error if we have no results and encountered errors
            raise Exception("Failed to fetch recipes: " + "; ".join(errors))

        return all_recipes

    async def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get recipe details by ID"""
        # Check cache first
        cached_recipe = self.recipe_cache.get_recipe_by_id(recipe_id)
        if cached_recipe:
            return cached_recipe

        try:
            # Parse source and ID from the combined ID
            source, original_id = recipe_id.split('_', 1)
            
            if source == 'spoonacular' and self.spoonacular_key:
                # Get from Spoonacular
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.spoonacular_base_url}/recipes/{original_id}/information",
                        params={"apiKey": self.spoonacular_key},
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            recipe = self._normalize_spoonacular_recipe(data)
                            if recipe:
                                await asyncio.to_thread(self.recipe_cache.cache_recipe, recipe)
                                return recipe
                        else:
                            logger.error(f"Spoonacular API error: {response.status}")
                            
            elif source == 'mealdb':
                # Get from TheMealDB
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.mealdb_base_url}/lookup.php",
                        params={"i": original_id},
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('meals'):
                                recipe = self._normalize_mealdb_recipe(data['meals'][0])
                                if recipe:
                                    await asyncio.to_thread(self.recipe_cache.cache_recipe, recipe)
                                    return recipe
                        else:
                            logger.error(f"TheMealDB API error: {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching recipe {recipe_id}: {e}")
            return None