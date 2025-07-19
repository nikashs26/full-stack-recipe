import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from services.recipe_service import RecipeService
from services.recipe_cache_service import RecipeCacheService
import logging
import ssl
import certifi
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# List of cuisines to fetch - MUST match frontend options
CUISINES = [
    "Italian", "Mexican", "Indian", "Chinese", "Japanese",
    "Thai", "Mediterranean", "French", "Greek", "Spanish",
    "Korean", "Vietnamese", "American", "British", "Irish",
    "Caribbean", "Moroccan"
]

async def fetch_mealdb_by_cuisine(session, cuisine: str) -> list:
    """Fetch recipes from TheMealDB for a specific cuisine"""
    url = "https://www.themealdb.com/api/json/v1/1/filter.php"
    params = {"a": cuisine}
    
    try:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                meals = data.get('meals', [])
                logger.info(f"Found {len(meals)} {cuisine} recipes from TheMealDB")
                
                # Take only up to 25 recipes (since we'll get 25 from Spoonacular too)
                meals = meals[:25]
                
                # Fetch full details for each recipe
                detailed_meals = []
                for meal in meals:
                    try:
                        async with session.get(
                            "https://www.themealdb.com/api/json/v1/1/lookup.php",
                            params={"i": meal['idMeal']}
                        ) as detail_response:
                            if detail_response.status == 200:
                                detail_data = await detail_response.json()
                                if detail_data.get('meals'):
                                    detailed_meals.extend(detail_data['meals'])
                                    logger.info(f"Fetched details for {meal['strMeal']}")
                    except Exception as e:
                        logger.error(f"Error fetching recipe details from TheMealDB: {e}")
                
                return detailed_meals
            else:
                logger.error(f"TheMealDB API error for {cuisine}: {response.status}")
                return []
    except Exception as e:
        logger.error(f"Error fetching {cuisine} recipes from TheMealDB: {e}")
        return []

async def fetch_spoonacular_by_cuisine(session, cuisine: str, api_key: str) -> list:
    """Fetch recipes from Spoonacular for a specific cuisine"""
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": api_key,
        "cuisine": cuisine,
        "number": 25,  # Get 25 from each API to total 50
        "addRecipeInformation": "true",
        "fillIngredients": "true",
        "instructionsRequired": "true"
    }
    
    try:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                recipes = data.get('results', [])
                logger.info(f"Found {len(recipes)} {cuisine} recipes from Spoonacular")
                return recipes
            else:
                logger.error(f"Spoonacular API error for {cuisine}: {response.status}")
                return []
    except Exception as e:
        logger.error(f"Error fetching {cuisine} recipes from Spoonacular: {e}")
        return []

async def populate_recipe_cache():
    """Populate ChromaDB with recipes from both APIs"""
    # Load environment variables
    load_dotenv()
    
    # Initialize services
    recipe_cache = RecipeCacheService()
    recipe_service = RecipeService(recipe_cache)
    
    # Create SSL context
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    # Track statistics
    stats = {
        "total_recipes": 0,
        "recipes_by_cuisine": {},
        "start_time": datetime.now()
    }
    
    # Create aiohttp session with SSL context
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        for cuisine in CUISINES:
            logger.info(f"\nFetching recipes for {cuisine} cuisine...")
            stats["recipes_by_cuisine"][cuisine] = {"mealdb": 0, "spoonacular": 0}
            
            # Fetch from TheMealDB
            mealdb_recipes = await fetch_mealdb_by_cuisine(session, cuisine)
            if mealdb_recipes:
                normalized_mealdb = []
                for recipe in mealdb_recipes:
                    normalized = recipe_service._normalize_mealdb_recipe(recipe)
                    if normalized:
                        # Add cuisine to recipe data
                        normalized['cuisines'] = [cuisine]
                        normalized_mealdb.append(normalized)
                
                if normalized_mealdb:
                    try:
                        # Cache with cuisine as a search term
                        await asyncio.to_thread(
                            recipe_cache.cache_recipes,
                            normalized_mealdb,
                            cuisine,  # Use cuisine as search term
                            "",      # No ingredient filter
                            {"cuisine": cuisine}  # Add cuisine metadata
                            print("stored recipes in chroma");
                        )
                        stats["total_recipes"] += len(normalized_mealdb)
                        stats["recipes_by_cuisine"][cuisine]["mealdb"] = len(normalized_mealdb)
                        logger.info(f"Cached {len(normalized_mealdb)} {cuisine} recipes from TheMealDB")
                    except Exception as e:
                        logger.error(f"Failed to cache {cuisine} recipes from TheMealDB: {e}")
            
            # Fetch from Spoonacular if API key is available
            if recipe_service.spoonacular_key:
                spoonacular_recipes = await fetch_spoonacular_by_cuisine(
                    session,
                    cuisine,
                    recipe_service.spoonacular_key
                )
                if spoonacular_recipes:
                    normalized_spoonacular = []
                    for recipe in spoonacular_recipes:
                        normalized = recipe_service._normalize_spoonacular_recipe(recipe)
                        if normalized:
                            # Ensure cuisine is in recipe data
                            if cuisine not in normalized.get('cuisines', []):
                                normalized['cuisines'] = [cuisine]
                            normalized_spoonacular.append(normalized)
                    
                    if normalized_spoonacular:
                        try:
                            # Cache with cuisine as a search term
                            await asyncio.to_thread(
                                recipe_cache.cache_recipes,
                                normalized_spoonacular,
                                cuisine,  # Use cuisine as search term
                                "",      # No ingredient filter
                                {"cuisine": cuisine}  # Add cuisine metadata
                            )
                            stats["total_recipes"] += len(normalized_spoonacular)
                            stats["recipes_by_cuisine"][cuisine]["spoonacular"] = len(normalized_spoonacular)
                            logger.info(f"Cached {len(normalized_spoonacular)} {cuisine} recipes from Spoonacular")
                        except Exception as e:
                            logger.error(f"Failed to cache {cuisine} recipes from Spoonacular: {e}")
            
            # Add a small delay between cuisines to avoid rate limits
            await asyncio.sleep(1)
    
    # Calculate execution time
    execution_time = datetime.now() - stats["start_time"]
    stats["execution_time"] = str(execution_time)
    stats["start_time"] = stats["start_time"].isoformat()  # Convert to string

    # Print final statistics
    logger.info("\nPopulation Summary:")
    logger.info(f"Total Recipes Cached: {stats['total_recipes']}")
    logger.info(f"Execution Time: {execution_time}")
    logger.info("\nRecipes by Cuisine:")
    for cuisine, counts in stats["recipes_by_cuisine"].items():
        total = counts["mealdb"] + counts["spoonacular"]
        logger.info(f"{cuisine}: {total} total ({counts['mealdb']} MealDB, {counts['spoonacular']} Spoonacular)")

    # Save statistics to file
    with open('recipe_population_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)

    # Print cache statistics
    cache_stats = recipe_cache.get_cache_stats()
    logger.info("\nCache Statistics:")
    logger.info(f"Total Recipes: {cache_stats['total_recipes']}")
    logger.info(f"Valid Recipes: {cache_stats['valid_recipes']}")
    logger.info(f"Cache TTL: {cache_stats['cache_ttl_days']} days")

    # Print missing cuisines
    missing_cuisines = [
        cuisine for cuisine, counts in stats["recipes_by_cuisine"].items()
        if counts["mealdb"] + counts["spoonacular"] == 0
    ]
    if missing_cuisines:
        logger.warning("\nMissing cuisines (no recipes found):")
        for cuisine in missing_cuisines:
            logger.warning(f"- {cuisine}")
        logger.warning("\nConsider adding sample recipes for these cuisines manually.")

if __name__ == "__main__":
    asyncio.run(populate_recipe_cache()) 