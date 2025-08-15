#!/usr/bin/env python3
"""
Test what the backend is actually receiving when processing recipes
"""

from backend.services.recipe_service import RecipeService
from backend.services.recipe_cache_service import RecipeCacheService

def test_backend_cuisine_processing():
    """Test what the backend receives when processing recipes"""
    
    print("🔍 Testing backend cuisine processing...")
    print("=" * 50)
    
    try:
        # Initialize services
        recipe_cache = RecipeCacheService()
        recipe_service = RecipeService(recipe_cache)
        
        # Get a few recipes from cache
        print("📥 Getting recipes from cache...")
        recipes = recipe_cache._get_all_recipes_from_cache()
        print(f"Found {len(recipes)} recipes in cache")
        
        # Check first few recipes
        for i, recipe in enumerate(recipes[:3]):
            print(f"\n🍳 Recipe {i+1}: {recipe.get('title', 'No title')}")
            print(f"  ID: {recipe.get('id', 'No ID')}")
            print(f"  Cuisine field: {recipe.get('cuisine', 'No cuisine')}")
            print(f"  Cuisines field: {recipe.get('cuisines', 'No cuisines')}")
            print(f"  All keys: {list(recipe.keys())}")
            
            # Test cuisine matching
            print(f"  Testing cuisine matching...")
            matches_italian = recipe_service._matches_cuisine(recipe, ['italian'])
            matches_mexican = recipe_service._matches_cuisine(recipe, ['mexican'])
            matches_both = recipe_service._matches_cuisine(recipe, ['italian', 'mexican'])
            
            print(f"    Matches Italian: {matches_italian}")
            print(f"    Matches Mexican: {matches_mexican}")
            print(f"    Matches Both: {matches_both}")
            
            print("---")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backend_cuisine_processing()
