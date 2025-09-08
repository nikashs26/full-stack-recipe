#!/usr/bin/env python3
"""
Minimal Railway Population Script
Creates a basic set of recipes to get the app working
"""

import json
import os
import sys
from typing import Dict, List, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_sample_recipes() -> List[Dict[str, Any]]:
    """Create a basic set of sample recipes"""
    return [
        {
            "id": "1",
            "title": "Classic Spaghetti Carbonara",
            "description": "A traditional Italian pasta dish with eggs, cheese, and pancetta",
            "ingredients": ["spaghetti", "eggs", "parmesan cheese", "pancetta", "black pepper", "salt"],
            "instructions": "Cook spaghetti, mix with beaten eggs and cheese, add pancetta",
            "prep_time": 15,
            "cook_time": 20,
            "servings": 4,
            "cuisine": "Italian",
            "dietary_tags": ["vegetarian"],
            "difficulty": "medium",
            "image_url": "https://example.com/carbonara.jpg",
            "nutrition": {
                "calories": 450,
                "protein": 18,
                "carbs": 35,
                "fat": 25
            }
        },
        {
            "id": "2", 
            "title": "Chicken Stir Fry",
            "description": "Quick and healthy chicken stir fry with vegetables",
            "ingredients": ["chicken breast", "bell peppers", "broccoli", "soy sauce", "garlic", "ginger", "rice"],
            "instructions": "Cut chicken, stir fry with vegetables, add sauce, serve over rice",
            "prep_time": 10,
            "cook_time": 15,
            "servings": 3,
            "cuisine": "Asian",
            "dietary_tags": ["gluten-free"],
            "difficulty": "easy",
            "image_url": "https://example.com/stirfry.jpg",
            "nutrition": {
                "calories": 320,
                "protein": 28,
                "carbs": 25,
                "fat": 12
            }
        },
        {
            "id": "3",
            "title": "Chocolate Chip Cookies",
            "description": "Soft and chewy homemade chocolate chip cookies",
            "ingredients": ["flour", "butter", "brown sugar", "eggs", "chocolate chips", "vanilla", "baking soda"],
            "instructions": "Mix ingredients, form cookies, bake at 375°F for 10-12 minutes",
            "prep_time": 20,
            "cook_time": 12,
            "servings": 24,
            "cuisine": "American",
            "dietary_tags": ["vegetarian"],
            "difficulty": "easy",
            "image_url": "https://example.com/cookies.jpg",
            "nutrition": {
                "calories": 150,
                "protein": 2,
                "carbs": 20,
                "fat": 7
            }
        },
        {
            "id": "4",
            "title": "Greek Salad",
            "description": "Fresh Mediterranean salad with tomatoes, cucumbers, and feta",
            "ingredients": ["tomatoes", "cucumbers", "red onion", "feta cheese", "olives", "olive oil", "oregano"],
            "instructions": "Chop vegetables, mix with feta and olives, drizzle with olive oil",
            "prep_time": 15,
            "cook_time": 0,
            "servings": 4,
            "cuisine": "Greek",
            "dietary_tags": ["vegetarian", "gluten-free"],
            "difficulty": "easy",
            "image_url": "https://example.com/greek-salad.jpg",
            "nutrition": {
                "calories": 180,
                "protein": 8,
                "carbs": 12,
                "fat": 14
            }
        },
        {
            "id": "5",
            "title": "Beef Tacos",
            "description": "Spicy ground beef tacos with fresh toppings",
            "ingredients": ["ground beef", "taco shells", "lettuce", "tomatoes", "cheese", "sour cream", "taco seasoning"],
            "instructions": "Cook beef with seasoning, fill shells with beef and toppings",
            "prep_time": 15,
            "cook_time": 20,
            "servings": 6,
            "cuisine": "Mexican",
            "dietary_tags": ["gluten-free"],
            "difficulty": "easy",
            "image_url": "https://example.com/tacos.jpg",
            "nutrition": {
                "calories": 280,
                "protein": 18,
                "carbs": 20,
                "fat": 15
            }
        }
    ]

def populate_railway_minimal():
    """Populate Railway with minimal sample recipes"""
    try:
        from services.recipe_cache_service import RecipeCacheService
        
        print("🚀 Starting minimal Railway population...")
        
        # Initialize cache service
        cache = RecipeCacheService()
        print("✓ Cache service initialized")
        
        # Create sample recipes
        recipes = create_sample_recipes()
        print(f"📊 Created {len(recipes)} sample recipes")
        
        # Add recipes to cache
        total_added = 0
        for recipe in recipes:
            try:
                # add_recipe is async, so we need to await it
                import asyncio
                result = asyncio.run(cache.add_recipe(recipe))
                if result:
                    total_added += 1
                    print(f"✓ Added recipe: {recipe['title']}")
                else:
                    print(f"⚠️ Failed to add recipe {recipe['title']}: add_recipe returned False")
            except Exception as e:
                print(f"⚠️ Failed to add recipe {recipe['title']}: {e}")
                continue
        
        print(f"🎉 Successfully populated Railway with {total_added} sample recipes!")
        print("💡 Note: This is a minimal set. For full functionality, you'll need to populate with your complete recipe database.")
        return True
        
    except Exception as e:
        print(f"❌ Error during population: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = populate_railway_minimal()
    sys.exit(0 if success else 1)
