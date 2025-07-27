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
                "description": recipe.get('summary', '').replace('<b>', '').replace('</b>', ''),  # Clean HTML tags
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

    def _detect_cuisine_from_recipe(self, recipe: Dict[str, Any], ingredients: List[Dict[str, Any]]) -> str:
        """Enhanced cuisine detection for TheMealDB recipes. Always returns a specific cuisine, never 'International'."""
        # First try area and category
        area = recipe.get('strArea', '').strip()
        category = recipe.get('strCategory', '').strip()
        
        # Cuisine mapping with common variations
        CUISINE_MAPPING = {
            'American': ['American', 'Southern', 'Cajun', 'Creole', 'Soul Food', 'Jamaican', 'Barbadian'],
            'Italian': ['Italian', 'Tuscan', 'Sicilian', 'Roman', 'Venetian'],
            'Chinese': ['Chinese', 'Cantonese', 'Sichuan', 'Szechuan', 'Hunan'],
            'Japanese': ['Japanese', 'Sushi', 'Ramen', 'Udon', 'Sashimi'],
            'Mexican': ['Mexican', 'Tex-Mex', 'Yucatecan', 'Oaxacan'],
            'Indian': ['Indian', 'Pakistani', 'Bangladeshi', 'Punjabi', 'Kashmiri', 'Kerala', 'Tamil', 'Andhra'],
            'Thai': ['Thai', 'Isan', 'Lanna'],
            'French': ['French', 'Provencal', 'Provençal', 'Burgundian', 'Lyonnaise'],
            'Mediterranean': ['Mediterranean', 'Greek', 'Turkish', 'Lebanese', 'Moroccan', 'Tunisian', 'Algerian'],
            'Spanish': ['Spanish', 'Catalan', 'Basque', 'Galician', 'Valencian'],
            'Vietnamese': ['Vietnamese', 'Viet'],
            'Korean': ['Korean'],
            'Filipino': ['Filipino', 'Filipino-Chinese'],
            'British': ['British', 'English', 'Scottish', 'Welsh', 'Irish'],
            'German': ['German', 'Bavarian', 'Swabian'],
            'Russian': ['Russian', 'Ukrainian', 'Belarusian'],
            'Polish': ['Polish'],
            'Caribbean': ['Caribbean', 'Jamaican', 'Trinidadian', 'Barbadian', 'Bahamian'],
            'Latin American': ['Latin American', 'Brazilian', 'Peruvian', 'Argentinian', 'Colombian', 'Chilean'],
            'Middle Eastern': ['Middle Eastern', 'Iranian', 'Iraqi', 'Syrian', 'Jordanian', 'Israeli'],
            'African': ['African', 'Ethiopian', 'Nigerian', 'South African', 'North African', 'West African', 'East African']
        }
        
        # First try exact matches on area and category
        if area:
            area_lower = area.lower()
            for main_cuisine, aliases in CUISINE_MAPPING.items():
                if any(alias.lower() == area_lower for alias in [main_cuisine] + aliases):
                    return main_cuisine
        
        if category:
            category_lower = category.lower()
            for main_cuisine, aliases in CUISINE_MAPPING.items():
                if any(alias.lower() == category_lower for alias in [main_cuisine] + aliases):
                    return main_cuisine
        
        # Try partial matches on area and category
        if area:
            area_lower = area.lower()
            for main_cuisine, aliases in CUISINE_MAPPING.items():
                if any(alias.lower() in area_lower for alias in [main_cuisine] + aliases):
                    return main_cuisine
        
        # Try ingredient-based detection
        ingredient_text = ' '.join(str(ing.get('name', '')).lower() for ing in ingredients)
        
        # Common ingredient-based cuisine detection with more specific checks
        if any(ing in ingredient_text for ing in ['soy sauce', 'hoisin', 'oyster sauce', 'sichuan', 'szechuan', 'bok choy', 'five spice', 'chinese broccoli']):
            return 'Chinese'
        elif any(ing in ingredient_text for ing in ['curry', 'garam masala', 'tandoori', 'tikka', 'dal', 'naan', 'paneer', 'masala', 'chutney']):
            return 'Indian'
        elif any(ing in ingredient_text for ing in ['sriracha', 'fish sauce', 'lemongrass', 'coconut milk', 'kaffir lime', 'galangal']):
            if 'coconut milk' in ingredient_text or 'kaffir lime' in ingredient_text or 'galangal' in ingredient_text:
                return 'Thai'
            else:
                return 'Vietnamese'
        elif any(ing in ingredient_text for ing in ['tortilla', 'salsa', 'guacamole', 'quesadilla', 'enchilada', 'chipotle', 'adobo', 'poblano']):
            return 'Mexican'
        elif any(ing in ingredient_text for ing in ['pasta', 'risotto', 'parmesan', 'basil', 'oregano', 'prosciutto', 'mozzarella', 'balsamic', 'arugula']):
            return 'Italian'
        elif any(ing in ingredient_text for ing in ['kimchi', 'gochujang', 'gochugaru', 'bulgogi', 'bibimbap', 'korean chili', 'doenjang']):
            return 'Korean'
        elif any(ing in ingredient_text for ing in ['tahini', 'zaatar', 'sumac', 'falafel', 'hummus', 'pita', 'shawarma', 'labneh']):
            return 'Middle Eastern'
        elif any(ing in ingredient_text for ing in ['olive oil', 'feta', 'olives', 'tzatziki', 'gyro', 'halloumi', 'dolmades']):
            return 'Mediterranean'
        
        # Common American/European dishes
        if any(ing in ingredient_text for ing in ['apple', 'pie', 'pancake', 'fritter', 'biscuit', 'gravy', 'cornbread', 'barbecue', 'bbq']):
            return 'American'
        elif any(ing in ingredient_text for ing in ['kale', 'chard', 'collard', 'mustard greens', 'turnip greens']):
            # Common in both American and Mediterranean cuisines, but more specific checks first
            if any(ing in ingredient_text for ing in ['garlic', 'olive oil', 'lemon']):
                return 'Mediterranean'
            return 'American'
        elif any(ing in ingredient_text for ing in ['potato', 'cabbage', 'sausage', 'stew', 'shepherd', 'corned beef']):
            return 'British' if any(ing in ingredient_text for ing in ['shepherd', 'corned beef']) else 'American'
        
        # If we still can't determine, use the area or category as is if they're not empty
        if area and area.lower() not in ['', 'unknown', 'international']:
            # Try to find the closest match in our cuisine mapping
            area_lower = area.lower()
            for cuisine in CUISINE_MAPPING:
                if cuisine.lower() in area_lower:
                    return cuisine
            return area
            
        if category and category.lower() not in ['', 'unknown', 'international']:
            category_lower = category.lower()
            for cuisine in CUISINE_MAPPING:
                if cuisine.lower() in category_lower:
                    return cuisine
            return category
        
        # Final fallback - analyze ingredients for common patterns
        ingredient_count = {}
        for ing in ingredients:
            ing_name = str(ing.get('name', '')).lower()
            if not ing_name:
                continue
                
            # Count occurrences of ingredient names
            for cuisine_key in CUISINE_MAPPING:
                if cuisine_key.lower() in ing_name:
                    ingredient_count[cuisine_key] = ingredient_count.get(cuisine_key, 0) + 1
        
        # Return the most frequently mentioned cuisine in ingredients
        if ingredient_count:
            return max(ingredient_count.items(), key=lambda x: x[1])[0]
        
        # Last resort fallback - assign based on most common cuisines
        return 'American'  # Most common default

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

    def _normalize_mealdb_recipe(self, recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize TheMealDB recipe format with enhanced dietary info and description"""
        try:
            # Extract ingredients (they're stored as strIngredient1, strMeasure1, etc.)
            ingredients = []
            for i in range(1, 21):  # TheMealDB has up to 20 ingredients
                ingredient = recipe.get(f'strIngredient{i}', '').strip()
                measure = recipe.get(f'strMeasure{i}', '').strip()
                if ingredient and ingredient.lower() != '':
                    # Clean up the ingredient name
                    ingredient_name = ingredient.lower()
                    
                    # Clean up the measurement
                    amount = ''
                    unit = ''
                    
                    if measure:
                        # Handle measurements like '1 1/2 cups' or '2-3 tablespoons'
                        parts = measure.split(' ', 1)
                        if parts and any(c.isdigit() for c in parts[0]):
                            amount = parts[0].strip()
                            unit = parts[1].strip() if len(parts) > 1 else ''
                        else:
                            unit = measure.strip()
                    
                    ingredients.append({
                        'name': ingredient_name,
                        'amount': amount,
                        'unit': unit,
                        'original': f"{measure} {ingredient}".strip() if measure else ingredient
                    })
            
            # Get dietary restrictions
            diets = []
            if recipe.get('strTags'):
                tags = [tag.strip().lower() for tag in recipe['strTags'].split(',')]
                if 'vegetarian' in tags:
                    diets.append('vegetarian')
                if 'vegan' in tags:
                    diets.append('vegan')
                if 'glutenfree' in tags or 'gluten-free' in tags:
                    diets.append('gluten-free')
                if 'dairyfree' in tags or 'dairy-free' in tags:
                    diets.append('dairy-free')
            
            # If no diets from tags, try to detect from ingredients
            if not diets:
                diets = self._get_dietary_restrictions(ingredients)
            
            # Create a proper description
            category = recipe.get('strCategory', '').title() or 'delicious'
            area = recipe.get('strArea', '').title() or 'international'
            description = f"A {category} recipe"
            if area.lower() != 'unknown':
                description += f" from {area} cuisine"
            description += ". "
            
            # Add the first sentence from instructions as description if available
            instructions = recipe.get('strInstructions', '').strip()
            if instructions:
                # Take first sentence or first 200 chars
                first_period = instructions.find('.')
                if first_period > 0:
                    description += instructions[:first_period + 1]
                else:
                    description += instructions[:200] + ('...' if len(instructions) > 200 else '')
            
            # Clean up and format instructions
            instructions = recipe.get('strInstructions', '').strip()
            if instructions:
                # Replace \r\n with \n for consistency
                instructions = instructions.replace('\r\n', '\n')
                
                # Split into steps if they're numbered
                if any(char.isdigit() for char in instructions[:10]):
                    # Handle numbered steps (1., 2., etc.)
                    steps = []
                    current_step = ''
                    
                    # Split by lines first
                    for line in instructions.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                            
                        # Check if line starts with a number followed by a dot or parenthesis
                        if line and line[0].isdigit() and (line[1] in '. )' or line[1:3] in (') ', '. ')):
                            if current_step:  # Save previous step if exists
                                steps.append(current_step.strip())
                            current_step = line[line.find(' ')+1:].strip()  # Remove number and following dot/space
                        else:
                            if current_step:
                                current_step += ' ' + line
                            else:
                                current_step = line
                    
                    if current_step:  # Add the last step
                        steps.append(current_step.strip())
                    
                    if steps:  # If we found steps, use them
                        instructions = steps
                    else:  # Fallback to splitting by periods
                        steps = [s.strip() for s in instructions.split('.') if s.strip()]
                        instructions = [s + '.' for s in steps if not s.endswith('.')]
                else:
                    # If no numbering, try to split by double newlines
                    steps = [s.strip() for s in instructions.split('\n\n') if s.strip()]
                    if len(steps) > 1:
                        instructions = steps
                    else:
                        # As last resort, split by periods
                        steps = [s.strip() for s in instructions.split('.') if s.strip()]
                        instructions = [s + '.' for s in steps if not s.endswith('.')]
            
            # Ensure instructions is always an array
            if not instructions:
                instructions = ['No instructions provided.']
            elif isinstance(instructions, str):
                instructions = [instructions]
            
            # Get cuisine
            cuisine = self._detect_cuisine_from_recipe(recipe, ingredients)
            
            return {
                "id": f"themealdb_{recipe['idMeal']}",
                "title": recipe.get('strMeal', '').strip(),
                "description": description,
                "image": recipe.get('strMealThumb', ''),
                "source": "themealdb",
                "source_url": recipe.get('strSource', ''),
                "youtube_url": recipe.get('strYoutube', ''),
                "servings": 4,  # Default value
                "ready_in_minutes": 30,  # Default value
                "cuisines": [cuisine] if cuisine else [],
                "diets": diets,
                "dish_types": [recipe.get('strCategory', '')] if recipe.get('strCategory') else [],
                "instructions": instructions,
                "ingredients": ingredients,
                "cached_at": int(time.time())
            }
        except Exception as e:
            logger.error(f"Error normalizing TheMealDB recipe: {e}")
            return None
            
    async def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get recipe details by ID"""
        # Check cache first
        cached_recipe = self.recipe_cache.get_recipe_by_id(recipe_id)
        if cached_recipe:
            return cached_recipe

        try:
            # Parse source and ID from the combined ID
            if '_' in recipe_id:
                source, original_id = recipe_id.split('_', 1)
            else:
                # Handle case where ID doesn't have a prefix (for backward compatibility)
                source = 'themealdb'
                original_id = recipe_id
            
            if source == 'spoonacular' and self.spoonacular_key:
                # Get from Spoonacular
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.spoonacular_base_url}/recipes/{original_id}/information",
                        params={
                            'apiKey': self.spoonacular_key,
                            'includeNutrition': 'false'
                        },
                        ssl=self.ssl_context
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            recipe = self._normalize_spoonacular_recipe(data)
                            if recipe:
                                await asyncio.to_thread(self.recipe_cache.cache_recipe, recipe)
                                return recipe
            elif source == 'themealdb':
                # Get from TheMealDB - ensure we're using just the numeric part of the ID
                numeric_id = ''.join(c for c in original_id if c.isdigit())
                if not numeric_id:
                    logger.error(f"Invalid TheMealDB ID format: {original_id}")
                    return None
                    
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.mealdb_base_url}/lookup.php?i={numeric_id}",
                        ssl=self.ssl_context
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and data.get('meals'):
                                recipe = self._normalize_mealdb_recipe(data['meals'][0])
                                if recipe:
                                    # Ensure the recipe has the correct ID format for future lookups
                                    recipe['id'] = f"themealdb_{numeric_id}"
                                    await asyncio.to_thread(self.recipe_cache.cache_recipe, recipe)
                                    return recipe
                        else:
                            logger.error(f"TheMealDB API error: {response.status}")
                            logger.error(f"URL: {self.mealdb_base_url}/lookup.php?i={numeric_id}")
                            logger.error(f"Response: {await response.text()}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching recipe {recipe_id}: {e}")
            return None