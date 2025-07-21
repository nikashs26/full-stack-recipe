import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from services.recipe_cache_service import RecipeCacheService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecipeService:
    def __init__(self):
        """Initialize the RecipeService with configuration"""
        # TheMealDB configuration
        self.mealdb_base_url = "https://www.themealdb.com/api/json/v1/1"
        
        # Initialize cache service
        self.cache = RecipeCacheService()
    
    def search_mealdb_recipes(
        self, 
        search_term: Optional[str] = None, 
        cuisine: Optional[str] = None,
        limit: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Search for recipes in TheMealDB
        
        Args:
            search_term: Optional search term
            cuisine: Optional cuisine filter
            limit: Maximum number of results to return
            
        Returns:
            List of recipe dictionaries
        """
        try:
            # Build the API URL based on search parameters
            if cuisine and cuisine.lower() != 'all':
                # Search by cuisine
                url = f"{self.mealdb_base_url}/filter.php"
                params = {'a': cuisine}
            elif search_term:
                # Search by name
                url = f"{self.mealdb_base_url}/search.php"
                params = {'s': search_term}
            else:
                # Get random recipes if no search term or cuisine
                url = f"{self.mealdb_base_url}/random.php"
                params = {}
            
            logger.info(f"Calling TheMealDB API: {url} with params: {params}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            meals = data.get('meals', [])
            
            if not meals:
                logger.info("No recipes found in TheMealDB response")
                return []
            
            # Limit results
            meals = meals[:limit]
            
            # Get detailed information for each recipe
            recipes = []
            for meal in meals:
                recipe = self._normalize_mealdb_recipe(meal)
                if recipe:
                    recipes.append(recipe)
            
            logger.info(f"Successfully fetched {len(recipes)} recipes from TheMealDB")
            return recipes
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling TheMealDB API: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in search_mealdb_recipes: {str(e)}")
            return []
    
    def get_mealdb_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific recipe from TheMealDB by ID
        
        Args:
            recipe_id: TheMealDB recipe ID
            
        Returns:
            Recipe dictionary or None if not found
        """
        try:
            # Clean the ID (in case it has the 'mealdb_' prefix)
            clean_id = str(recipe_id).replace('mealdb_', '')
            
            # Call TheMealDB API
            url = f"{self.mealdb_base_url}/lookup.php"
            response = requests.get(url, params={'i': clean_id})
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            meal = data.get('meals', [{}])[0] if data.get('meals') else None
            
            if not meal:
                logger.warning(f"Recipe not found in TheMealDB: {recipe_id}")
                return None
            
            # Normalize the recipe data
            return self._normalize_mealdb_recipe(meal)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching recipe from TheMealDB: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_mealdb_recipe: {str(e)}")
            return None
    
    def get_mealdb_cuisines(self) -> List[str]:
        """
        Get a list of available cuisine areas from TheMealDB
        
        Returns:
            List of cuisine names
        """
        try:
            # Check cache first
            cache_key = "mealdb_cuisines"
            cached = self.cache.get(cache_key)
            if cached:
                return cached
            
            # Fetch from API if not in cache
            url = f"{self.mealdb_base_url}/list.php"
            response = requests.get(url, params={'a': 'list'})
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            cuisines = [area['strArea'] for area in data.get('meals', [])]
            
            # Cache the result for 1 day
            self.cache.set(cache_key, cuisines, ttl=86400)
            
            return cuisines
            
        except Exception as e:
            logger.error(f"Error fetching cuisines from TheMealDB: {str(e)}")
            # Return a default list if API call fails
            return ["American", "British", "Canadian", "Chinese", "French", 
                   "Indian", "Italian", "Japanese", "Mexican", "Spanish"]
    
    def _normalize_mealdb_recipe(self, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a recipe from TheMealDB to our standard format
        
        Args:
            meal_data: Raw recipe data from TheMealDB
            
        Returns:
            Normalized recipe dictionary
        """
        try:
            # Extract ingredients and measures
            ingredients = []
            for i in range(1, 21):  # TheMealDB has up to 20 ingredients
                ingredient = meal_data.get(f'strIngredient{i}', '').strip()
                measure = meal_data.get(f'strMeasure{i}', '').strip()
                
                if ingredient:
                    ingredients.append({
                        'name': ingredient,
                        'amount': measure if measure else '',
                        'unit': ''  # TheMealDB doesn't provide separate units
                    })
            
            # Create the normalized recipe
            recipe = {
                'id': f"mealdb_{meal_data['idMeal']}",
                'title': meal_data['strMeal'],
                'description': meal_data.get('strInstructions', '')[:200] + '...' if meal_data.get('strInstructions') else '',
                'image': meal_data.get('strMealThumb', ''),
                'cuisine': meal_data.get('strArea', 'International'),
                'cuisines': [meal_data.get('strArea', 'International')],
                'ingredients': ingredients,
                'instructions': meal_data.get('strInstructions', '').split('\r\n') if meal_data.get('strInstructions') else [],
                'source': 'themealdb',
                'type': 'spoonacular',  # For compatibility with existing frontend
                'servings': 4,  # Default since TheMealDB doesn't provide this
                'ready_in_minutes': 30,  # Default estimate
                'diets': [],  # TheMealDB doesn't provide diet info
                'dietaryRestrictions': []  # For compatibility
            }
            
            return recipe
            
        except Exception as e:
            logger.error(f"Error normalizing TheMealDB recipe: {str(e)}")
            return None

# Singleton instance
recipe_service = RecipeService()
