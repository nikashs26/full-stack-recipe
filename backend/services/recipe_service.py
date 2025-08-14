import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

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

    def _normalize_spoonacular_recipe(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize recipe data from Spoonacular API to our standard format.
        
        Args:
            recipe_data: Raw recipe data from Spoonacular API
            
        Returns:
            Normalized recipe dictionary in our standard format
        """
        try:
            # Extract basic recipe information
            recipe = {
                'id': str(recipe_data.get('id', '')),
                'title': recipe_data.get('title', '').strip(),
                'summary': recipe_data.get('summary', '').strip(),
                'readyInMinutes': recipe_data.get('readyInMinutes', 0),
                'servings': recipe_data.get('servings', 1),
                'sourceUrl': recipe_data.get('sourceUrl', ''),
                'image': recipe_data.get('image', ''),
                'imageType': 'jpg',
                'sourceName': 'Spoonacular',
                'spoonacularSourceUrl': recipe_data.get('spoonacularSourceUrl', ''),
                'analyzedInstructions': recipe_data.get('analyzedInstructions', []),
                'cuisines': [c.strip() for c in recipe_data.get('cuisines', []) 
                                if c.strip() and c.strip().lower() in [
                                    'american', 'british', 'canadian', 'chinese', 'croatian', 'dutch',
                                    'egyptian', 'french', 'greek', 'indian', 'irish', 'italian',
                                    'jamaican', 'japanese', 'kenyan', 'malaysian', 'mexican',
                                    'moroccan', 'russian', 'spanish', 'thai', 'tunisian',
                                    'turkish', 'vietnamese'
                                ]],
                'diets': [d.strip() for d in recipe_data.get('diets', []) if d.strip()],
                'dietary_restrictions': self._extract_dietary_restrictions(recipe_data),
                'dishTypes': [dt.strip() for dt in recipe_data.get('dishTypes', []) if dt.strip()],
                'occasions': [o.strip() for o in recipe_data.get('occasions', []) if o.strip()],
                'winePairing': recipe_data.get('winePairing', {}),
                'createdAt': datetime.utcnow().isoformat(),
                'updatedAt': datetime.utcnow().isoformat()
            }
            
            # Extract and format instructions
            instructions = []
            for instruction in recipe_data.get('analyzedInstructions', []):
                for step in instruction.get('steps', []):
                    if step.get('step'):
                        instructions.append(step['step'].strip())
            
            if not instructions and 'instructions' in recipe_data and recipe_data['instructions']:
                # Fallback to plain instructions if no analyzed steps
                instructions = [s.strip() for s in recipe_data['instructions'].split('\n') if s.strip()]
            
            recipe['instructions'] = instructions or ['No instructions provided.']
            
            # Extract and format ingredients
            ingredients = []
            for ing in recipe_data.get('extendedIngredients', []):
                try:
                    amount = ing.get('amount', 0)
                    unit = ing.get('unit', '').strip()
                    name = ing.get('name', '').strip()
                    
                    if not name:
                        continue
                        
                    ingredient = {
                        'id': str(ing.get('id', '')),
                        'name': name,
                        'amount': amount,
                        'unit': unit,
                        'original': ing.get('original', '').strip(),
                        'measures': {
                            'us': {
                                'amount': ing.get('measures', {}).get('us', {}).get('amount', amount),
                                'unitShort': ing.get('measures', {}).get('us', {}).get('unitShort', unit),
                                'unitLong': ing.get('measures', {}).get('us', {}).get('unitLong', unit)
                            },
                            'metric': {
                                'amount': ing.get('measures', {}).get('metric', {}).get('amount', amount),
                                'unitShort': ing.get('measures', {}).get('metric', {}).get('unitShort', unit),
                                'unitLong': ing.get('measures', {}).get('metric', {}).get('unitLong', unit)
                            }
                        }
                    }
                    ingredients.append(ingredient)
                except Exception as e:
                    logger.error(f"Error processing ingredient {ing.get('name', 'unknown')}: {e}")
            
            recipe['ingredients'] = ingredients
            
            # Add nutrition information if available
            if 'nutrition' in recipe_data:
                recipe['nutrition'] = recipe_data['nutrition']
            
            return recipe
            
        except Exception as e:
            logger.error(f"Error normalizing Spoonacular recipe: {e}", exc_info=True)
            return None
            
    def _extract_dietary_restrictions(self, recipe_data: Dict[str, Any]) -> List[str]:
        """
        Extract dietary restrictions from recipe data.
        
        Args:
            recipe_data: Raw recipe data from API
            
        Returns:
            List of dietary restriction tags
        """
        restrictions = set()
        
        # Check for vegetarian/vegan
        if recipe_data.get('vegetarian', False):
            restrictions.add('vegetarian')
        if recipe_data.get('vegan', False):
            restrictions.add('vegan')
            
        # Check for common allergens and dietary preferences
        if 'dairyFree' in recipe_data and recipe_data['dairyFree']:
            restrictions.add('dairy-free')
            
        if 'glutenFree' in recipe_data and recipe_data['glutenFree']:
            restrictions.add('gluten-free')
            
        # Check for nuts in ingredients
        ingredients_text = ' '.join([
            ing.get('name', '').lower() + ' ' + ing.get('original', '').lower() 
            for ing in recipe_data.get('extendedIngredients', [])
        ])
        
        nut_keywords = ['nut', 'almond', 'cashew', 'pistachio', 'walnut', 'pecan', 'hazelnut', 'peanut']
        if any(keyword in ingredients_text for keyword in nut_keywords):
            restrictions.add('contains-nuts')
        else:
            restrictions.add('nut-free')
            
        # Check for eggs
        egg_keywords = ['egg', 'eggs', 'mayonnaise', 'mayo']
        if any(keyword in ingredients_text for keyword in egg_keywords):
            restrictions.add('contains-eggs')
        else:
            restrictions.add('egg-free')
            
        # Add any diets from the recipe data
        for diet in recipe_data.get('diets', []):
            if diet and isinstance(diet, str):
                diet = diet.lower().replace(' ', '-')
                restrictions.add(diet)
                
        # Add any intolerances if present
        for intolerance in recipe_data.get('intolerances', []):
            if intolerance and isinstance(intolerance, str):
                restrictions.add(intolerance.lower().replace(' ', '-'))
                
        return sorted(list(restrictions))
        
    def _extract_mealdb_dietary_restrictions(self, recipe_data: Dict[str, Any], ingredients: List[Dict[str, str]]) -> List[str]:
        """
        Extract dietary restrictions from TheMealDB recipe data.
        
        Args:
            recipe_data: Raw recipe data from TheMealDB
            ingredients: List of normalized ingredients
            
        Returns:
            List of dietary restriction tags
        """
        restrictions = set()
        
        # Convert ingredients to text for searching
        ingredients_text = ' '.join([
            f"{ing.get('name', '').lower()} {ing.get('measure', '').lower()}" 
            for ing in ingredients
        ])
        
        # Define food categories
        meat_keywords = ['chicken', 'beef', 'pork', 'lamb', 'bacon', 'sausage', 'meat', 'fish', 'seafood', 'shrimp', 'prawn', 'ham', 'bacon', 'salami', 'pepperoni', 'prosciutto', 'poultry', 'venison', 'duck', 'goose', 'turkey']
        dairy_keywords = ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein', 'ghee', 'yoghurt', 'sour cream', 'heavy cream', 'whipping cream', 'half-and-half', 'buttermilk']
        egg_keywords = ['egg', 'eggs', 'mayonnaise', 'mayo', 'albumen']
        nut_keywords = ['nut', 'almond', 'cashew', 'pistachio', 'walnut', 'pecan', 'hazelnut', 'peanut', 'macadamia', 'brazil nut', 'chestnut', 'pinenut', 'pine nut', 'pistachio']
        
        # Check for meat/fish/poultry (non-vegetarian)
        has_meat = any(meat in ingredients_text for meat in meat_keywords)
        has_dairy = any(dairy in ingredients_text for dairy in dairy_keywords)
        has_eggs = any(egg in ingredients_text for egg in egg_keywords)
        
        # Set vegetarian/vegan status
        if not has_meat:
            restrictions.add('vegetarian')
            recipe_data['vegetarian'] = True  # Set the vegetarian flag
            if not has_dairy and not has_eggs:
                restrictions.add('vegan')
                recipe_data['vegan'] = True  # Set the vegan flag
        
        # Set dairy status
        if not has_dairy:
            restrictions.add('dairy-free')
        else:
            recipe_data['dairy'] = True
            
        # Ensure vegetarian/vegan tags are in the recipe's tags if not already present
        if recipe_data.get('vegetarian', False) and 'vegetarian' not in recipe_data.get('tags', []):
            if 'tags' not in recipe_data:
                recipe_data['tags'] = []
            recipe_data['tags'].append('vegetarian')
            
        if recipe_data.get('vegan', False) and 'vegan' not in recipe_data.get('tags', []):
            if 'tags' not in recipe_data:
                recipe_data['tags'] = []
            recipe_data['tags'].append('vegan')
            
        # Set nut status
        has_nuts = any(nut in ingredients_text for nut in nut_keywords)
        if has_nuts:
            restrictions.add('contains-nuts')
            recipe_data['containsNuts'] = True
        else:
            restrictions.add('nut-free')
            
        # Set egg status
        if has_eggs:
            restrictions.add('contains-eggs')
            recipe_data['containsEggs'] = True
        else:
            restrictions.add('egg-free')
            
        # Check for gluten (common in TheMealDB recipes)
        gluten_keywords = ['wheat', 'flour', 'bread', 'pasta', 'noodle', 'dough', 'crust', 'cake', 'biscuit', 'cracker', 'barley', 'rye', 'triticale', 'malt', 'brewer\'s yeast']
        has_gluten = any(gluten in ingredients_text for gluten in gluten_keywords)
        if not has_gluten:
            restrictions.add('gluten-free')
            
        # Add category as a tag if available
        if recipe_data.get('strCategory'):
            category = str(recipe_data['strCategory'] or '').strip().lower()
            if category:
                restrictions.add(category.replace(' ', '-'))
        
        # Log the restrictions for debugging
        logger.debug(f"Recipe: {recipe_data.get('strMeal', 'Unknown')}")
        logger.debug(f"Ingredients text: {ingredients_text}")
        logger.debug(f"Detected restrictions: {restrictions}")
                
        return sorted(list(restrictions))

    def _normalize_mealdb_recipe(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize recipe data from TheMealDB API to our standard format.
        
        Args:
            recipe_data: Raw recipe data from TheMealDB API
            
        Returns:
            Normalized recipe dictionary or None if recipe is invalid
        """
        if not recipe_data or not isinstance(recipe_data, dict) or 'idMeal' not in recipe_data:
            logger.warning("Invalid recipe data received")
            return None
            
        try:
            # Extract ingredients and measurements
            # Extract ingredients and measurements
            ingredients = []
            for i in range(1, 21):  # TheMealDB has up to 20 ingredients
                # Safely get and clean ingredient and measure
                ingredient = str(recipe_data.get(f'strIngredient{i}', '') or '').strip()
                measure = str(recipe_data.get(f'strMeasure{i}', '') or '').strip()
                
                # Skip empty ingredients or placeholders
                if not ingredient or ingredient.lower() in ('', 'null', 'none'):
                    continue
                    
                ingredients.append({
                    'name': ingredient,
                    'measure': measure if measure and measure.lower() not in ('', 'null', 'none') else 'to taste',
                    'original': f"{measure} {ingredient}".strip()
                })
        
            # Handle instructions - split into steps if they're numbered
            instructions = recipe_data.get('strInstructions', '')
            if instructions:
                # First try to split by common step separators
                import re
                
                # Try different patterns for step separation
                # Pattern 1: Numbers followed by dots or parentheses (e.g., "1.", "1)", "1 -")
                steps_pattern1 = re.split(r'\d+[\.\)\-\s]+', instructions)
                
                # Pattern 2: Split by double newlines or periods followed by newlines
                steps_pattern2 = re.split(r'\.\s*\n|\n\s*\n', instructions)
                
                # Pattern 3: Split by single newlines
                steps_pattern3 = instructions.split('\n')
                
                # Choose the best pattern based on which one gives us the most non-empty steps
                all_patterns = [steps_pattern1, steps_pattern2, steps_pattern3]
                best_pattern = max(all_patterns, key=lambda x: len([s for s in x if s.strip()]))
                
                # Clean up the steps
                steps = []
                for step in best_pattern:
                    step = step.strip()
                    if step and len(step) > 5:  # Only include steps with meaningful content
                        # Remove leading numbers, dots, dashes, etc.
                        step = re.sub(r'^[\d\.\)\-\s]+', '', step).strip()
                        if step:
                            steps.append(step)
                
                # If we still don't have multiple steps, try to split by common cooking instruction keywords
                if len(steps) <= 1 and instructions:
                    # Look for common cooking instruction patterns
                    cooking_keywords = [
                        'preheat', 'heat', 'add', 'stir', 'mix', 'combine', 'pour', 'bake', 'cook', 'fry',
                        'grill', 'roast', 'boil', 'simmer', 'season', 'salt', 'pepper', 'drain', 'remove',
                        'serve', 'garnish', 'decorate', 'cool', 'chill', 'refrigerate', 'freeze'
                    ]
                    
                    # Split by sentences that contain cooking keywords
                    sentences = re.split(r'[.!?]+', instructions)
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if sentence and len(sentence) > 10:  # Only meaningful sentences
                            # Check if sentence contains cooking keywords
                            if any(keyword in sentence.lower() for keyword in cooking_keywords):
                                steps.append(sentence)
                
                # If all else fails, just split by periods and clean up
                if len(steps) <= 1:
                    sentences = re.split(r'[.!?]+', instructions)
                    steps = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
                
                # Ensure we have at least one step
                if not steps:
                    steps = [instructions.strip()]
                    
            else:
                steps = ['No instructions provided.']
            
            # Safely get ID and title
            recipe_id = str(recipe_data.get('idMeal', '')).strip()
            if not recipe_id:
                logger.warning("Recipe missing ID, skipping")
                return None
                
            title = str(recipe_data.get('strMeal', 'Untitled Recipe') or 'Untitled Recipe').strip()
            
            # Extract dietary restrictions
            dietary_restrictions = self._extract_mealdb_dietary_restrictions(recipe_data, ingredients)
            
            # Build the normalized recipe
            normalized = {
                'id': f"mealdb_{recipe_id}",
                'title': title,
                'image': str(recipe_data.get('strMealThumb', '') or ''),
                'source': 'TheMealDB',
                'source_url': str(recipe_data.get('strSource', '') or ''),
                'ingredients': ingredients,
                'instructions': steps,
                'prep_time': None,
                'cook_time': None,
                'dietary_restrictions': dietary_restrictions,
                'diets': dietary_restrictions,  # Also add to diets for filtering
                'cuisines': [],
                'tags': [],
                'nutrition': {},
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'source_id': recipe_id,
                    'source': 'TheMealDB',
                    'original_data': recipe_data
                }
            }
            
            # Map of TheMealDB areas to standard cuisine names
            CUISINE_MAPPING = {
                'american': 'american',
                'british': 'british',
                'canadian': 'canadian',
                'chinese': 'chinese',
                'croatian': 'croatian',
                'dutch': 'dutch',
                'egyptian': 'egyptian',
                'french': 'french',
                'greek': 'greek',
                'indian': 'indian',
                'irish': 'irish',
                'italian': 'italian',  # Italian is not automatically Mediterranean
                'jamaican': 'jamaican',
                'japanese': 'japanese',
                'kenyan': 'kenyan',
                'malaysian': 'malaysian',
                'mexican': 'mexican',
                'moroccan': 'moroccan',
                'russian': 'russian',
                'spanish': 'spanish',
                'thai': 'thai',
                'tunisian': 'tunisian',
                'turkish': 'turkish',
                'vietnamese': 'vietnamese'
            }
            
            # List of specific dishes that are considered Mediterranean
            MEDITERRANEAN_DISHES = {
                'greek': ['moussaka', 'tzatziki', 'dolmades', 'souvlaki', 'spanakopita', 'baklava', 'gyro', 'feta salad'],
                'spanish': ['paella', 'gazpacho', 'patatas bravas', 'tortilla española', 'chorizo', 'pisto', 'albondigas'],
                'italian': ['caprese salad', 'bruschetta', 'minestrone', 'risotto alla milanese', 'insalata caprese'],
                'turkish': ['kebab', 'baklava', 'dolma', 'lahmacun', 'menemen', 'imam bayildi'],
                'lebanese': ['falafel', 'hummus', 'tabbouleh', 'baba ganoush', 'fattoush', 'shawarma'],
                'moroccan': ['tagine', 'couscous', 'harira', 'pastilla', 'zaalouk', 'kefta']
            }
            
            # Add category as a tag if available
            if recipe_data.get('strCategory'):
                category = str(recipe_data['strCategory'] or '').strip().lower()
                if category:
                    normalized['tags'].append(category)
            
            # Handle cuisine/area with validation and mapping
            if recipe_data.get('strArea'):
                area = str(recipe_data['strArea'] or '').strip().lower()
                
                # Only add if it's a known cuisine from our mapping
                if area in CUISINE_MAPPING:
                    normalized_cuisine = CUISINE_MAPPING[area]
                    normalized['cuisines'].append(normalized_cuisine)
                    
                    # Check if this is a Mediterranean dish
                    title_lower = normalized['title'].lower()
                    is_mediterranean = False
                    
                    # Check if this is a specifically Mediterranean dish
                    if area in MEDITERRANEAN_DISHES:
                        for dish in MEDITERRANEAN_DISHES[area]:
                            if dish in title_lower:
                                is_mediterranean = True
                                break
                    
                    # For Italian dishes, be more strict about what's considered Mediterranean
                    if area == 'italian' and not is_mediterranean:
                        # Common Italian dishes that aren't necessarily Mediterranean
                        common_italian = ['pizza', 'pasta', 'ravioli', 'spaghetti', 'fettuccine', 'lasagna', 'risotto',
                                       'carbonara', 'bolognese', 'pesto', 'tiramisu', 'cannoli', 'bruschetta']
                        if any(dish in title_lower for dish in common_italian):
                            is_mediterranean = False
                    
                    if is_mediterranean:
                        normalized['tags'].append('mediterranean')
                        logger.debug(f"Marked '{normalized['title']}' as Mediterranean")
                    
                    logger.debug(f"Added cuisine '{normalized_cuisine}' for area '{area}' in recipe: {normalized['title']}")
                else:
                    logger.debug(f"Skipping unknown cuisine area: {area} for recipe: {normalized['title']}")
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing recipe data: {str(e)}")
            import traceback
            logger.debug(f"Error details: {traceback.format_exc()}")
            return None
            
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
            
        # Special handling for American cuisine to include regional American cuisines
        for cuisine in cuisines:
            cuisine_lower = cuisine.lower()
            if cuisine_lower == 'american':
                # For American cuisine, also match Southern, Creole, and other American regional cuisines
                american_regional_cuisines = {
                    'american', 'southern', 'creole', 'cajun', 'soul food', 'southwestern', 
                    'louisiana', 'tex-mex', 'new orleans', 'deep south', 'gulf coast'
                }
                if recipe_cuisines.intersection(american_regional_cuisines):
                    logger.debug(f"✓ American regional cuisine match found: {recipe_cuisines.intersection(american_regional_cuisines)}")
                    return True
            else:
                # Normal exact match for other cuisines
                if cuisine_lower in recipe_cuisines:
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
        """Check if a recipe matches all the specified dietary restrictions.
        
        This method checks the recipe's dietary restriction tags for matches.
        """
        if not restrictions:
            return True
            
        # Get dietary restrictions from various possible fields
        recipe_restrictions = set()
        
        # Check diets field (common in Spoonacular data)
        if 'diets' in recipe and isinstance(recipe['diets'], list):
            recipe_restrictions.update(d.lower() for d in recipe['diets'] if isinstance(d, str) and d.strip())
            
        # Check dietary_restrictions field (our normalized field)
        if 'dietary_restrictions' in recipe and isinstance(recipe['dietary_restrictions'], list):
            recipe_restrictions.update(d.lower() for d in recipe['dietary_restrictions'] 
                                     if isinstance(d, str) and d.strip())
        
        # Check for vegetarian/vegan flags directly in the recipe
        if recipe.get('vegetarian', False):
            recipe_restrictions.add('vegetarian')
        if recipe.get('vegan', False):
            recipe_restrictions.add('vegan')
        
        # If no restrictions found in the recipe, assume it's not restricted
        if not recipe_restrictions:
            return False
            
        # Debug logging
        logger.debug(f"Recipe '{recipe.get('title', 'unknown')}' has restrictions: {recipe_restrictions}")
        
        # Check if all required restrictions are met
        required_restrictions = {r.lower().strip() for r in restrictions if r and r.strip()}
        
        # If no valid restrictions to check, return True
        if not required_restrictions:
            return True
            
        # Special case: if 'vegetarian' is required but recipe is marked as 'vegan', that's also acceptable
        if 'vegetarian' in required_restrictions and 'vegan' in recipe_restrictions:
            required_restrictions.discard('vegetarian')
            required_restrictions.add('vegan')
        
        # Check if all required restrictions are present in the recipe
        return required_restrictions.issubset(recipe_restrictions)
        
    def _matches_query(self, recipe: Dict[str, Any], query: str) -> bool:
        """
        Check if a recipe's title matches the search query.
        Only matches against the recipe title, not ingredients or other fields.
        
        Args:
            recipe: The recipe to check
            query: The search query string
            
        Returns:
            bool: True if the recipe title contains the query (case-insensitive), 
                  False otherwise. Returns True if query is empty.
        """
        if not query or not query.strip():
            return True
            
        query = query.lower().strip()
        if not query:
            return True
            
        # Only search in the recipe title
        title = str(recipe.get('title', '')).lower()
        return query in title
            
        # Check ingredients
        if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
            for ing in recipe['ingredients']:
                if isinstance(ing, dict) and 'name' in ing:
                    ing_name = str(ing['name']).lower()
                    if any(term in ing_name for term in query_terms):
                        return True
                elif isinstance(ing, str) and any(term in ing.lower() for term in query_terms):
                    return True
                    
        # Check instructions if available
        instructions = recipe.get('instructions', '')
        if isinstance(instructions, list):
            # Create a copy of instructions for search without modifying the original
            search_instructions = ' '.join(str(step) for step in instructions)
        else:
            search_instructions = str(instructions)
        search_instructions = search_instructions.lower()
        if any(term in search_instructions for term in query_terms):
            return True
            
        # Check tags if available
        if 'tags' in recipe and isinstance(recipe['tags'], list):
            for tag in recipe['tags']:
                tag_str = str(tag).lower()
                if any(term in tag_str for term in query_terms):
                    return True
                    
        # Check cuisines if available
        if 'cuisines' in recipe and isinstance(recipe['cuisines'], list):
            for cuisine in recipe['cuisines']:
                cuisine_str = str(cuisine).lower()
                if any(term in cuisine_str for term in query_terms):
                    return True
                    
        return False

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
        all_recipes = self.recipe_cache.get_cached_recipes(query, ingredient)
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
        
        # Apply preference-based scoring and balancing
        if cuisines or favorite_foods:
            # Normalize cuisine preferences to lowercase for consistent comparison
            normalized_cuisines = [c.lower().strip() for c in cuisines] if cuisines else []
            
            # Score recipes based on preferences
            scored_recipes = []
            for recipe in all_recipes:
                score = 0
                
                # Score based on cuisine preferences
                if normalized_cuisines:
                    recipe_cuisines = []
                    if 'cuisines' in recipe and isinstance(recipe['cuisines'], list):
                        recipe_cuisines.extend([c.lower().strip() for c in recipe['cuisines'] if isinstance(c, str)])
                    if 'cuisine' in recipe and isinstance(recipe['cuisine'], list):
                        recipe_cuisines.extend([c.lower().strip() for c in recipe['cuisine'] if isinstance(c, str)])
                    
                    for pref_cuisine in normalized_cuisines:
                        if pref_cuisine in recipe_cuisines:
                            score += 10  # High score for cuisine match
                            break
                
                # Score based on favorite foods
                if favorite_foods:
                    recipe_text = f"{recipe.get('title', '')} {recipe.get('description', '')}".lower()
                    for food in favorite_foods:
                        if food.lower() in recipe_text:
                            score += 5  # Medium score for food match
                            break
                
                scored_recipes.append((recipe, score))
            
            # Sort by score (highest first) - this ensures preference-based ordering
            scored_recipes.sort(key=lambda x: x[1], reverse=True)
            
            # Apply cuisine balancing for display order (NOT quantity limits)
            if normalized_cuisines and len(normalized_cuisines) > 1:
                logger.info(f"Applying cuisine balancing for {len(normalized_cuisines)} cuisines (ordering only, no quantity limits)")
                
                # Group recipes by cuisine for better ordering
                cuisine_groups = {cuisine: [] for cuisine in normalized_cuisines}
                other_recipes = []
                
                for recipe, score in scored_recipes:
                    recipe_cuisines = []
                    if 'cuisines' in recipe and isinstance(recipe['cuisines'], list):
                        recipe_cuisines.extend([c.lower().strip() for c in recipe['cuisines'] if isinstance(c, str)])
                    if 'cuisine' in recipe and isinstance(recipe['cuisine'], list):
                        recipe_cuisines.extend([c.lower().strip() for c in recipe['cuisine'] if isinstance(c, str)])
                    
                    # Find which preference cuisine this recipe matches
                    matched_cuisine = None
                    for pref_cuisine in normalized_cuisines:
                        if pref_cuisine in recipe_cuisines:
                            matched_cuisine = pref_cuisine
                            break
                    
                    if matched_cuisine:
                        cuisine_groups[matched_cuisine].append((recipe, score))
                    else:
                        other_recipes.append((recipe, score))
                
                # Sort each cuisine group by score
                for cuisine in normalized_cuisines:
                    cuisine_groups[cuisine].sort(key=lambda x: x[1], reverse=True)
                
                # Create balanced ordering (round-robin) but keep ALL recipes
                balanced_recipes = []
                max_recipes_per_cuisine = max(len(group) for group in cuisine_groups.values()) if cuisine_groups else 0
                
                # Round-robin selection to ensure even distribution in ordering
                for round_num in range(max_recipes_per_cuisine):
                    for cuisine in normalized_cuisines:
                        if round_num < len(cuisine_groups[cuisine]):
                            recipe, score = cuisine_groups[cuisine][round_num]
                            balanced_recipes.append(recipe)
                
                # Add remaining recipes from each cuisine group
                for cuisine in normalized_cuisines:
                    for recipe, score in cuisine_groups[cuisine]:
                        if recipe not in balanced_recipes:
                            balanced_recipes.append(recipe)
                
                # Add other recipes at the end
                balanced_recipes.extend(other_recipes)
                
                all_recipes = balanced_recipes
                logger.info(f"Applied cuisine balancing: {len(all_recipes)} recipes with preference-based ordering")
            else:
                # No balancing needed, just use scored results
                all_recipes = [recipe for recipe, score in scored_recipes]
        
        # Filter recipes based on query, ingredient, cuisine, and dietary restrictions
        filtered_recipes = []
        total_recipes = len(all_recipes)
        
        logger.info(f"\n=== Starting recipe filtering ===")
        logger.info(f"Total recipes to process: {total_recipes}")
        logger.info(f"Search query: '{query}'")
        logger.info(f"Ingredient filter: '{ingredient}'")
        logger.info(f"Cuisines: {cuisines}")
        logger.info(f"Dietary restrictions: {dietary_restrictions}")
        logger.info(f"Foods to avoid: {foods_to_avoid}")
        
        # Track cuisine matching statistics
        cuisine_match_counts = {cuisine: 0 for cuisine in (cuisines or [])}
        total_cuisine_matches = 0
        
        for idx, recipe in enumerate(all_recipes, 1):
            if not isinstance(recipe, dict) or 'id' not in recipe:
                logger.warning(f"Skipping invalid recipe at index {idx}")
                continue
                
            recipe_name = recipe.get('title', 'Unknown Recipe')
            recipe_id = recipe.get('id', 'unknown')
            
            logger.debug(f"\n[{idx}/{total_recipes}] Processing: {recipe_name} (ID: {recipe_id})")
            
            # Get recipe's dietary restrictions for logging
            recipe_restrictions = set()
            if 'diets' in recipe and isinstance(recipe['diets'], list):
                recipe_restrictions.update(d.lower() for d in recipe['diets'] if isinstance(d, str) and d.strip())
            if 'dietary_restrictions' in recipe and isinstance(recipe['dietary_restrictions'], list):
                recipe_restrictions.update(d.lower() for d in recipe['dietary_restrictions'] 
                                         if isinstance(d, str) and d.strip())
            if recipe.get('vegetarian', False):
                recipe_restrictions.add('vegetarian')
            if recipe.get('vegan', False):
                recipe_restrictions.add('vegan')
                
            # Check if recipe contains the required ingredient
            if ingredient:
                ingredient_found = False
                recipe_ingredients = recipe.get('ingredients', [])
                if isinstance(recipe_ingredients, list):
                    for ing in recipe_ingredients:
                        if isinstance(ing, dict) and 'name' in ing:
                            ing_name = str(ing['name']).lower()
                            if ingredient.lower() in ing_name:
                                ingredient_found = True
                                break
                        elif isinstance(ing, str) and ingredient.lower() in ing.lower():
                            ingredient_found = True
                            break
                
                if not ingredient_found:
                    logger.debug(f"  - Recipe does not contain ingredient: {ingredient}")
                    continue
            
            logger.debug(f"Recipe restrictions: {recipe_restrictions}")
            
            # Apply search query filter if provided
            if query and not self._matches_query(recipe, query):
                logger.debug("Skipping - doesn't match search query")
                continue
                
            # Apply ingredient filter if provided
            if ingredient and not self._contains_ingredient(recipe, ingredient):
                logger.debug("Skipping - doesn't contain required ingredient")
                continue
                
            # Skip if recipe contains any foods to avoid
            if foods_to_avoid:
                contains_bad_food = self._contains_foods_to_avoid(recipe, foods_to_avoid)
                if contains_bad_food:
                    logger.info(f"❌ Excluding recipe due to containing foods to avoid: {recipe_name}")
                    continue
            
            # Check other criteria
            matches_query = self._matches_query(recipe, query) if query else True
            has_ingredient = self._contains_ingredient(recipe, ingredient) if ingredient else True
            matches_cuisine = self._matches_cuisine(recipe, cuisines) if cuisines else True
            matches_diet = self._matches_dietary_restrictions(recipe, dietary_restrictions) if dietary_restrictions else True
            
            # Track cuisine matches for statistics
            if cuisines and matches_cuisine:
                total_cuisine_matches += 1
                # Find which specific cuisine matched
                recipe_cuisines = set()
                if 'cuisines' in recipe and isinstance(recipe['cuisines'], list):
                    recipe_cuisines.update(c.lower() for c in recipe['cuisines'] if c and isinstance(c, str))
                if 'cuisine' in recipe and isinstance(recipe['cuisine'], list):
                    recipe_cuisines.update(c.lower() for c in recipe['cuisine'] if c and isinstance(c, str))
                
                for cuisine in cuisines:
                    if cuisine.lower() in recipe_cuisines:
                        cuisine_match_counts[cuisine] += 1
                        break
            
            # Include recipe only if it matches all criteria
            if all([matches_query, has_ingredient, matches_cuisine, matches_diet]):
                filtered_recipes.append(recipe)
            else:
                logger.debug(f"❌ Excluding recipe - Criteria not met: {recipe_name}")
                if query:
                    logger.debug(f"  - Matches query '{query}': {matches_query}")
                if ingredient:
                    logger.debug(f"  - Has ingredient '{ingredient}': {has_ingredient}")
                if cuisines:
                    logger.debug(f"  - Matches cuisine {cuisines}: {matches_cuisine}")
                if dietary_restrictions:
                    logger.debug(f"  - Matches diet {dietary_restrictions}: {matches_diet}")
        
        logger.info(f"\n=== Filtering complete ===")
        logger.info(f"Total recipes processed: {total_recipes}")
        logger.info(f"Recipes after filtering: {len(filtered_recipes)}")
        
        # Log cuisine matching statistics
        if cuisines:
            logger.info(f"Cuisine filtering statistics:")
            logger.info(f"  Total recipes matching any cuisine: {total_cuisine_matches}")
            for cuisine, count in cuisine_match_counts.items():
                logger.info(f"  {cuisine}: {count} recipes")
        
        # Apply offset and limit
        start_idx = min(offset, len(filtered_recipes))
        end_idx = min(offset + limit, len(filtered_recipes))
        paginated_recipes = filtered_recipes[start_idx:end_idx]
        
        logger.info(f"Returning {len(paginated_recipes)} of {len(filtered_recipes)} matching recipes")
        return {
            "results": paginated_recipes,
            "total": len(filtered_recipes)
        }
