#!/usr/bin/env python3
"""
Test script to debug the vegetarian filter issue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

def test_vegetarian_filter():
    print("🔍 Testing vegetarian filter...")
    
    # Initialize the cache service
    cache_service = RecipeCacheService()
    
    # Get all recipes
    all_recipes = cache_service._get_all_recipes_from_cache()
    print(f"Total recipes in cache: {len(all_recipes)}")
    
    # Count vegetarian recipes by different methods
    vegetarian_by_dietary_restrictions = 0
    vegetarian_by_diets = 0
    vegetarian_by_boolean = 0
    vegetarian_any_method = 0
    
    vegetarian_recipes = []
    
    for recipe in all_recipes:
        is_vegetarian = False
        
        # Method 1: Check dietaryRestrictions array
        if recipe.get('dietaryRestrictions'):
            for restriction in recipe['dietaryRestrictions']:
                if restriction and 'vegetarian' in str(restriction).lower():
                    vegetarian_by_dietary_restrictions += 1
                    is_vegetarian = True
                    break
        
        # Method 2: Check diets array
        if not is_vegetarian and recipe.get('diets'):
            for diet in recipe['diets']:
                if diet and 'vegetarian' in str(diet).lower():
                    vegetarian_by_diets += 1
                    is_vegetarian = True
                    break
        
        # Method 3: Check vegetarian boolean field
        if not is_vegetarian and recipe.get('vegetarian') is True:
            vegetarian_by_boolean += 1
            is_vegetarian = True
        
        if is_vegetarian:
            vegetarian_any_method += 1
            vegetarian_recipes.append({
                'id': recipe.get('id'),
                'title': recipe.get('title'),
                'dietaryRestrictions': recipe.get('dietaryRestrictions'),
                'diets': recipe.get('diets'),
                'vegetarian': recipe.get('vegetarian')
            })
    
    print(f"\n📊 Vegetarian recipe counts:")
    print(f"  - By dietaryRestrictions field: {vegetarian_by_dietary_restrictions}")
    print(f"  - By diets field: {vegetarian_by_diets}")
    print(f"  - By vegetarian boolean: {vegetarian_by_boolean}")
    print(f"  - Total (any method): {vegetarian_any_method}")
    print(f"  - Percentage: {(vegetarian_any_method/len(all_recipes)*100):.1f}%")
    
    # Test the filtering logic
    print(f"\n🔍 Testing filter logic...")
    
    # Test with dietary_restrictions filter
    filters = {"dietary_restrictions": ["vegetarian"]}
    filtered_recipes = cache_service.get_cached_recipes("", "", filters)
    
    print(f"Filtered recipes with vegetarian filter: {len(filtered_recipes)}")
    
    # Show some sample vegetarian recipes
    print(f"\n🍽️ Sample vegetarian recipes:")
    for i, recipe in enumerate(vegetarian_recipes[:5]):
        print(f"{i+1}. {recipe['title']} (ID: {recipe['id']})")
        print(f"   Dietary Restrictions: {recipe['dietaryRestrictions']}")
        print(f"   Diets: {recipe['diets']}")
        print(f"   Vegetarian field: {recipe['vegetarian']}")
        print()
    
    # Test the specific filtering logic
    print(f"\n🔍 Testing specific filtering logic...")
    
    # Simulate the filtering logic from the cache service
    test_recipes = all_recipes[:100]  # Test with first 100 recipes
    filtered_count = 0
    
    for recipe in test_recipes:
        should_include = True
        
        # Apply dietary restrictions filter
        dietary_filter = ["vegetarian"]
        recipe_dietary = []
        
        # Check dietaryRestrictions and diets arrays
        if recipe.get('dietaryRestrictions'):
            recipe_dietary.extend([d.lower() for d in recipe['dietaryRestrictions'] if d])
        if recipe.get('diets'):
            recipe_dietary.extend([d.lower() for d in recipe['diets'] if d])
        
        # Check vegetarian and vegan boolean fields
        if recipe.get('vegetarian') is True:
            recipe_dietary.append('vegetarian')
        if recipe.get('vegan') is True:
            recipe_dietary.append('vegan')
        
        # Check if any recipe dietary info matches the filter
        if not any(diet in recipe_dietary for diet in dietary_filter):
            should_include = False
        
        if should_include:
            filtered_count += 1
    
    print(f"Test filtering results:")
    print(f"  - Tested recipes: {len(test_recipes)}")
    print(f"  - Passed filter: {filtered_count}")
    print(f"  - Filtered out: {len(test_recipes) - filtered_count}")

if __name__ == "__main__":
    test_vegetarian_filter()
