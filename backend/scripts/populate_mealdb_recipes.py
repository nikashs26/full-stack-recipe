import os
import aiohttp
import asyncio
import sys
from typing import List, Dict, Any, Optional
import logging
import ssl
import certifi
import random
from datetime import datetime

# Add the parent directory to the path to import from services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.recipe_cache_service import RecipeCacheService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('populate_recipes.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize the recipe cache service
recipe_cache = RecipeCacheService(cache_ttl_days=30)  # 30 day TTL for cached recipes

# Create a custom SSL context that uses certifi's CA bundle
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Dietary restrictions mapping
DIETARY_RESTRICTIONS = {
    'vegetarian': ['cheese', 'milk', 'butter', 'cream', 'egg', 'yogurt'],
    'vegan': ['cheese', 'milk', 'butter', 'cream', 'egg', 'yogurt', 'honey', 'gelatin'],
    'gluten-free': ['wheat', 'barley', 'rye', 'bread', 'pasta', 'flour'],
    'dairy-free': ['milk', 'cheese', 'butter', 'cream', 'yogurt'],
}

# Cuisine mapping with more comprehensive coverage
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

async def fetch_all_meals():
    """Fetch all meals from TheMealDB"""
    all_meals = []
    base_url = "https://www.themealdb.com/api/json/v1/1"
    
    # Create a connector with our SSL context
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            # First, get all categories
            logger.info("Fetching meal categories...")
            async with session.get(f"{base_url}/list.php?c=list") as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch categories: {response.status}")
                    return []
                categories_data = await response.json()
                categories = [cat['strCategory'] for cat in categories_data.get('meals', [])]
                logger.info(f"Found {len(categories)} categories")
            
            # Then fetch meals from each category
            for category in categories:
                try:
                    logger.debug(f"Fetching meals for category: {category}")
                    async with session.get(f"{base_url}/filter.php?c={category}") as response:
                        if response.status != 200:
                            logger.warning(f"Failed to fetch meals for {category}: {response.status}")
                            continue
                            
                        data = await response.json()
                        if data.get('meals'):
                            all_meals.extend(data['meals'])
                            logger.info(f"Fetched {len(data['meals'])} meals from category: {category}")
                except Exception as e:
                    logger.error(f"Error fetching category {category}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in fetch_all_meals: {str(e)}")
    
    logger.info(f"Total meals fetched: {len(all_meals)}")
    return all_meals

def parse_instructions(instructions: str) -> Dict[str, Any]:
    """Parse recipe instructions into structured format with steps and description."""
    if not instructions:
        return {'description': '', 'steps': []}
    
    # Clean up the instructions - preserve original structure but normalize whitespace
    instructions = instructions.replace('\r\n', '\n').replace('\r', '\n')
    
    # First, try to split by actual numbered steps (e.g., "1.", "1)", "Step 1:")
    import re
    
    # Look for actual step numbers at the beginning of lines or after periods
    # This pattern is more conservative and won't split on measurements
    step_pattern = r'(?:\n\s*\d+[.)]|\A\s*\d+[.)])'
    
    # Split by the step pattern
    raw_steps = re.split(f'({step_pattern})', instructions, flags=re.MULTILINE)
    
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
        steps = [s.strip() for s in instructions.split('\n\n') if s.strip()]
        
        # If that doesn't work, try splitting by single newlines that look like step separators
        if len(steps) <= 1:
            # Look for newlines that are followed by capital letters (likely new steps)
            steps = [s.strip() for s in re.split(r'\n(?=\s*[A-Z])', instructions) if s.strip()]
    
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
    if len(cleaned_steps) <= 1 and instructions:
        # Look for common cooking instruction patterns that indicate new steps
        cooking_keywords = [
            'preheat', 'heat', 'add', 'stir', 'mix', 'combine', 'pour', 'bake', 'cook', 'fry',
            'grill', 'roast', 'boil', 'simmer', 'season', 'salt', 'pepper', 'drain', 'remove',
            'serve', 'garnish', 'decorate', 'cool', 'chill', 'refrigerate', 'freeze', 'place',
            'transfer', 'return', 'bring', 'lower', 'cover', 'uncover', 'flip', 'turn'
        ]
        
        # Split by sentences that contain cooking keywords
        sentences = re.split(r'[.!?]+', instructions)
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
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z][a-z])', instructions)
        cleaned_steps = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
    
    # Ensure we have at least one step
    if not cleaned_steps:
        cleaned_steps = [instructions.strip()]
    
    # Number the steps properly
    numbered_steps = [f"{i+1}. {step}" for i, step in enumerate(cleaned_steps)]
    
    # If we have multiple steps, use the first one as description if it's short enough
    description = ''
    if numbered_steps:
        if len(numbered_steps) > 1 and len(numbered_steps[0].split()) < 30:  # First step is short
            description = numbered_steps[0]
            numbered_steps = numbered_steps[1:]
        elif len(numbered_steps[0].split()) > 50:  # First step is too long, split it
            words = numbered_steps[0].split()
            split_point = len(words) // 2
            description = ' '.join(words[:split_point]).strip()
            numbered_steps[0] = ' '.join(words[split_point:]).strip()
    
    return {
        'description': description,
        'steps': numbered_steps
    }

def enhance_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance recipe with additional metadata"""
    if not recipe or not isinstance(recipe, dict):
        logger.warning("Invalid recipe format in enhance_recipe")
        return {}
        
    try:
        # Add cuisine based on category/area
        area = str(recipe.get('strArea', '')).strip()
        category = str(recipe.get('strCategory', '')).strip()
        
        # Determine cuisine - first try to match area, then category
        cuisine = None
        
        # First try to match area exactly
        if area:
            area_lower = area.lower()
            for main_cuisine, aliases in CUISINE_MAPPING.items():
                if any(alias.lower() == area_lower for alias in [main_cuisine] + aliases):
                    cuisine = main_cuisine
                    break
        
        # If no match from area, try category
        if not cuisine and category:
            category_lower = category.lower()
            for main_cuisine, aliases in CUISINE_MAPPING.items():
                if any(alias.lower() == category_lower for alias in [main_cuisine] + aliases):
                    cuisine = main_cuisine
                    break
        
        # If still no match, try partial matching
        if not cuisine and area:
            area_lower = area.lower()
            for main_cuisine, aliases in CUISINE_MAPPING.items():
                if any(alias.lower() in area_lower for alias in [main_cuisine] + aliases):
                    cuisine = main_cuisine
                    break
        
        # If still no match, try to infer from ingredients
        if not cuisine:
            ingredients = ' '.join(
                str(recipe.get(f'strIngredient{i}', '')).lower() 
                for i in range(1, 21)
                if recipe.get(f'strIngredient{i}')
            )
            
            # Common ingredient-based cuisine detection
            if 'soy sauce' in ingredients or 'hoisin' in ingredients or 'oyster sauce' in ingredients:
                cuisine = 'Chinese'
            elif 'curry' in ingredients or 'garam masala' in ingredients or 'tandoori' in ingredients:
                cuisine = 'Indian'
            elif 'sriracha' in ingredients or 'fish sauce' in ingredients or 'lemongrass' in ingredients:
                if 'coconut milk' in ingredients or 'kaffir lime' in ingredients:
                    cuisine = 'Thai'
                else:
                    cuisine = 'Vietnamese'
            elif 'tortilla' in ingredients or 'salsa' in ingredients or 'guacamole' in ingredients:
                cuisine = 'Mexican'
            elif 'pasta' in ingredients or 'risotto' in ingredients or 'parmesan' in ingredients:
                cuisine = 'Italian'
            elif 'kimchi' in ingredients or 'gochujang' in ingredients or 'gochugaru' in ingredients:
                cuisine = 'Korean'
            elif 'tahini' in ingredients or 'zaatar' in ingredients or 'sumac' in ingredients:
                cuisine = 'Middle Eastern'
        
        # If we still don't have a cuisine, use the area or category as is
        if not cuisine:
            cuisine = area or category or 'International'
        
        # Add dietary restrictions
        ingredients = ' '.join(
            str(recipe.get(f'strIngredient{i}', '')).lower() 
            for i in range(1, 21)  # TheMealDB has up to 20 ingredients
            if recipe.get(f'strIngredient{i}')
        )
        
        dietary_restrictions = []
        for diet, diet_ingredients in DIETARY_RESTRICTIONS.items():
            if any(ing in ingredients for ing in diet_ingredients):
                dietary_restrictions.append(diet)
        
        # Add cooking time if not present (TheMealDB doesn't provide this)
        if 'readyInMinutes' not in recipe:
            # Generate a reasonable cooking time based on category
            base_times = {
                'Dessert': 45,
                'Starter': 25,
                'Side': 30,
                'Breakfast': 20,
                'Vegan': 40,
                'Vegetarian': 35,
                'Pasta': 25,
                'Seafood': 30,
                'Beef': 60,
                'Chicken': 45,
                'Lamb': 90,
                'Pork': 75,
                'Goat': 120,
                'Miscellaneous': 45
            }
            
            # Add some randomness to the cooking time
            base_time = base_times.get(category, 45)
            recipe['readyInMinutes'] = max(15, min(180, base_time + random.randint(-15, 30)))
        
        # Process instructions
        instructions = recipe.get('strInstructions', '')
        parsed_instructions = parse_instructions(instructions)
        
        # Add structured instructions to recipe
        recipe['description'] = parsed_instructions['description']
        recipe['steps'] = parsed_instructions['steps']
        
        # If no description was extracted, use the first 2 steps as description
        if not recipe['description'] and recipe['steps']:
            recipe['description'] = ' '.join(recipe['steps'][:2])
            recipe['steps'] = recipe['steps'][2:] if len(recipe['steps']) > 2 else []
        
        # Ensure we have at least one step
        if not recipe['steps'] and instructions:
            recipe['steps'] = [f"1. {instructions}"]
        
        # Add metadata
        recipe['cuisine'] = cuisine
        recipe['dietary_restrictions'] = dietary_restrictions
        recipe['source'] = 'themealdb'
        recipe['date_modified'] = datetime.now().isoformat()
        
        return recipe
        
    except Exception as e:
        logger.error(f"Error enhancing recipe: {str(e)}")
        return recipe if isinstance(recipe, dict) else {}

async def fetch_recipe_details(meal_id: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed recipe information from TheMealDB"""
    if not meal_id:
        logger.warning("No meal ID provided to fetch_recipe_details")
        return None
        
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    max_retries = 3
    retry_delay = 2  # seconds
    
    connector = aiohttp.TCPConnector(ssl=ssl_context, limit=10)  # Limit concurrent connections
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('meals') and len(data['meals']) > 0:
                            return data['meals'][0]
                        else:
                            logger.warning(f"No meal found with ID {meal_id}")
                            return None
                    elif response.status == 429:  # Too Many Requests
                        wait_time = int(response.headers.get('Retry-After', retry_delay * (attempt + 1)))
                        logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Failed to fetch recipe {meal_id}: HTTP {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching recipe {meal_id} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
            continue
            
        except Exception as e:
            logger.error(f"Error fetching recipe details for meal {meal_id}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
            continue
    
    logger.error(f"Failed to fetch recipe {meal_id} after {max_retries} attempts")
    return None

async def main():
    """Main function to populate the database with recipes from TheMealDB"""
    start_time = datetime.now()
    logger.info("Starting to populate TheMealDB recipes...")
    
    try:
        # Fetch all meals
        all_meals = await fetch_all_meals()
        
        if not all_meals:
            logger.error("No meals found. Exiting.")
            return
            
        # Limit to 100 recipes for testing
        all_meals = all_meals[:100]
        logger.info(f"Processing {len(all_meals)} meals...")
        
        successful = 0
        failed = 0
        
        # Process meals one at a time with delays
        for i, meal in enumerate(all_meals, 1):
            logger.info(f"Processing meal {i}/{len(all_meals)}")
            
            try:
                result = await process_meal(meal, i, len(all_meals))
                if result:
                    successful += 1
                    logger.info(f"Successfully processed meal {i}/{len(all_meals)}")
                else:
                    failed += 1
                    logger.warning(f"Failed to process meal {i}/{len(all_meals)}")
                
                # Add a delay between requests
                delay = random.uniform(2.0, 5.0)  # 2-5 second delay between requests
                logger.debug(f"Waiting {delay:.2f} seconds before next request...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                failed += 1
                logger.error(f"Error processing meal {i}/{len(all_meals)}: {str(e)}", exc_info=True)
                # Continue with the next meal even if one fails
                
        # Log summary
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 50)
        logger.info(f"Recipe population complete!")
        logger.info(f"Total recipes processed: {len(all_meals)}")
        logger.info(f"Successfully cached: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Time taken: {elapsed:.2f} seconds")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise

async def process_meal(meal, current, total):
    """Process a single meal and add it to the cache"""
    try:
        if not meal or not isinstance(meal, dict):
            logger.error("Invalid meal data")
            return False
            
        meal_id = str(meal.get('idMeal', '')).strip()
        if not meal_id:
            logger.error("Meal is missing ID")
            return False
            
        meal_name = str(meal.get('strMeal', 'Unnamed Recipe')).strip()
        
        logger.info(f"Processing {current}/{total}: {meal_name} (ID: {meal_id})")
        
        # Fetch meal details
        meal_details = await fetch_recipe_details(meal_id)
        
        if not meal_details or not isinstance(meal_details, dict):
            logger.warning(f"No valid details found for meal ID: {meal_id}")
            return False
            
        try:
            # Enhance the recipe with additional metadata
            enhanced_recipe = enhance_recipe(meal_details)
            if not enhanced_recipe:
                logger.warning(f"Failed to enhance recipe: {meal_id}")
                return False
                
            # Add the meal to the cache
            success = await recipe_cache.add_recipe(enhanced_recipe)
            if success:
                logger.info(f"Successfully cached: {meal_name}")
                return True
            else:
                logger.warning(f"Failed to cache recipe: {meal_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing meal {meal_id}: {str(e)}", exc_info=True)
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error in process_meal: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
