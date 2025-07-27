import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecipeService:
    def __init__(self, recipe_cache):
        """
        Initialize the RecipeService to work with local cache only.
        
        Args:
            recipe_cache: The recipe cache instance to use for storing/retrieving recipes
        """
        self.recipe_cache = recipe_cache
        logger.info("Recipe Service initialized in local-only mode - no API calls will be made")
    
    async def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a recipe by its ID from the local cache only.
        
        Args:
            recipe_id: The ID of the recipe to retrieve
            
        Returns:
            The recipe dictionary if found, None otherwise
        """
        # Only check cache - no API calls will be made
        cached_recipe = self.recipe_cache.get_recipe_by_id(recipe_id)
        
        if not cached_recipe:
            logger.warning(f"Recipe not found in cache: {recipe_id}")
            return None
            
        # Ensure the cached recipe has consistent formatting
        if 'instructions' not in cached_recipe or not cached_recipe['instructions']:
            cached_recipe['instructions'] = ['No instructions provided.']
        elif isinstance(cached_recipe['instructions'], str):
            # Re-normalize instructions if they're stored as a string
            cached_recipe['instructions'] = [cached_recipe['instructions']]
                
        return cached_recipe

    def _matches_query(self, recipe: Dict[str, Any], query: str) -> bool:
        """Check if a recipe matches the search query."""
        if not query:
            return True
            
        query = query.lower()
        
        # Check title
        if 'title' in recipe and query in recipe['title'].lower():
            return True
            
        # Check description
        if 'description' in recipe and query in recipe['description'].lower():
            return True
            
        # Check ingredients
        if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
            for ing in recipe['ingredients']:
                if isinstance(ing, dict) and 'name' in ing and query in ing['name'].lower():
                    return True
                elif isinstance(ing, str) and query in ing.lower():
                    return True
                    
        return False
        
    def _contains_ingredient(self, recipe: Dict[str, Any], ingredient: str) -> bool:
        """Check if a recipe contains the specified ingredient."""
        if not ingredient:
            return True
            
        ingredient = ingredient.lower()
        
        if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
            for ing in recipe['ingredients']:
                if isinstance(ing, dict) and 'name' in ing and ingredient in ing['name'].lower():
                    return True
                elif isinstance(ing, str) and ingredient in ing.lower():
                    return True
                    
        return False
        
    def _matches_cuisine(self, recipe: Dict[str, Any], cuisines: List[str]) -> bool:
        """Check if a recipe matches any of the specified cuisines."""
        if not cuisines:
            return True
            
        # Get cuisines from various possible fields in the recipe
        recipe_cuisines = set()
        
        if 'cuisines' in recipe and isinstance(recipe['cuisines'], list):
            recipe_cuisines.update(c.lower() for c in recipe['cuisines'] if isinstance(c, str))
        if 'cuisine' in recipe and isinstance(recipe['cuisine'], list):
            recipe_cuisines.update(c.lower() for c in recipe['cuisine'] if isinstance(c, str))
        if 'cuisine' in recipe and isinstance(recipe['cuisine'], str):
            recipe_cuisines.add(recipe['cuisine'].lower())
            
        # Check if any of the recipe's cuisines match the filter
        for cuisine in cuisines:
            if not cuisine:
                continue
            cuisine_lower = cuisine.lower()
            for recipe_cuisine in recipe_cuisines:
                if cuisine_lower in recipe_cuisine or recipe_cuisine in cuisine_lower:
                    return True
        return False
        
    def _matches_dietary_restrictions(self, recipe: Dict[str, Any], restrictions: List[str]) -> bool:
        """Check if a recipe matches all the specified dietary restrictions."""
        if not restrictions:
            return True
            
        # Get dietary restrictions from various possible fields
        recipe_restrictions = set()
        
        if 'diets' in recipe and isinstance(recipe['diets'], list):
            recipe_restrictions.update(d.lower() for d in recipe['diets'] if isinstance(d, str))
        if 'dietary_restrictions' in recipe and isinstance(recipe['dietary_restrictions'], list):
            recipe_restrictions.update(d.lower() for d in recipe['dietary_restrictions'] if isinstance(d, str))
            
        # For vegetarian/vegan, also check ingredients
        if 'vegetarian' in restrictions or 'vegan' in restrictions:
            ingredients = []
            if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
                ingredients = [
                    ing['name'].lower() if isinstance(ing, dict) and 'name' in ing 
                    else ing.lower() if isinstance(ing, str) 
                    else str(ing).lower() 
                    for ing in recipe['ingredients']
                ]
            
            non_veg_ingredients = ['meat', 'chicken', 'beef', 'pork', 'fish', 'shrimp', 'bacon', 'sausage', 
                                 'steak', 'ham', 'turkey', 'duck', 'goose', 'venison', 'lamb']
            
            if any(ing in ' '.join(ingredients) for ing in non_veg_ingredients):
                recipe_restrictions.discard('vegetarian')
                recipe_restrictions.discard('vegan')
                
        # For vegan, also check for dairy/eggs
        if 'vegan' in restrictions:
            non_vegan_ingredients = ['egg', 'cheese', 'milk', 'butter', 'yogurt', 'honey', 'gelatin']
            if any(ing in ' '.join(ingredients) for ing in non_vegan_ingredients):
                recipe_restrictions.discard('vegan')
        
        # Check if all required restrictions are met
        required_restrictions = set(r.lower() for r in restrictions if r)
        return required_restrictions.issubset(recipe_restrictions)

    async def search_recipes(self, query: str = "", ingredient: str = "", 
                           offset: int = 0, limit: int = 1000,
                           cuisines: List[str] = None, 
                           dietary_restrictions: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search recipes from local cache with filtering.
        
        Args:
            query: Search query string to match against title, description, or ingredients
            ingredient: Filter by ingredient name
            offset: Pagination offset
            limit: Maximum number of results to return (default: 1000)
            
        Returns:
            List of filtered recipe dictionaries from local cache
        """
        logger.info(f"Searching recipes with query='{query}', ingredient='{ingredient}'")
        
        # Get all recipes from cache
        all_recipes = self.recipe_cache.get_cached_recipes()
        
        if not all_recipes:
            logger.warning("No recipes found in local cache")
            return []
            
        logger.info(f"Found {len(all_recipes)} total recipes in cache")
        
        # Filter recipes based on query, ingredient, cuisine, and dietary restrictions
        filtered_recipes = []
        for recipe in all_recipes:
            if not isinstance(recipe, dict) or 'id' not in recipe:
                continue
                
            # Check if recipe matches all criteria
            matches_query = self._matches_query(recipe, query)
            has_ingredient = self._contains_ingredient(recipe, ingredient)
            matches_cuisine = self._matches_cuisine(recipe, cuisines or [])
            matches_diet = self._matches_dietary_restrictions(recipe, dietary_restrictions or [])
            
            if all([matches_query, has_ingredient, matches_cuisine, matches_diet]):
                filtered_recipes.append(recipe)
        
        # Apply offset and limit
        start_idx = min(offset, len(filtered_recipes))
        end_idx = min(offset + limit, len(filtered_recipes))
        paginated_recipes = filtered_recipes[start_idx:end_idx]
        
        logger.info(f"Returning {len(paginated_recipes)} of {len(filtered_recipes)} matching recipes")
        return paginated_recipes
