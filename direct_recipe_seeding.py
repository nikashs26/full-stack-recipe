#!/usr/bin/env python3
"""
Direct recipe seeding script that bypasses the admin API and uses direct ChromaDB approach
"""
import json
import requests

def seed_recipes_directly():
    """
    Create a simplified recipe seeding approach that works around the metadata issue
    """
    
    # First, let's get a few recipes and flatten them manually
    with open('recipes_data.json', 'r') as f:
        recipes = json.load(f)
    
    print(f"Loaded {len(recipes)} recipes from local file")
    
    # Take first recipe and manually flatten its metadata
    sample_recipe = recipes[0]
    print(f"Sample recipe: {sample_recipe['title']}")
    print(f"Nutrition keys: {list(sample_recipe.get('nutrition', {}).keys())}")
    
    # Create a flattened version manually
    flattened_recipe = {}
    for key, value in sample_recipe.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            flattened_recipe[key] = value
        elif isinstance(value, (dict, list)):
            # Convert complex objects to JSON strings  
            flattened_recipe[key] = json.dumps(value)
        else:
            flattened_recipe[key] = str(value)
    
    print(f"Flattened recipe nutrition: {flattened_recipe.get('nutrition', 'N/A')}")
    
    # Create a minimal payload to test with the admin API
    admin_token = "390a77929dbe4a50705a8d8cd2888678"
    
    # Let's try creating a minimal JSON file with flattened recipes
    flattened_recipes = []
    for i, recipe in enumerate(recipes[:5]):  # Just first 5 for testing
        flat_recipe = {}
        for key, value in recipe.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                flat_recipe[key] = value
            elif isinstance(value, (dict, list)):
                flat_recipe[key] = json.dumps(value)
            else:
                flat_recipe[key] = str(value)
        flattened_recipes.append(flat_recipe)
    
    # Save flattened recipes to a test file
    with open('flattened_recipes_test.json', 'w') as f:
        json.dump(flattened_recipes, f, indent=2)
    
    print(f"Created flattened_recipes_test.json with {len(flattened_recipes)} recipes")
    print("Upload this file to your server and test seeding with it")
    
    # Also test the exact API call format
    print("\n" + "="*50)
    print("Testing the exact error scenario...")
    
    # Try to understand exactly what metadata is causing the issue
    problem_recipe = sample_recipe.copy()
    nutrition = problem_recipe.get('nutrition', {})
    
    print(f"Problem metadata type: {type(nutrition)}")
    print(f"Problem metadata content: {nutrition}")
    
    # Show what the ChromaDB metadata should look like
    fixed_nutrition = json.dumps(nutrition)
    print(f"Fixed metadata: {fixed_nutrition} (type: {type(fixed_nutrition)})")

if __name__ == "__main__":
    seed_recipes_directly()
