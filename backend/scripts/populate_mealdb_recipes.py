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

# Cuisine mapping
CUISINE_MAPPING = {
    'American': ['American', 'Southern', 'Cajun', 'Creole', 'Soul Food'],
    'Italian': ['Italian', 'Mediterranean'],
    'Chinese': ['Chinese', 'Cantonese', 'Sichuan'],
    'Japanese': ['Japanese', 'Sushi'],
    'Mexican': ['Mexican', 'Tex-Mex'],
    'Indian': ['Indian', 'Pakistani', 'Bangladeshi'],
    'Thai': ['Thai'],
    'French': ['French'],
    'Mediterranean': ['Mediterranean', 'Greek', 'Turkish', 'Lebanese', 'Moroccan'],
    'Other': []
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

def enhance_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance recipe with additional metadata"""
    if not recipe or not isinstance(recipe, dict):
        logger.warning("Invalid recipe format in enhance_recipe")
        return {}
        
    try:
        # Add cuisine based on category/area
        area = str(recipe.get('strArea', '')).strip()
        category = str(recipe.get('strCategory', '')).strip()
        
        # Determine cuisine
        cuisine = 'Other'
        for main_cuisine, aliases in CUISINE_MAPPING.items():
            if (area and any(alias.lower() in area.lower() for alias in aliases)) or \
               (category and any(alias.lower() in category.lower() for alias in aliases)):
                cuisine = main_cuisine
                break
        
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
