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

    def _matches_name(self, recipe: Dict[str, Any], name_query: str) -> bool:
        """Check if a recipe's name matches the search query."""
        if not name_query:
            return True
            
        query = name_query.lower()
        
        # Only check title for name search
        if 'title' in recipe and query in recipe['title'].lower():
            return True
            
        return False
        
    def _matches_ingredient(self, recipe: Dict[str, Any], ingredient_query: str) -> bool:
        """Check if a recipe contains the specified ingredient."""
        if not ingredient_query:
            return True
            
        query = ingredient_query.lower()
        
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
        cuisines = [c.lower().strip() for c in cuisines]
        recipe_cuisines = set()
        
        # Check 'cuisine' field
        if 'cuisine' in recipe and recipe['cuisine']:
            if isinstance(recipe['cuisine'], str):
                recipe_cuisines.add(recipe['cuisine'].lower().strip())
            elif isinstance(recipe['cuisine'], list):
                recipe_cuisines.update(c.lower().strip() for c in recipe['cuisine'] if c and isinstance(c, str))
        
        # Check 'cuisines' field
        if 'cuisines' in recipe and recipe['cuisines']:
            if isinstance(recipe['cuisines'], str):
                recipe_cuisines.add(recipe['cuisines'].lower().strip())
            elif isinstance(recipe['cuisines'], list):
                recipe_cuisines.update(c.lower().strip() for c in recipe['cuisines'] if c and isinstance(c, str))
        
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
                tag_lower = tag.lower().strip()
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
        
        # Check for any match between requested cuisines and recipe's cuisines
        matches = any(cuisine in recipe_cuisines for cuisine in cuisines)
        
        if matches:
            logger.debug(f"✓ Match found for {recipe.get('title', 'Unknown')}")
        else:
            logger.debug(f"✗ No cuisine matches found for {recipe.get('title', 'Unknown')}")
            
        return matches
        
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
        
        # Get all ingredients for checking
        ingredients = []
        if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
            ingredients = [
                ing['name'].lower() if isinstance(ing, dict) and 'name' in ing 
                else ing.lower() if isinstance(ing, str) 
                else str(ing).lower() 
                for ing in recipe['ingredients']
            ]
        
        ingredients_text = ' '.join(ingredients)
        
        # For vegetarian/vegan, check ingredients
        if 'vegetarian' in restrictions or 'vegan' in restrictions:
            non_veg_ingredients = ['meat', 'chicken', 'beef', 'pork', 'fish', 'shrimp', 'bacon', 'sausage', 
                                 'steak', 'ham', 'turkey', 'duck', 'goose', 'venison', 'lamb']
            
            if any(ing in ingredients_text for ing in non_veg_ingredients):
                recipe_restrictions.discard('vegetarian')
                recipe_restrictions.discard('vegan')
        
        # For vegan, also check for dairy/eggs
        if 'vegan' in restrictions:
            non_vegan_ingredients = ['egg', 'cheese', 'milk', 'butter', 'yogurt', 'honey', 'gelatin', 'cream']
            if any(ing in ingredients_text for ing in non_vegan_ingredients):
                recipe_restrictions.discard('vegan')
        
        # For gluten-free, check for gluten-containing ingredients
        if 'gluten-free' in restrictions:
            gluten_ingredients = ['wheat', 'barley', 'rye', 'malt', 'brewer\'s yeast', 'seitan', 'farina', 'spelt', 'triticale']
            if any(ing in ingredients_text for ing in gluten_ingredients):
                recipe_restrictions.discard('gluten-free')
            
            # Also check for common gluten-containing additives
            gluten_additives = ['modified food starch', 'maltodextrin', 'dextrin', 'malt extract', 'malt syrup', 'soy sauce']
            if any(additive in ingredients_text for additive in gluten_additives):
                recipe_restrictions.discard('gluten-free')
        
        # For dairy-free, check for dairy ingredients
        if 'dairy-free' in restrictions:
            dairy_ingredients = ['milk', 'cheese', 'butter', 'yogurt', 'cream', 'whey', 'casein', 'lactose', 'ghee', 'curd']
            if any(ing in ingredients_text for ing in dairy_ingredients):
                recipe_restrictions.discard('dairy-free')
        
        # Check if all required restrictions are met
        required_restrictions = set(r.lower().strip() for r in restrictions if r)
        return required_restrictions.issubset(recipe_restrictions)

    def _recipe_contains_ingredient(self, recipe: Dict[str, Any], ingredient: str) -> bool:
        """Check if a recipe contains the specified ingredient (case-insensitive)."""
        if not ingredient or not recipe.get('ingredients'):
            return False
            
        ingredient = ingredient.lower().strip()
        
        for ing in recipe['ingredients']:
            if isinstance(ing, dict) and 'name' in ing:
                if ingredient in ing['name'].lower():
                    return True
            elif isinstance(ing, str) and ingredient in ing.lower():
                return True
                
        return False
        
    def _recipe_matches_any_ingredients(self, recipe: Dict[str, Any], ingredients: List[str]) -> bool:
        """Check if a recipe contains any of the specified ingredients."""
        if not ingredients or not recipe.get('ingredients'):
            return False
            
        recipe_ingredients = ' '.join(
            ing['name'].lower() if isinstance(ing, dict) and 'name' in ing 
            else ing.lower() if isinstance(ing, str) 
            else str(ing).lower() 
            for ing in recipe['ingredients']
        )
        
        return any(ing.lower().strip() in recipe_ingredients for ing in ingredients if ing.strip())
    
    async def search_recipes(self, query: str = "", ingredient: str = "", 
                           offset: int = 0, limit: int = None,
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
            limit: This parameter is no longer used and will be removed in a future version
            cuisines: List of cuisines to filter by
            dietary_restrictions: List of dietary restrictions to filter by
            foods_to_avoid: List of foods to exclude from results
            favorite_foods: List of user's favorite foods to prioritize in results
            
        Returns:
            List of filtered recipe dictionaries from local cache, with favorite food matches first
        """
        # Normalize inputs
        cuisines = [c.lower().strip() for c in cuisines] if cuisines else []
        dietary_restrictions = [dr.lower().strip() for dr in dietary_restrictions] if dietary_restrictions else []
        foods_to_avoid = [fa.lower().strip() for fa in foods_to_avoid] if foods_to_avoid else []
        favorite_foods = [ff.lower().strip() for ff in favorite_foods] if favorite_foods else []
        
        logger.info(f"Searching recipes with query='{query}', ingredient='{ingredient}'")
        logger.info(f"Search filters - Cuisines: {cuisines}, Diets: {dietary_restrictions}")
        logger.info(f"Foods to avoid: {foods_to_avoid}")
        logger.info(f"Favorite foods to prioritize: {favorite_foods}")
        
        # Get all recipes from cache
        all_recipes = self.recipe_cache.get_cached_recipes()
        
        if not all_recipes:
            logger.warning("No recipes found in local cache")
            return []
            
        # Show actual number of recipes without duplicating
        logger.info(f"Found {len(all_recipes)} total recipes in cache")
        
        # If you want to limit to a maximum number of recipes, uncomment this:
        # if len(all_recipes) > 1000:
        #     all_recipes = all_recipes[:1000]
        #     logger.info(f"Limited to first 1000 of {len(all_recipes)} recipes")
        
        # Initialize recipe categories
        perfect_matches = []  # Matches both cuisine AND favorite foods
        favorite_food_matches = []  # Matches favorite foods but not cuisine
        cuisine_matches = []  # Matches cuisine but not favorite foods
        other_matches = []  # Matches other criteria but neither favorite foods nor cuisine
        
        total_recipes = len(all_recipes)
        
        logger.info(f"\n=== Starting recipe filtering ===")
        logger.info(f"Total recipes to process: {total_recipes}")
        
        for idx, recipe in enumerate(all_recipes, 1):
            if not isinstance(recipe, dict) or 'id' not in recipe:
                logger.warning(f"Skipping invalid recipe at index {idx}")
                continue
                
            recipe_name = recipe.get('title', 'Unknown Recipe')
            recipe_id = recipe.get('id', 'unknown')
            
            # Skip if recipe contains any foods to avoid
            if foods_to_avoid and self._contains_foods_to_avoid(recipe, foods_to_avoid):
                logger.info(f"❌ Excluding recipe due to containing foods to avoid: {recipe_name}")
                continue
            
            # Check all criteria including cuisine
            matches_name = self._matches_name(recipe, query) if query else True
            has_ingredient = self._contains_ingredient(recipe, ingredient) if ingredient else True
            matches_diet = self._matches_dietary_restrictions(recipe, dietary_restrictions) if dietary_restrictions else True
            matches_cuisine = self._matches_cuisine(recipe, cuisines) if cuisines else True
            
            # Debug log for each filter
            logger.debug(f"\nRecipe: {recipe.get('title', 'Unknown')}")
            logger.debug(f"- Matches name: {matches_name}")
            logger.debug(f"- Has ingredient: {has_ingredient}")
            logger.debug(f"- Matches diet: {matches_diet}")
            logger.debug(f"- Matches cuisine: {matches_cuisine}")
            
            # Skip if any filter doesn't match
            if not all([matches_name, has_ingredient, matches_diet, matches_cuisine]):
                logger.debug("❌ Excluding recipe - Criteria not met")
                continue
            
            # Check for favorite food matches
            contains_favorite_food = self._recipe_matches_any_ingredients(recipe, favorite_foods) if favorite_foods else False
            
            # Categorize the recipe - favorite foods take priority over cuisine
            if contains_favorite_food:
                if matches_cuisine:
                    perfect_matches.append(recipe)
                favorite_food_matches.append(recipe)
            elif matches_cuisine:
                cuisine_matches.append(recipe)
            else:
                other_matches.append(recipe)
        
        logger.info(f"\n=== Filtering complete ===")
        logger.info(f"Total recipes processed: {total_recipes}")
        logger.info(f"Perfect matches (cuisine + favorite food): {len(perfect_matches)}")
        logger.info(f"Favorite food matches: {len(favorite_food_matches)}")
        logger.info(f"Cuisine matches: {len(cuisine_matches)}")
        logger.info(f"Other matches: {len(other_matches)}")
        
        # Combine results with priority:
        # 1. Perfect matches (both cuisine and favorite food)
        # 2. Favorite food matches
        # 3. Cuisine matches
        # 4. Other matches
        combined_results = perfect_matches + favorite_food_matches + cuisine_matches + other_matches
        
        # If we have favorite foods but no matches, include some random recipes
        if favorite_foods and not (perfect_matches or favorite_food_matches) and len(combined_results) < 10:
            logger.info("No favorite food matches found, including some random recipes")
            import random
            random.shuffle(cuisine_matches + other_matches)
            combined_results = (perfect_matches + favorite_food_matches + 
                              (cuisine_matches + other_matches)[:10])
        
        logger.info(f"Returning {len(combined_results)} matching recipes")
        return combined_results
