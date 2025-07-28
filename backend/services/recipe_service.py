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
        """
        Check if a recipe matches any of the specified cuisines.
        All recipes are included by default if no cuisine filter is applied.
        The 'international' tag is always excluded from matching.
        """
        if not cuisines:
            return True
            
        # Normalize the input cuisines (convert to lowercase and strip whitespace)
        recipe_cuisines = set()
        
        # Check 'cuisine' field
        if 'cuisine' in recipe and recipe['cuisine']:
            if isinstance(recipe['cuisine'], str):
                recipe_cuisines.add(recipe['cuisine'].lower())
            elif isinstance(recipe['cuisine'], list):
                recipe_cuisines.update(c.lower() for c in recipe['cuisine'] if c and isinstance(c, str))
        
        # Check 'cuisines' field
        if 'cuisines' in recipe and recipe['cuisines']:
            if isinstance(recipe['cuisines'], str):
                recipe_cuisines.add(recipe['cuisines'].lower())
            elif isinstance(recipe['cuisines'], list):
                recipe_cuisines.update(c.lower() for c in recipe['cuisines'] if c and isinstance(c, str))
        
        # Check 'tags' field for common cuisine tags
        if 'tags' in recipe and isinstance(recipe['tags'], list):
            cuisine_tags = [
                'american', 'italian', 'mexican', 'chinese', 'indian', 'japanese', 'thai', 'french', 'greek', 'spanish',
                'mediterranean', 'middle eastern', 'vietnamese', 'korean', 'german', 'british', 'caribbean', 'african',
                'latin american', 'cajun', 'southern', 'soul food', 'southwestern', 'hawaiian', 'cuban', 'jamaican',
                'russian', 'irish', 'swedish', 'danish', 'dutch', 'portuguese', 'brazilian', 'peruvian', 'argentinian',
                'moroccan', 'ethiopian', 'lebanese', 'turkish', 'israeli', 'persian', 'pakistani', 'filipino', 'malaysian',
                'indonesian', 'australian', 'new zealand', 'polish', 'hungarian', 'austrian', 'swiss', 'belgian', 'scandinavian'
            ]
            
            # Only add tags that are actual cuisines
            for tag in recipe['tags']:
                if not tag or not isinstance(tag, str):
                    continue
                tag_lower = tag.lower()
                if tag_lower in cuisine_tags:
                    recipe_cuisines.add(tag_lower)
        
        # Remove 'international' as it's not a real cuisine
        recipe_cuisines.discard('international')
        recipe_cuisines.discard('international cuisine')
        
        # If no specific cuisines found after filtering, don't match any cuisine filter
        if not recipe_cuisines:
            logger.debug(f"No specific cuisine found for {recipe.get('title', 'Unknown')} - only had: {recipe.get('cuisine') or recipe.get('cuisines') or recipe.get('tags', [])}")
            return False
            
        # Debug log
        logger.debug(f"Matching cuisines for {recipe.get('title', 'Unknown')}:")
        logger.debug(f"- Looking for: {cuisines}")
        logger.debug(f"- Recipe has: {recipe_cuisines}")
            
        # Only allow exact matches for cuisines
        for cuisine in cuisines:
            if cuisine in recipe_cuisines:
                logger.debug(f"✓ Exact match found: {cuisine}")
                return True
        
        logger.debug(f"✗ No cuisine matches found for {recipe.get('title', 'Unknown')}")
        return False
        
    def _contains_foods_to_avoid(self, recipe: Dict[str, Any], foods_to_avoid: List[str]) -> bool:
        """
        Check if a recipe contains any of the foods to avoid.
        
        Args:
            recipe: The recipe to check
            foods_to_avoid: List of food items to avoid (case-insensitive)
            
        Returns:
            bool: True if any food to avoid is found in the recipe, False otherwise
        """
        if not foods_to_avoid:
            return False
            
        # Get all ingredients from the recipe
        ingredients = []
        if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
            for ing in recipe['ingredients']:
                if isinstance(ing, dict) and 'name' in ing:
                    ingredients.append(ing['name'].lower())
                elif isinstance(ing, str):
                    ingredients.append(ing.lower())
        
        # Also check ingredientLines if available
        if 'ingredientLines' in recipe and isinstance(recipe['ingredientLines'], list):
            ingredients.extend(ing.lower() for ing in recipe['ingredientLines'] if isinstance(ing, str))
        
        # Clean and normalize ingredients
        cleaned_ingredients = []
        for ing in ingredients:
            # Remove measurements and special characters
            ing = re.sub(r'^\d+\s*(\d+/\d+)?\s*(tsp|tbsp|cup|pound|oz|g|kg|ml|l|liter|liters|teaspoon|tablespoon|cups|pounds|ounces|grams|kilograms|milliliters)?\s*', '', ing)
            ing = re.sub(r'[^\w\s]', ' ', ing).strip()
            if ing:
                cleaned_ingredients.append(ing)
        
        # Debug log
        recipe_name = recipe.get('title', 'Unknown Recipe')
        logger.debug(f"\n=== Checking recipe: {recipe_name} ===")
        logger.debug(f"Foods to avoid: {foods_to_avoid}")
        logger.debug(f"Recipe ingredients: {cleaned_ingredients}")
        
        # Check if any food to avoid is in the ingredients
        for food in foods_to_avoid:
            if not food:
                continue
                
            food_lower = food.lower().strip()
            logger.debug(f"Checking for food: {food_lower}")
            
            # Check for exact matches first
            for ing in cleaned_ingredients:
                if food_lower == ing:
                    logger.debug(f"❌ Exact match found: '{food_lower}' in recipe")
                    return True
            
            # Then check for partial matches (whole word only)
            for ing in cleaned_ingredients:
                # Split into words and check each word
                words = ing.split()
                if any(food_lower == word for word in words):
                    logger.debug(f"❌ Found whole word match: '{food_lower}' in '{ing}'")
                    return True
                
                # Check for partial matches within words (but not too short words)
                if len(food_lower) > 3 and food_lower in ing:
                    logger.debug(f"❌ Found partial match: '{food_lower}' in '{ing}'")
                    return True
        
        logger.debug(f"✅ No foods to avoid found in recipe: {recipe_name}")
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
                       dietary_restrictions: List[str] = None,
                       foods_to_avoid: List[str] = None,
                       favorite_foods: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search recipes from local cache with filtering.
        
        Args:
            query: Search query string to match against title, description, or ingredients
            ingredient: Filter by ingredient name
            offset: Pagination offset
            limit: Maximum number of results to return (default: 1000)
            cuisines: List of cuisines to filter by
            dietary_restrictions: List of dietary restrictions to filter by
            foods_to_avoid: List of foods to exclude from results
            favorite_foods: List of favorite foods to prioritize
            
        Returns:
            List of filtered recipe dictionaries from local cache
        """
        # Normalize inputs
        cuisines = [c.lower().strip() for c in cuisines] if cuisines else []
        dietary_restrictions = [dr.lower().strip() for dr in dietary_restrictions] if dietary_restrictions else []
        foods_to_avoid = [fa.lower().strip() for fa in foods_to_avoid] if foods_to_avoid else []
        favorite_foods = [ff.lower().strip() for ff in favorite_foods] if favorite_foods else []
        
        logger.info(f"Searching recipes with query: {query}, ingredient: {ingredient}, "
                   f"cuisines: {cuisines}, dietary_restrictions: {dietary_restrictions}, "
                   f"foods_to_avoid: {foods_to_avoid}, favorite_foods: {favorite_foods}, "
                   f"offset: {offset}, limit: {limit}")
        
        # Get all recipes from cache
        all_recipes = self.recipe_cache.get_cached_recipes()
        if not all_recipes:
            logger.warning("No recipes found in cache")
            return []
            
        logger.info(f"Found {len(all_recipes)} recipes in cache")
        
        # If favorite_foods is provided, filter recipes that contain any of the favorite foods
        if favorite_foods and len(favorite_foods) > 0 and favorite_foods[0]:
            filtered_recipes = []
            for recipe in all_recipes:
                # Check if any favorite food is in the recipe title or description
                recipe_lower = {k: str(v).lower() for k, v in recipe.items() if isinstance(v, str)}
                
                # Check title and description
                title_match = any(food in recipe_lower.get('title', '') for food in favorite_foods)
                desc_match = any(food in recipe_lower.get('description', '') for food in favorite_foods)
                
                # Check ingredients
                ingredient_match = False
                if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
                    for ing in recipe['ingredients']:
                        if isinstance(ing, dict) and 'name' in ing:
                            ing_name = str(ing['name']).lower()
                            if any(food in ing_name for food in favorite_foods):
                                ingredient_match = True
                                break
                        elif isinstance(ing, str):
                            ing_lower = ing.lower()
                            if any(food in ing_lower for food in favorite_foods):
                                ingredient_match = True
                                break
                
                if title_match or desc_match or ingredient_match:
                    filtered_recipes.append(recipe)
            
            all_recipes = filtered_recipes
            logger.info(f"Filtered to {len(all_recipes)} recipes matching favorite foods")
        
        # Filter recipes based on query, ingredient, cuisine, and dietary restrictions
        filtered_recipes = []
        total_recipes = len(all_recipes)
        
        logger.info(f"\n=== Starting recipe filtering ===")
        logger.info(f"Total recipes to process: {total_recipes}")
        
        for idx, recipe in enumerate(all_recipes, 1):
            if not isinstance(recipe, dict) or 'id' not in recipe:
                logger.warning(f"Skipping invalid recipe at index {idx}")
                continue
                
            recipe_name = recipe.get('title', 'Unknown Recipe')
            recipe_id = recipe.get('id', 'unknown')
            
            logger.debug(f"\n[{idx}/{total_recipes}] Processing: {recipe_name} (ID: {recipe_id})")
            
            # Skip if recipe contains any foods to avoid
            if foods_to_avoid:
                contains_bad_food = self._contains_foods_to_avoid(recipe, foods_to_avoid)
                if contains_bad_food:
                    logger.info(f"❌ Excluding recipe due to containing foods to avoid: {recipe_name}")
                    continue
            
            # Check other criteria
            matches_query = self._matches_query(recipe, query)
            has_ingredient = self._contains_ingredient(recipe, ingredient)
            matches_cuisine = self._matches_cuisine(recipe, cuisines)
            matches_diet = self._matches_dietary_restrictions(recipe, dietary_restrictions)
            
            # Include recipe only if it matches all criteria
            if all([matches_query, has_ingredient, matches_cuisine, matches_diet]):
                logger.debug(f"✅ Including recipe: {recipe_name}")
                filtered_recipes.append(recipe)
            else:
                logger.debug(f"❌ Excluding recipe - Criteria not met: {recipe_name}")
                logger.debug(f"  - Matches query: {matches_query}")
                logger.debug(f"  - Has ingredient: {has_ingredient}")
                logger.debug(f"  - Matches cuisine: {matches_cuisine}")
                logger.debug(f"  - Matches diet: {matches_diet}")
        
        logger.info(f"\n=== Filtering complete ===")
        logger.info(f"Total recipes processed: {total_recipes}")
        logger.info(f"Recipes after filtering: {len(filtered_recipes)}")
        
        # Apply offset and limit
        start_idx = min(offset, len(filtered_recipes))
        end_idx = min(offset + limit, len(filtered_recipes))
        paginated_recipes = filtered_recipes[start_idx:end_idx]
        
        logger.info(f"Returning {len(paginated_recipes)} of {len(filtered_recipes)} matching recipes")
        return paginated_recipes
