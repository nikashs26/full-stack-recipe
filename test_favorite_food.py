#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_search_service import RecipeSearchService
import json

def test_favorite_food_recommendations():
    """Test the favorite food recommendation functionality"""
    
    # Initialize the search service
    search_service = RecipeSearchService()
    
    # Test preferences with favorite foods
    test_preferences = {
        "favoriteFoods": ["chicken", "pasta"],
        "favoriteCuisines": [],
        "dietaryRestrictions": [],
        "foodsToAvoid": []
    }
    
    print("Testing favorite food recommendations...")
    print(f"Test preferences: {json.dumps(test_preferences, indent=2)}")
    
    try:
        # Get recommendations
        recommendations = search_service.get_recipe_recommendations(test_preferences, limit=5)
        
        print(f"\nFound {len(recommendations)} recommendations")
        
        if recommendations:
            print("\nTop recommendations:")
            for i, recipe in enumerate(recommendations[:5], 1):
                title = recipe.get('title', recipe.get('name', 'No title'))
                cuisine = recipe.get('cuisine', 'Unknown')
                ingredients = recipe.get('ingredients', [])
                
                print(f"{i}. {title}")
                print(f"   Cuisine: {cuisine}")
                print(f"   Ingredients: {[ing.get('name', str(ing)) for ing in ingredients[:3]]}")
                print()
        else:
            print("No recommendations found!")
            
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_favorite_food_recommendations() 