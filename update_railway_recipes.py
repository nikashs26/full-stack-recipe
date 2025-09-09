#!/usr/bin/env python3
"""
Update Railway app with all local recipes
Replace the recipes in railway_app_with_recipes.py with all local recipes
"""

import os
import sys
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

def update_railway_recipes():
    """Update Railway app with all local recipes"""
    print("🚀 Updating Railway app with all local recipes...")
    
    # Initialize local recipe cache
    recipe_cache = RecipeCacheService()
    
    # Get all local recipes
    all_recipes = recipe_cache.recipe_collection.get(include=['metadatas', 'documents'])
    
    if not all_recipes['ids']:
        print("❌ No local recipes found")
        return False
    
    print(f"📊 Found {len(all_recipes['ids'])} local recipes")
    
    # Process recipes
    recipes = []
    for i, (recipe_id, metadata, document) in enumerate(zip(all_recipes['ids'], all_recipes['metadatas'], all_recipes['documents'])):
        try:
            recipe_data = json.loads(document)
            
            # Create recipe in the format expected by Railway app
            recipe = {
                "id": recipe_id,
                "title": recipe_data.get('title', 'Unknown Recipe'),
                "cuisine": recipe_data.get('cuisine', 'unknown'),
                "cuisines": recipe_data.get('cuisines', [recipe_data.get('cuisine', 'unknown')]),
                "diets": recipe_data.get('diets', []),
                "ingredients": recipe_data.get('ingredients', []),
                "instructions": recipe_data.get('instructions', []),
                "image": recipe_data.get('image', ''),
                "description": recipe_data.get('description', ''),
                "calories": recipe_data.get('calories', 0),
                "protein": recipe_data.get('protein', 0),
                "carbs": recipe_data.get('carbs', 0),
                "fat": recipe_data.get('fat', 0),
                "readyInMinutes": recipe_data.get('readyInMinutes', 0),
                "servings": recipe_data.get('servings', 1),
                "source": recipe_data.get('source', 'local'),
                "sourceUrl": recipe_data.get('sourceUrl', ''),
                "spoonacularScore": recipe_data.get('spoonacularScore', 0),
                "healthScore": recipe_data.get('healthScore', 0),
                "pricePerServing": recipe_data.get('pricePerServing', 0),
                "cheap": recipe_data.get('cheap', False),
                "dairyFree": recipe_data.get('dairyFree', False),
                "glutenFree": recipe_data.get('glutenFree', False),
                "ketogenic": recipe_data.get('ketogenic', False),
                "lowFodmap": recipe_data.get('lowFodmap', False),
                "sustainable": recipe_data.get('sustainable', False),
                "vegan": recipe_data.get('vegan', False),
                "vegetarian": recipe_data.get('vegetarian', False),
                "veryHealthy": recipe_data.get('veryHealthy', False),
                "veryPopular": recipe_data.get('veryPopular', False),
                "whole30": recipe_data.get('whole30', False),
                "weightWatcherSmartPoints": recipe_data.get('weightWatcherSmartPoints', 0),
                "dishTypes": recipe_data.get('dishTypes', []),
                "occasions": recipe_data.get('occasions', []),
                "winePairing": recipe_data.get('winePairing', {}),
                "analyzedInstructions": recipe_data.get('analyzedInstructions', []),
                "extendedIngredients": recipe_data.get('extendedIngredients', []),
                "summary": recipe_data.get('summary', ''),
                "winePairingText": recipe_data.get('winePairingText', ''),
                "tags": recipe_data.get('tags', []),
                "usedIngredientCount": recipe_data.get('usedIngredientCount', 0),
                "missedIngredientCount": recipe_data.get('missedIngredientCount', 0),
                "likes": recipe_data.get('likes', 0),
                "favorite": recipe_data.get('favorite', False),
                "comments": recipe_data.get('comments', [])
            }
            
            recipes.append(recipe)
            
            if (i + 1) % 100 == 0:
                print(f"   📦 Processed {i + 1} recipes...")
                
        except Exception as e:
            print(f"   ⚠️  Error processing recipe {recipe_id}: {e}")
            continue
    
    print(f"   ✅ Processed {len(recipes)} recipes successfully")
    
    # Read the current Railway app file
    railway_app_path = 'backend/railway_app_with_recipes.py'
    with open(railway_app_path, 'r') as f:
        app_content = f.read()
    
    # Find the RECIPES = [...] section and replace it
    start_marker = "RECIPES = ["
    end_marker = "]"
    
    start_idx = app_content.find(start_marker)
    if start_idx == -1:
        print("❌ Could not find RECIPES array in Railway app file")
        return False
    
    # Find the end of the RECIPES array
    end_idx = app_content.find(end_marker, start_idx)
    if end_idx == -1:
        print("❌ Could not find end of RECIPES array")
        return False
    
    # Create new content with updated recipes
    new_recipes_json = json.dumps(recipes, indent=2)
    new_content = (
        app_content[:start_idx] + 
        f"RECIPES = {new_recipes_json}" + 
        app_content[end_idx + 1:]
    )
    
    # Write updated app file
    with open(railway_app_path, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Updated Railway app with {len(recipes)} recipes")
    print(f"📊 File size: {os.path.getsize(railway_app_path) / (1024*1024):.1f} MB")
    
    return True

if __name__ == "__main__":
    update_railway_recipes()
