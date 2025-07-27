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
        
    def _normalize_spoonacular_recipe(self, recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize Spoonacular recipe format with enhanced dietary info"""
        try:
            # Extract ingredients
            ingredients = []
            for ing in recipe.get('extendedIngredients', []):
                ingredients.append({
                    "name": ing.get('name', '').lower(),
                    "amount": ing.get('amount', 1),
                    "unit": ing.get('unit', '')
                })
            
            # Get dietary restrictions from both API flags and ingredient analysis
            api_diets = []
            if recipe.get('vegetarian', False):
                api_diets.append('vegetarian')
            if recipe.get('vegan', False):
                api_diets.append('vegan')
            if recipe.get('glutenFree', False):
                api_diets.append('gluten-free')
            if recipe.get('dairyFree', False):
                api_diets.append('dairy-free')
                
            # Also analyze ingredients to catch any the API might have missed
            ingredient_based_diets = self._get_dietary_restrictions(ingredients)
            
            # Combine both lists and remove duplicates
            diets = list(set(api_diets + ingredient_based_diets))
            
            return {
                "id": f"spoonacular_{recipe['id']}",  # Prefix to avoid ID conflicts
                "title": recipe.get('title', ''),
                "image": recipe.get('image', ''),
                "source": "spoonacular",
                "source_url": recipe.get('sourceUrl', ''),
                "servings": recipe.get('servings', 0),
                "ready_in_minutes": recipe.get('readyInMinutes', 0),
                "cuisines": recipe.get('cuisines', []),
                "diets": diets,
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

    def _get_dietary_restrictions(self, ingredients: List[Dict[str, Any]]) -> List[str]:
        """Determine dietary restrictions based on ingredients"""
        if not ingredients:
            return []
            
        # Initialize dietary flags
        is_vegetarian = True
        is_vegan = True
        is_gluten_free = True
        contains_dairy = False
        
        # Common ingredient keywords for dietary restrictions
        non_veg_keywords = {'beef', 'chicken', 'pork', 'lamb', 'fish', 'seafood', 'bacon', 
                          'sausage', 'meat', 'poultry', 'ham', 'salami', 'pepperoni', 'gelatin',
                          'anchovy', 'shrimp', 'prawn', 'lobster', 'crab', 'oyster', 'mussel',
                          'squid', 'octopus', 'duck', 'goose', 'venison', 'bison', 'rabbit'}
                          
        dairy_keywords = {'milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein',
                        'lactose', 'ghee', 'sour cream', 'buttermilk', 'custard'}
                        
        gluten_keywords = {'wheat', 'barley', 'rye', 'bread', 'pasta', 'flour', 'couscous',
                         'bulgur', 'semolina', 'spelt', 'farro', 'kamut', 'triticale', 'malt',
                         'beer', 'ale', 'lager', 'soy sauce', 'teriyaki', 'seitan'}
        
        # Check each ingredient
        for ing in ingredients:
            if not isinstance(ing, dict):
                continue
                
            ingredient_name = str(ing.get('name', '')).lower()
            if not ingredient_name:
                continue
                
            # Check for non-vegetarian ingredients
            if any(keyword in ingredient_name for keyword in non_veg_keywords):
                is_vegetarian = False
                is_vegan = False
                
            # Check for dairy
            if any(keyword in ingredient_name for keyword in dairy_keywords):
                contains_dairy = True
                
            # Check for gluten
            if any(keyword in ingredient_name for keyword in gluten_keywords):
                is_gluten_free = False
        
        # Build dietary restrictions list
        diets = []
        if is_vegetarian:
            diets.append('vegetarian')
            if is_vegan and not contains_dairy:
                diets.append('vegan')
        if is_gluten_free:
            diets.append('gluten-free')
        if not contains_dairy:
            diets.append('dairy-free')
            
        return diets

    def _normalize_mealdb_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize TheMealDB recipe format with enhanced dietary info"""
        try:
            # Extract ingredients from numbered fields
            ingredients = []
            
            for i in range(1, 21):  # TheMealDB has up to 20 ingredients
                ingredient = (recipe.get(f'strIngredient{i}') or '').strip()
                measure = (recipe.get(f'strMeasure{i}') or '').strip()
                
                if ingredient:
                    ingredients.append({
                        "name": ingredient,
                        "amount": 1,  # Default amount since measure might be like "to taste"
                        "unit": measure if measure else ""
                    })
            
            # Get dietary restrictions
            diets = self._get_dietary_restrictions(ingredients)
            
            # Get cooking time from instructions if possible
            instructions = recipe.get('strInstructions', '')
            ready_in_minutes = 30  # Default
            
            # Try to estimate cooking time from instructions
            if 'minute' in instructions.lower():
                import re
                time_matches = re.findall(r'(\d+)\s*min', instructions, re.IGNORECASE)
                if time_matches:
                    times = [int(t) for t in time_matches if t.isdigit()]
                    if times:
                        ready_in_minutes = max(times)  # Take the longest time mentioned
            
            return {
                "id": f"mealdb_{recipe['idMeal']}",  # Prefix to avoid ID conflicts
                "title": recipe.get('strMeal', 'Untitled Recipe').strip(),
                "image": recipe.get('strMealThumb', ''),
                "source": "themealdb",
                "source_url": recipe.get('strSource', ''),
                "servings": 4,  # Default since TheMealDB doesn't provide this
                "ready_in_minutes": ready_in_minutes,
                "cuisines": [recipe.get('strArea', 'International').strip()] if recipe.get('strArea') else ['International'],
                "diets": diets,
                "dish_types": [recipe.get('strCategory', '').strip()] if recipe.get('strCategory') else [],
                "instructions": instructions,
                "ingredients": ingredients,
                "cached_at": int(time.time())
            }
        except Exception as e:
            logger.error(f"Error normalizing MealDB recipe: {e}")
            return None

    async def search_recipes(self, query: str = "", ingredient: str = "", offset: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Search recipes from multiple sources with enhanced result handling
        
        Args:
            query: Search query string
            ingredient: Filter by ingredient
            offset: Pagination offset
            limit: Maximum number of results to return (default: 1000)
            
        Returns:
            List of recipe dictionaries
        """
        all_recipes = []
        errors = []
        search_terms = f"Query: '{query}'", f"Ingredient: '{ingredient}'", f"Offset: {offset}"
        logger.info(f"Starting recipe search - {', '.join(term for term in search_terms if term)}")

        # Check cache first
        try:
            # Get cached recipes with a higher limit to allow for better filtering
            cached_recipes = self.recipe_cache.get_cached_recipes(query, ingredient)
            if cached_recipes:
                logger.info(f"Found {len(cached_recipes)} recipes in cache")
                # Apply offset and limit to cached results
                return cached_recipes[offset:offset + limit]
        except Exception as e:
            logger.warning(f"Error checking cache: {e}")
            # Continue with API calls if cache check fails

        # If we get here, either cache was empty or there was an error
        logger.info("No valid cache found, proceeding with API calls")

        # Track if we've found any recipes from any source
        found_recipes = False
        
        # Only make API calls if we didn't find any cached results
        if not all_recipes:
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
                
                # Initialize response variable to avoid UnboundLocalError
                response = None

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
                                
                                if mealdb_recipes:
                                    found_recipes = True
                                    all_recipes.extend(mealdb_recipes)
                                    
                                    # Only cache recipes that aren't already in the cache
                                    try:
                                        # Filter out recipes that are already in the cache
                                        recipe_ids = [str(r['id']) for r in mealdb_recipes]
                                        existing_recipes = await asyncio.to_thread(
                                            self.recipe_cache.get_recipes_by_ids,
                                            recipe_ids
                                        )
                                        existing_ids = {r['id'] for r in existing_recipes if r}
                                        new_recipes = [r for r in mealdb_recipes if str(r['id']) not in existing_ids]
                                        
                                        if new_recipes:
                                            await asyncio.to_thread(
                                                self.recipe_cache.cache_recipes,
                                                new_recipes,
                                                query,
                                                ingredient
                                            )
                                            logger.info(f"Cached {len(new_recipes)} new TheMealDB recipes")
                                        else:
                                            logger.debug("All recipes already in cache")
                                    except Exception as cache_error:
                                        logger.error(f"Failed to check/cache TheMealDB recipes: {cache_error}")
                        else:
                            error_msg = f"TheMealDB API error: {response.status}"
                            logger.error(error_msg)
                            errors.append(error_msg)
            except aiohttp.ClientError as e:
                error_msg = f"TheMealDB API request failed: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"TheMealDB API error: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Only try Spoonacular if we didn't find any recipes from TheMealDB
        if not found_recipes and self.spoonacular_key:
            try:
                logger.info("No recipes found in TheMealDB, trying Spoonacular...")
                params = {
                    "apiKey": self.spoonacular_key,
                    "number": min(100, limit),  # Use the provided limit, but cap at 100 to avoid API limits
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
                            if "results" in data and data["results"]:
                                spoonacular_recipes = [
                                    recipe for recipe in [
                                        self._normalize_spoonacular_recipe(r)
                                        for r in data["results"]
                                    ]
                                    if recipe is not None
                                ]
                                logger.info(f"Successfully normalized {len(spoonacular_recipes)} Spoonacular recipes")
                                
                                if spoonacular_recipes:
                                    all_recipes.extend(spoonacular_recipes)
                                    
                                    # Cache the recipes
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