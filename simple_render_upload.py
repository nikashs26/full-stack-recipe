#!/usr/bin/env python3
"""
Simple Recipe Upload for Render
Works with existing /api/admin/seed endpoint
"""

import json
import requests
import os
from typing import Dict, List, Any

def prepare_recipes_for_render():
    """Prepare recipes in the format expected by the existing admin/seed endpoint"""
    print("🔍 Finding and preparing recipe data...")
    
    # Try to find the best recipe data source
    recipe_files = ["complete_recipes_backup.json", "recipes_data.json", "backend/recipes_data.json"]
    
    for file_path in recipe_files:
        if os.path.exists(file_path):
            print(f"📁 Found: {file_path}")
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'recipes' in data:
                recipes = data['recipes']
            elif isinstance(data, list):
                recipes = data
            else:
                continue
            
            # Clean and prepare recipes for the existing endpoint
            cleaned_recipes = []
            for i, recipe in enumerate(recipes[:100]):  # Start with first 100
                try:
                    cleaned_recipe = clean_recipe_for_seed_endpoint(recipe, i)
                    if cleaned_recipe:
                        cleaned_recipes.append(cleaned_recipe)
                except Exception as e:
                    print(f"⚠️ Skipped recipe {i}: {e}")
                    continue
            
            print(f"✅ Prepared {len(cleaned_recipes)} recipes from {file_path}")
            return cleaned_recipes, file_path
    
    print("❌ No usable recipe data found")
    return [], None

def clean_recipe_for_seed_endpoint(recipe: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Clean recipe data to work with existing seed endpoint"""
    
    # Basic validation
    if not recipe.get('title') and not recipe.get('name'):
        return None
    
    cleaned = {
        'id': str(recipe.get('id', f'recipe_{index}')),
        'title': recipe.get('title') or recipe.get('name') or f'Recipe {index}',
        'image': recipe.get('image', ''),
        'ingredients': recipe.get('ingredients', []),
        'instructions': recipe.get('instructions', []),
        'ready_in_minutes': recipe.get('ready_in_minutes', 30),
        'source': recipe.get('source', 'imported'),
        'type': 'external'
    }
    
    # Handle ingredients format
    if isinstance(cleaned['ingredients'], str):
        try:
            cleaned['ingredients'] = json.loads(cleaned['ingredients'])
        except:
            cleaned['ingredients'] = []
    
    # Handle instructions format
    if isinstance(cleaned['instructions'], str):
        try:
            cleaned['instructions'] = json.loads(cleaned['instructions'])
        except:
            cleaned['instructions'] = [cleaned['instructions']] if cleaned['instructions'] else []
    
    # Ensure lists are actually lists
    if not isinstance(cleaned['ingredients'], list):
        cleaned['ingredients'] = []
    if not isinstance(cleaned['instructions'], list):
        cleaned['instructions'] = []
    
    # Add simple metadata (avoiding nested objects)
    if recipe.get('cuisines'):
        if isinstance(recipe['cuisines'], list) and recipe['cuisines']:
            cleaned['cuisine'] = recipe['cuisines'][0]  # Take first cuisine
        elif isinstance(recipe['cuisines'], str):
            cleaned['cuisine'] = recipe['cuisines']
    
    if recipe.get('diets'):
        if isinstance(recipe['diets'], list) and recipe['diets']:
            cleaned['diet'] = ', '.join(recipe['diets'][:3])  # Join first 3 diets
        elif isinstance(recipe['diets'], str):
            cleaned['diet'] = recipe['diets']
    
    # Add simple string/number values only (no nested objects)
    if recipe.get('nutrition') and isinstance(recipe['nutrition'], dict):
        # Only add if it's a reasonable value
        cal = recipe['nutrition'].get('calories', 0)
        if cal and isinstance(cal, (int, float)) and cal > 0:
            cleaned['calories'] = int(cal)
    elif recipe.get('calories') and isinstance(recipe.get('calories'), (int, float)):
        cleaned['calories'] = int(recipe['calories'])
    
    return cleaned

def upload_to_render(recipes: List[Dict[str, Any]], render_url: str = "https://dietary-delight.onrender.com", admin_token: str = "390a77929dbe4a50705a8d8cd2888678"):
    """Upload recipes using the existing admin/seed endpoint"""
    
    print(f"🚀 Uploading {len(recipes)} recipes to Render...")
    
    # Save recipes to a temporary file that the seed endpoint can read
    temp_file = "temp_recipes_for_render.json"
    with open(temp_file, 'w') as f:
        json.dump({"recipes": recipes}, f, indent=2)
    
    print(f"📁 Saved recipes to {temp_file}")
    
    # Use the existing seed endpoint
    try:
        payload = {
            "action": "seed_from_data",
            "recipes": recipes[:50],  # Start with first 50 recipes
            "truncate": True  # Clear existing data
        }
        
        response = requests.post(
            f"{render_url}/api/admin/seed",
            headers={
                "Content-Type": "application/json",
                "X-Admin-Token": admin_token
            },
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful: {result}")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def verify_upload(render_url: str = "https://dietary-delight.onrender.com", admin_token: str = "390a77929dbe4a50705a8d8cd2888678"):
    """Verify recipes were uploaded successfully"""
    try:
        response = requests.get(
            f"{render_url}/api/admin/stats",
            params={"token": admin_token},
            timeout=15
        )
        
        if response.status_code == 200:
            stats = response.json()
            recipe_count = stats.get('stats', {}).get('recipes', {}).get('total', {}).get('total', 0)
            print(f"📊 Current recipe count on Render: {recipe_count}")
            return recipe_count
        else:
            print(f"⚠️ Could not verify: {response.status_code}")
            return 0
    except Exception as e:
        print(f"⚠️ Verification error: {e}")
        return 0

def main():
    print("🚀 Simple Recipe Upload for Render")
    print("=" * 40)
    
    # Step 1: Prepare recipes
    recipes, source_file = prepare_recipes_for_render()
    if not recipes:
        print("❌ No recipes to upload")
        return
    
    print(f"📋 Using {len(recipes)} recipes from {source_file}")
    
    # Step 2: Upload recipes
    success = upload_to_render(recipes)
    if not success:
        print("❌ Upload failed")
        return
    
    # Step 3: Verify upload
    count = verify_upload()
    if count > 0:
        print(f"🎉 Success! {count} recipes are now available on Render")
        print("🌐 Check your app: https://dietary-delight.onrender.com")
    else:
        print("⚠️ Upload completed but verification failed")

if __name__ == "__main__":
    main()
