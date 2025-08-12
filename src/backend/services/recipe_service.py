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
            
            # Parse instructions properly
            raw_instructions = meal_data.get('strInstructions', '')
            if raw_instructions:
                # Use the improved parsing logic
                parsed_instructions = self._parse_instructions(raw_instructions)
                instructions = parsed_instructions
            else:
                instructions = []
            
            # Create the normalized recipe
            recipe = {
                'id': f"mealdb_{meal_data['idMeal']}",
                'title': meal_data['strMeal'],
                'description': meal_data.get('strInstructions', '')[:200] + '...' if meal_data.get('strInstructions') else '',
                'image': meal_data.get('strMealThumb', ''),
                'cuisine': meal_data.get('strArea', 'International'),
                'cuisines': [meal_data.get('strArea', 'International')],
                'ingredients': ingredients,
                'instructions': instructions,
                'source': 'themealdb',
                'type': 'spoonacular',  # For compatibility with existing frontend
                'servings': 4,  # Default since TheMealDB doesn't provide this
                'ready_in_minutes': 30,  # Default estimate
                'diets': [],  # TheMealDB doesn't provide diet info
                'dietaryRestrictions': []  # For compatibility
            }
            
            return recipe
            
        except Exception as e:
            logger.error(f"Error normalizing TheMealDB recipe: {e}")
            return None
    
    def _parse_instructions(self, instructions_text: str) -> List[str]:
        """Parse recipe instructions into individual steps"""
        if not instructions_text:
            return ['No instructions provided.']
        
        # Clean up the instructions - preserve original structure but normalize whitespace
        instructions_text = instructions_text.replace('\r\n', '\n').replace('\r', '\n')
        
        # First, try to split by actual numbered steps (e.g., "1.", "1)", "Step 1:")
        import re
        
        # Look for actual step numbers at the beginning of lines or after periods
        # This pattern is more conservative and won't split on measurements
        step_pattern = r'(?:\n\s*\d+[.)]|\A\s*\d+[.)])'
        
        # Split by the step pattern
        raw_steps = re.split(f'({step_pattern})', instructions_text, flags=re.MULTILINE)
        
        # Clean up the split results
        steps = []
        current_step = ''
        
        for i, part in enumerate(raw_steps):
            part = part.strip()
            if not part:
                continue
                
            # If this part is a step number/indicator
            if re.match(f'^{step_pattern}$', part, flags=re.MULTILINE):
                if current_step:  # Save the previous step if exists
                    steps.append(current_step.strip())
                current_step = part + ' '  # Start new step with the number
            else:
                current_step += part + ' '
        
        # Add the last step if it exists
        if current_step.strip():
            steps.append(current_step.strip())
        
        # If we couldn't split by numbers, try other methods
        if len(steps) <= 1:
            # Try splitting by double newlines first (preserve natural paragraph breaks)
            steps = [s.strip() for s in instructions_text.split('\n\n') if s.strip()]
            
            # If that doesn't work, try splitting by single newlines that look like step separators
            if len(steps) <= 1:
                # Look for newlines that are followed by capital letters (likely new steps)
                steps = [s.strip() for s in re.split(r'\n(?=\s*[A-Z])', instructions_text) if s.strip()]
        
        # Clean up each step - remove leading numbers and normalize
        cleaned_steps = []
        for step in steps:
            if step:
                # Remove leading step numbers
                cleaned_step = re.sub(r'^\s*\d+[.)]?\s*', '', step).strip()
                if cleaned_step:
                    # Normalize whitespace within the step
                    cleaned_step = ' '.join(cleaned_step.split())
                    cleaned_steps.append(cleaned_step)
        
        # If we still don't have multiple steps, try to split by cooking action keywords
        if len(cleaned_steps) <= 1 and instructions_text:
            # Look for common cooking instruction patterns that indicate new steps
            cooking_keywords = [
                'preheat', 'heat', 'add', 'stir', 'mix', 'combine', 'pour', 'bake', 'cook', 'fry',
                'grill', 'roast', 'boil', 'simmer', 'season', 'salt', 'pepper', 'drain', 'remove',
                'serve', 'garnish', 'decorate', 'cool', 'chill', 'refrigerate', 'freeze', 'place',
                'transfer', 'return', 'bring', 'lower', 'cover', 'uncover', 'flip', 'turn'
            ]
            
            # Split by sentences that contain cooking keywords
            sentences = re.split(r'[.!?]+', instructions_text)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 15:  # Only meaningful sentences
                    # Check if sentence contains cooking keywords
                    if any(keyword in sentence.lower() for keyword in cooking_keywords):
                        cleaned_steps.append(sentence)
        
        # If all else fails, try to split by periods that end sentences
        if len(cleaned_steps) <= 1:
            # More intelligent sentence splitting that doesn't break on measurements
            # Look for periods followed by space and capital letter, but avoid breaking on measurements
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z][a-z])', instructions_text)
            cleaned_steps = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
        
        # Ensure we have at least one step
        if not cleaned_steps:
            cleaned_steps = [instructions_text.strip()]
        
        return cleaned_steps

# Singleton instance
recipe_service = RecipeService()
