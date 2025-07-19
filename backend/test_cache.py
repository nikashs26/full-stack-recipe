from services.recipe_cache_service import RecipeCacheService
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cache():
    # Initialize cache service
    cache = RecipeCacheService()
    
    # Test searching by cuisine
    for cuisine in ["Italian", "Mexican", "Indian", "Chinese", "Japanese"]:
        print(f"\n{'='*50}")
        print(f"Testing {cuisine} cuisine:")
        print(f"{'='*50}")
        
        # Method 1: Search by cuisine filter
        print("\nMethod 1: Using cuisine filter")
        recipes = cache.get_cached_recipes("", "", {"cuisine": cuisine})
        print(f"Found {len(recipes)} recipes using filter")
        
        # Method 2: Search by cuisine query
        print("\nMethod 2: Using cuisine as search term")
        recipes = cache.get_cached_recipes(cuisine, "")
        print(f"Found {len(recipes)} recipes using search")
        
        if recipes:
            # Print first 3 recipes
            for i, recipe in enumerate(recipes[:3]):
                print(f"\n{i+1}. {recipe.get('title', 'No Title')}")
                print(f"   Source: {recipe.get('source', 'Unknown')}")
                print(f"   ID: {recipe.get('id', 'No ID')}")
                print(f"   Cuisines: {recipe.get('cuisines', [])}")
                print(f"   Ingredients: {len(recipe.get('ingredients', []))} items")
                print(f"   Instructions: {recipe.get('instructions', 'No instructions')[:100]}...")
        else:
            print("\nNo recipes found for this cuisine")

    # Get cache statistics
    stats = cache.get_cache_stats()
    print("\nCache Statistics:")
    print(json.dumps(stats, indent=2))

    # Test searching by ingredient within a cuisine
    print("\nTesting ingredient search within cuisines:")
    test_cases = [
        ("Italian", "pasta"),
        ("Mexican", "tortilla"),
        ("Indian", "curry"),
        ("Chinese", "rice"),
        ("Japanese", "sushi")
    ]
    
    for cuisine, ingredient in test_cases:
        print(f"\nSearching for {ingredient} in {cuisine} cuisine:")
        recipes = cache.get_cached_recipes(ingredient, "", {"cuisine": cuisine})
        print(f"Found {len(recipes)} matching recipes")
        if recipes:
            for i, recipe in enumerate(recipes[:2]):
                print(f"\n{i+1}. {recipe.get('title', 'No Title')}")
                print(f"   Ingredients: {', '.join([ing.get('name', '') for ing in recipe.get('ingredients', [])][:3])}...")

if __name__ == "__main__":
    test_cache() 