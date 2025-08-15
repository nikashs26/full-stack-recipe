#!/usr/bin/env python3
"""
Test to verify chicken recipes come from both Italian and Mexican cuisines
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.recipe_search_service import RecipeSearchService

def test_chicken_diversity():
    """Test that chicken recipes come from both Italian and Mexican cuisines"""
    
    service = RecipeSearchService()
    
    # Test user with chicken preference and Italian/Mexican cuisines
    user_prefs = {
        "favoriteFoods": ["chicken"],
        "favoriteCuisines": ["Italian", "Mexican"],
        "dietaryRestrictions": []
    }
    
    try:
        recommendations = service.get_recipe_recommendations(user_prefs, limit=8)
        print(f"Found {len(recommendations)} recommendations")
        
        # Check cuisine distribution
        cuisine_counts = {}
        chicken_recipes = []
        
        for recipe in recommendations:
            cuisine = recipe.get('cuisine', 'Unknown')
            cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
            
            # Check if it's a chicken recipe
            title = recipe.get('title', recipe.get('name', '')).lower()
            ingredients = recipe.get('ingredients', [])
            ingredients_text = ' '.join(str(i).lower() for i in ingredients)
            
            is_chicken = 'chicken' in title or 'chicken' in ingredients_text
            if is_chicken:
                chicken_recipes.append(recipe)
                print(f"  Chicken recipe: {recipe.get('title', 'Unknown')} (Cuisine: {cuisine})")
        
        print(f"\nTotal chicken recipes found: {len(chicken_recipes)}")
        print(f"Overall cuisine distribution: {cuisine_counts}")
        
        # Check if we have chicken recipes from both Italian and Mexican cuisines
        italian_chicken = [r for r in chicken_recipes if r.get('cuisine', '').lower() in ['italian', 'italy']]
        mexican_chicken = [r for r in chicken_recipes if r.get('cuisine', '').lower() in ['mexican', 'mexico']]
        
        print(f"\nItalian chicken recipes: {len(italian_chicken)}")
        print(f"Mexican chicken recipes: {len(mexican_chicken)}")
        
        if len(italian_chicken) > 0 and len(mexican_chicken) > 0:
            print("✅ SUCCESS: Found chicken recipes from both Italian and Mexican cuisines")
        else:
            print("❌ FAILURE: Missing chicken recipes from one or both cuisines")
            if len(italian_chicken) == 0:
                print("  - No Italian chicken recipes found")
            if len(mexican_chicken) == 0:
                print("  - No Mexican chicken recipes found")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_chicken_diversity()
