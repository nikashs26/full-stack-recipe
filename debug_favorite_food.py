#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_search_service import RecipeSearchService
import json

def test_favorite_food_search():
    """Test favorite food search functionality"""
    print("🔍 Testing Favorite Food Search...")
    
    # Initialize the search service
    search_service = RecipeSearchService()
    
    # Test user preferences with burger as favorite food
    test_preferences = {
        "favoriteFoods": ["burger"],
        "favoriteCuisines": [],
        "foodsToAvoid": [],
        "dietaryRestrictions": []
    }
    
    print(f"📋 Test preferences: {test_preferences}")
    
    # Get recommendations
    recommendations = search_service.get_recipe_recommendations(test_preferences, limit=10)
    
    print(f"\n📊 Found {len(recommendations)} recommendations")
    
    if recommendations:
        print("\n🍔 Top recommendations:")
        for i, recipe in enumerate(recommendations[:5], 1):
            name = recipe.get('name', recipe.get('title', 'No name'))
            cuisine = recipe.get('cuisine', 'No cuisine')
            ingredients = recipe.get('ingredients', [])
            
            print(f"{i}. {name}")
            print(f"   Cuisine: {cuisine}")
            print(f"   Ingredients: {ingredients[:3] if ingredients else 'No ingredients'}")
            
            # Check if it actually contains burger
            searchable_text = ' '.join([
                str(recipe.get('name', '')),
                str(recipe.get('title', '')),
                str(recipe.get('description', '')),
                ' '.join([str(ing) for ing in ingredients])
            ]).lower()
            
            has_burger = 'burger' in searchable_text
            print(f"   Contains 'burger': {has_burger}")
            print()
    else:
        print("❌ No recommendations found!")
        
        # Let's try a direct search
        print("\n🔍 Trying direct search for 'burger'...")
        direct_results = search_service.semantic_search("burger", limit=10)
        print(f"Direct search found {len(direct_results)} results")
        
        if direct_results:
            print("\n🍔 Direct search results:")
            for i, recipe in enumerate(direct_results[:3], 1):
                name = recipe.get('name', recipe.get('title', 'No name'))
                print(f"{i}. {name}")
        else:
            print("❌ Direct search also failed!")

if __name__ == "__main__":
    test_favorite_food_search() 