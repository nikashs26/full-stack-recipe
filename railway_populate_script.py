#!/usr/bin/env python3
"""
Railway Direct Population Script
Run this on Railway to populate the database with recipes
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

def get_sample_recipes():
    """Get a comprehensive set of sample recipes"""
    return [
        {
            "id": "recipe_1",
            "title": "Classic Spaghetti Carbonara",
            "name": "Classic Spaghetti Carbonara",
            "cuisine": "Italian",
            "cuisines": ["Italian"],
            "ingredients": [
                {"name": "spaghetti", "amount": "400g"},
                {"name": "eggs", "amount": "4 large"},
                {"name": "pancetta", "amount": "200g"},
                {"name": "parmesan cheese", "amount": "100g"},
                {"name": "black pepper", "amount": "1 tsp"},
                {"name": "salt", "amount": "to taste"}
            ],
            "instructions": [
                "Cook spaghetti according to package instructions",
                "Cut pancetta into small cubes and cook until crispy",
                "Beat eggs with grated parmesan and black pepper",
                "Drain pasta and immediately mix with pancetta",
                "Remove from heat and quickly stir in egg mixture",
                "Serve immediately with extra parmesan"
            ],
            "dietaryRestrictions": [],
            "diets": [],
            "readyInMinutes": 20,
            "cookingTime": "20 minutes",
            "difficulty": "intermediate",
            "servings": 4,
            "image": "https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=500",
            "type": "spoonacular",
            "nutrition": {
                "calories": 520,
                "protein": 28,
                "carbs": 45,
                "fat": 24
            }
        },
        {
            "id": "recipe_2",
            "title": "Chicken Teriyaki Bowl",
            "name": "Chicken Teriyaki Bowl",
            "cuisine": "Japanese",
            "cuisines": ["Japanese"],
            "ingredients": [
                {"name": "chicken breast", "amount": "500g"},
                {"name": "jasmine rice", "amount": "2 cups"},
                {"name": "soy sauce", "amount": "1/4 cup"},
                {"name": "mirin", "amount": "2 tbsp"},
                {"name": "brown sugar", "amount": "2 tbsp"},
                {"name": "garlic", "amount": "3 cloves"},
                {"name": "ginger", "amount": "1 inch"},
                {"name": "broccoli", "amount": "2 cups"},
                {"name": "carrots", "amount": "2 medium"}
            ],
            "instructions": [
                "Cook rice according to package instructions",
                "Cut chicken into bite-sized pieces",
                "Make teriyaki sauce by combining soy sauce, mirin, sugar, garlic, and ginger",
                "Cook chicken in a pan until golden",
                "Add teriyaki sauce and simmer until thick",
                "Steam broccoli and carrots until tender",
                "Serve chicken over rice with vegetables"
            ],
            "dietaryRestrictions": [],
            "diets": [],
            "readyInMinutes": 30,
            "cookingTime": "30 minutes",
            "difficulty": "easy",
            "servings": 4,
            "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=500",
            "type": "spoonacular",
            "nutrition": {
                "calories": 450,
                "protein": 35,
                "carbs": 55,
                "fat": 8
            }
        },
        {
            "id": "recipe_3",
            "title": "Mediterranean Quinoa Salad",
            "name": "Mediterranean Quinoa Salad",
            "cuisine": "Mediterranean",
            "cuisines": ["Mediterranean"],
            "ingredients": [
                {"name": "quinoa", "amount": "1 cup"},
                {"name": "cherry tomatoes", "amount": "2 cups"},
                {"name": "cucumber", "amount": "1 large"},
                {"name": "red onion", "amount": "1/2 medium"},
                {"name": "kalamata olives", "amount": "1/2 cup"},
                {"name": "feta cheese", "amount": "100g"},
                {"name": "olive oil", "amount": "1/4 cup"},
                {"name": "lemon juice", "amount": "3 tbsp"},
                {"name": "oregano", "amount": "1 tsp"},
                {"name": "salt", "amount": "to taste"},
                {"name": "black pepper", "amount": "to taste"}
            ],
            "instructions": [
                "Cook quinoa according to package instructions and let cool",
                "Dice tomatoes, cucumber, and red onion",
                "Halve the olives and crumble feta cheese",
                "Make dressing by whisking olive oil, lemon juice, oregano, salt, and pepper",
                "Combine all ingredients in a large bowl",
                "Toss with dressing and refrigerate for 30 minutes before serving"
            ],
            "dietaryRestrictions": ["vegetarian"],
            "diets": ["vegetarian"],
            "readyInMinutes": 25,
            "cookingTime": "25 minutes",
            "difficulty": "easy",
            "servings": 6,
            "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500",
            "type": "spoonacular",
            "nutrition": {
                "calories": 280,
                "protein": 12,
                "carbs": 35,
                "fat": 12
            }
        }
    ]

def create_comprehensive_recipe_set():
    """Create a comprehensive set of recipes covering various cuisines and dietary needs"""
    base_recipes = get_sample_recipes()
    
    # Add more recipes programmatically
    cuisines = ["Italian", "Chinese", "Mexican", "Indian", "Thai", "French", "Greek", "Korean", "American", "Spanish"]
    proteins = ["chicken", "beef", "fish", "tofu", "lentils", "chickpeas", "salmon", "shrimp", "pork", "turkey"]
    vegetables = ["broccoli", "spinach", "carrots", "bell peppers", "zucchini", "mushrooms", "asparagus", "cauliflower", "sweet potato", "eggplant"]
    
    additional_recipes = []
    recipe_id = 4
    
    for cuisine in cuisines:
        for i, protein in enumerate(proteins[:3]):  # Limit to 3 proteins per cuisine
            for j, vegetable in enumerate(vegetables[:2]):  # Limit to 2 vegetables per protein
                recipe = {
                    "id": f"recipe_{recipe_id}",
                    "title": f"{cuisine} {protein.title()} with {vegetable.title()}",
                    "name": f"{cuisine} {protein.title()} with {vegetable.title()}",
                    "cuisine": cuisine,
                    "cuisines": [cuisine],
                    "ingredients": [
                        {"name": protein, "amount": "300g"},
                        {"name": vegetable, "amount": "2 cups"},
                        {"name": "olive oil", "amount": "2 tbsp"},
                        {"name": "garlic", "amount": "2 cloves"},
                        {"name": "salt", "amount": "to taste"},
                        {"name": "black pepper", "amount": "to taste"}
                    ],
                    "instructions": [
                        f"Prepare {protein} by cutting into bite-sized pieces",
                        f"Clean and chop {vegetable}",
                        "Heat olive oil in a large pan",
                        "Add garlic and cook until fragrant",
                        f"Add {protein} and cook until golden",
                        f"Add {vegetable} and cook until tender",
                        "Season with salt and pepper",
                        "Serve hot"
                    ],
                    "dietaryRestrictions": ["vegetarian"] if protein in ["tofu", "lentils", "chickpeas"] else [],
                    "diets": ["vegetarian"] if protein in ["tofu", "lentils", "chickpeas"] else [],
                    "readyInMinutes": 25 + (i * 5),
                    "cookingTime": f"{25 + (i * 5)} minutes",
                    "difficulty": "easy" if i < 2 else "intermediate",
                    "servings": 4,
                    "image": f"https://images.unsplash.com/photo-{1500000000000 + recipe_id}?w=500",
                    "type": "spoonacular",
                    "nutrition": {
                        "calories": 300 + (i * 50),
                        "protein": 25 + (i * 5),
                        "carbs": 20 + (j * 10),
                        "fat": 10 + (i * 3)
                    }
                }
                additional_recipes.append(recipe)
                recipe_id += 1
    
    return base_recipes + additional_recipes

async def populate_railway_database():
    """Populate Railway database with recipes"""
    print("🚀 Starting Railway Database Population")
    print("=" * 50)
    
    try:
        # Initialize recipe cache service
        recipe_cache = RecipeCacheService()
        print("✅ Recipe cache service initialized")
        
        # Get comprehensive recipe set
        recipes = create_comprehensive_recipe_set()
        print(f"📊 Created {len(recipes)} recipes for population")
        
        # Add recipes to cache in batches
        batch_size = 50
        total_added = 0
        
        print(f"🔄 Adding recipes to Railway database...")
        
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            print(f"📦 Processing batch {i//batch_size + 1}/{(len(recipes) + batch_size - 1)//batch_size} ({len(batch)} recipes)")
            
            for recipe in batch:
                try:
                    result = await recipe_cache.add_recipe(recipe)
                    if result:
                        total_added += 1
                    else:
                        print(f"⚠️ Failed to add recipe {recipe.get('title', 'Unknown')}")
                except Exception as e:
                    print(f"⚠️ Error adding recipe {recipe.get('title', 'Unknown')}: {e}")
                    continue
            
            print(f"✓ Added {total_added} recipes so far...")
        
        print(f"🎉 Successfully populated Railway with {total_added} recipes!")
        
        # Verify population
        print("\n🔍 Verifying population...")
        if recipe_cache.recipe_collection:
            count = recipe_cache.recipe_collection.count()
            print(f"  - Total recipes in database: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during population: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🍳 Railway Direct Population Script")
    print("This script will populate the Railway database with recipes")
    print("=" * 60)
    
    # Run the population
    success = asyncio.run(populate_railway_database())
    
    if success:
        print("\n🎉 Database population completed successfully!")
        print("🌐 Your recipes are now available on Railway!")
    else:
        print("\n❌ Database population failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
