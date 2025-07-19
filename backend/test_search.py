from services.recipe_cache_service import RecipeCacheService
import json

def test_recipe_search():
    # Initialize cache service
    cache = RecipeCacheService()
    
    # Test cases
    test_cases = [
        ("", "", {"cuisine": "Italian"}),
        ("pasta", "", {"cuisine": "Italian"}),
        ("", "", {"cuisine": "Indian"}),
        ("curry", "", {"cuisine": "Indian"}),
        ("chicken", "", None),  # Search across all cuisines
    ]
    
    for query, ingredient, filters in test_cases:
        print(f"\n{'='*60}")
        print(f"Search: query='{query}', ingredient='{ingredient}', filters={filters}")
        print(f"{'='*60}")
        
        try:
            recipes = cache.get_cached_recipes(query, ingredient, filters)
            print(f"\nFound {len(recipes)} recipes")
            
            if recipes:
                print("\nTop 3 results:")
                for i, recipe in enumerate(recipes[:3]):
                    print(f"\n{i+1}. {recipe.get('title', 'No Title')}")
                    print(f"   Source: {recipe.get('source', 'Unknown')}")
                    print(f"   Cuisines: {recipe.get('cuisines', [])}")
                    print(f"   Ingredients: {len(recipe.get('ingredients', []))} items")
                    if recipe.get('ingredients'):
                        print(f"   Sample ingredients: {', '.join(ing.get('name', '') for ing in recipe['ingredients'][:3])}")
        except Exception as e:
            print(f"Error during search: {e}")

if __name__ == "__main__":
    test_recipe_search() 