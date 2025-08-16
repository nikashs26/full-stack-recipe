#!/usr/bin/env python3
"""
Test script to debug Indian cuisine filtering specifically
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_indian_cuisine():
    """Test Indian cuisine filtering specifically"""
    
    print("=== Testing Indian Cuisine Filtering ===\n")
    
    try:
        from services.recipe_cache_service import RecipeCacheService
        
        cache_service = RecipeCacheService()
        
        print("1. Testing Indian cuisine filter...")
        try:
            # Test with Indian cuisine filter
            recipes_with_indian_filter = cache_service.get_cached_recipes(
                query="", 
                ingredient="", 
                filters={"cuisine": "indian"}
            )
            
            print(f"   ✅ Got {len(recipes_with_indian_filter)} recipes with Indian cuisine filter")
            
            if recipes_with_indian_filter:
                print(f"   Sample filtered recipe: {recipes_with_indian_filter[0].get('title', 'Unknown')}")
                print(f"   Recipe cuisine: {recipes_with_indian_filter[0].get('cuisine', 'Unknown')}")
                print(f"   Recipe cuisines: {recipes_with_indian_filter[0].get('cuisines', [])}")
            else:
                print("   ❌ No Indian recipes found")
            
        except Exception as e:
            print(f"   ❌ Error with Indian cuisine filter: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n2. Testing all recipes to see cuisine distribution...")
        try:
            # Get all recipes to see what cuisines exist
            all_recipes = cache_service.get_cached_recipes("", "", None)
            
            # Count cuisines
            cuisine_counts = {}
            indian_recipes = []
            
            for recipe in all_recipes:
                recipe_cuisines = []
                
                # Check both cuisine and cuisines fields
                if recipe.get('cuisine'):
                    recipe_cuisines.append(recipe['cuisine'].lower())
                if recipe.get('cuisines') and isinstance(recipe['cuisines'], list):
                    recipe_cuisines.extend([c.lower() for c in recipe['cuisines'] if c])
                
                # Count each cuisine
                for cuisine in recipe_cuisines:
                    cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
                
                # Check for Indian recipes specifically
                if 'indian' in recipe_cuisines:
                    indian_recipes.append(recipe)
            
            print(f"   Total recipes: {len(all_recipes)}")
            print(f"   Indian recipes found: {len(indian_recipes)}")
            print(f"   Cuisine distribution:")
            
            # Sort by count
            sorted_cuisines = sorted(cuisine_counts.items(), key=lambda x: x[1], reverse=True)
            for cuisine, count in sorted_cuisines[:10]:  # Show top 10
                print(f"     - {cuisine}: {count} recipes")
            
            if indian_recipes:
                print(f"\n   Sample Indian recipes:")
                for i, recipe in enumerate(indian_recipes[:5]):
                    print(f"     {i+1}. {recipe.get('title', 'Unknown')}")
                    print(f"        Cuisine: {recipe.get('cuisine', 'Unknown')}")
                    print(f"        Cuisines: {recipe.get('cuisines', [])}")
            
        except Exception as e:
            print(f"   ❌ Error analyzing all recipes: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n3. Testing different Indian cuisine variations...")
        try:
            # Test different ways to specify Indian cuisine
            variations = ["indian", "india", "indian cuisine", "indian food"]
            
            for variation in variations:
                recipes = cache_service.get_cached_recipes("", "", {"cuisine": variation})
                print(f"   '{variation}': {len(recipes)} recipes")
                
        except Exception as e:
            print(f"   ❌ Error testing variations: {e}")
        
        print(f"\n✅ Indian cuisine test completed")
        
    except Exception as e:
        print(f"❌ Error in Indian cuisine test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_indian_cuisine()
    
    print(f"\n=== Summary ===")
    print(f"1. 🔍 This will show if Indian cuisine filtering is working")
    print(f"2. 🔍 Check how many Indian recipes exist in the database")

