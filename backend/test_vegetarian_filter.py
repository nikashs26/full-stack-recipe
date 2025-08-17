#!/usr/bin/env python3
"""
Test script to verify vegetarian filter is working correctly
"""

import json
import os
import sys

# Add the current directory to the path so we can import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.recipe_search_service import RecipeSearchService

def test_vegetarian_filter():
    """Test that vegetarian filter returns all vegetarian recipes"""
    
    print("🧪 Testing vegetarian filter...")
    
    # Initialize the search service
    try:
        search_service = RecipeSearchService()
        print("✅ RecipeSearchService initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize RecipeSearchService: {e}")
        return
    
    # Test 1: Check how many recipes are marked as vegetarian in the database
    print("\n📊 Checking vegetarian recipe count in database...")
    
    try:
        # Get all recipes without filters
        all_recipes = search_service.semantic_search("", limit=2000)
        print(f"📈 Total recipes in database: {len(all_recipes)}")
        
        # Count vegetarian recipes using the new logic
        vegetarian_count = 0
        vegetarian_recipes = []
        
        for recipe in all_recipes:
            # Check if recipe is vegetarian using the same logic as the indexing
            is_vegetarian = (
                "vegetarian" in recipe.get("dietaryRestrictions", []) or
                recipe.get("vegetarian", False) or
                recipe.get("diets") == "vegetarian" or
                (isinstance(recipe.get("diets"), list) and "vegetarian" in recipe.get("diets", []))
            )
            
            if is_vegetarian:
                vegetarian_count += 1
                vegetarian_recipes.append({
                    'title': recipe.get('title') or recipe.get('name'),
                    'diets': recipe.get('diets'),
                    'vegetarian': recipe.get('vegetarian'),
                    'dietaryRestrictions': recipe.get('dietaryRestrictions')
                })
        
        print(f"🥗 Total vegetarian recipes found: {vegetarian_count}")
        
        # Show some examples
        if vegetarian_recipes:
            print("\n📝 Sample vegetarian recipes:")
            for i, recipe in enumerate(vegetarian_recipes[:5]):
                print(f"  {i+1}. {recipe['title']}")
                print(f"     - diets: {recipe['diets']}")
                print(f"     - vegetarian flag: {recipe['vegetarian']}")
                print(f"     - dietaryRestrictions: {recipe['dietaryRestrictions']}")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return
    
    # Test 2: Test the vegetarian filter
    print("\n🔍 Testing vegetarian filter...")
    
    try:
        # Apply vegetarian filter
        filters = {"is_vegetarian": True}
        vegetarian_filtered = search_service.semantic_search("", filters=filters, limit=2000)
        
        print(f"🔍 Recipes returned with vegetarian filter: {len(vegetarian_filtered)}")
        
        if len(vegetarian_filtered) != vegetarian_count:
            print(f"⚠️  WARNING: Filter returned {len(vegetarian_filtered)} recipes but database has {vegetarian_count} vegetarian recipes")
            print("   This suggests the filter is not working correctly")
        else:
            print("✅ Vegetarian filter is working correctly!")
        
        # Show some filtered results
        if vegetarian_filtered:
            print("\n📝 Sample filtered vegetarian recipes:")
            for i, recipe in enumerate(vegetarian_filtered[:5]):
                print(f"  {i+1}. {recipe.get('title') or recipe.get('name')}")
        
    except Exception as e:
        print(f"❌ Error testing vegetarian filter: {e}")
        return
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    test_vegetarian_filter()
