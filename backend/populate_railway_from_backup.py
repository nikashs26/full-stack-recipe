#!/usr/bin/env python3
"""
Script to populate Railway deployment with recipes from your backup file or URL
This ensures Railway has access to your full recipe collection
"""

import json
import os
import sys
from typing import List, Dict, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.recipe_cache_service import RecipeCacheService
except ImportError as e:
    print(f"⚠️ Could not import services: {e}")
    print("This script should be run from the backend directory")
    sys.exit(1)

# Lazy import requests only if needed to avoid extra deps in some contexts
def _get_requests_module():
    import importlib
    return importlib.import_module('requests')

def resolve_backup_path() -> str:
    """Resolve backup path from env or default repo location"""
    env_path = os.environ.get('BACKUP_RECIPES_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
    # Fallback to repo path relative to backend/
    repo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chroma_db_backup_20250812_204552', 'recipes_backup.json')
    return repo_path

def load_backup_recipes(backup_path: str = None) -> List[Dict[str, Any]]:
    """Load recipes from BACKUP_RECIPES_URL (if set) or from a local backup file"""
    try:
        # 1) Prefer URL if provided
        backup_url = os.environ.get('BACKUP_RECIPES_URL')
        if backup_url:
            try:
                print(f"🌐 Downloading recipes from URL: {backup_url}")
                requests = _get_requests_module()
                resp = requests.get(backup_url, timeout=60)
                resp.raise_for_status()
                recipes = resp.json()
                print(f"✅ Loaded {len(recipes) if isinstance(recipes, list) else 'N/A'} recipes from URL")
                if not isinstance(recipes, list):
                    print("⚠️ URL did not return a list; skipping URL content")
                else:
                    return recipes
            except Exception as e:
                print(f"⚠️ Failed to load from URL: {e}")
                # Fall through to file path
        
        # 2) Fallback to file path
        backup_path = backup_path or resolve_backup_path()
        print(f"📂 Loading recipes from backup file: {backup_path}")
        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_path}")
            return []
        with open(backup_path, 'r', encoding='utf-8') as f:
            recipes = json.load(f)
        print(f"✅ Loaded {len(recipes)} recipes from file")
        return recipes
        
    except Exception as e:
        print(f"❌ Error loading backup: {e}")
        return []

def clean_recipe_for_railway(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and format recipe for Railway storage"""
    
    # Extract title and create a stable-ish ID
    title = recipe.get('title', 'Untitled Recipe')
    recipe_id = recipe.get('id') or f"backup-{abs(hash(title)) % 10000000}"
    
    clean_recipe = {
        'id': str(recipe_id),
        'title': title,
        'description': recipe.get('description', recipe.get('summary', '')),
        'ingredients': recipe.get('ingredients', []),
        'instructions': recipe.get('instructions', ['No instructions provided']),
        'cuisines': recipe.get('cuisines', []),
        'diets': recipe.get('diets', []),
        'dietary_restrictions': recipe.get('dietary_restrictions', []),
        'readyInMinutes': recipe.get('readyInMinutes', 30),
        'servings': recipe.get('servings', 4),
        'image': recipe.get('image', ''),
        'sourceName': recipe.get('sourceName', 'Backup Recipe'),
        'createdAt': recipe.get('createdAt', '2024-01-01T00:00:00Z'),
        'updatedAt': recipe.get('updatedAt', '2024-01-01T00:00:00Z')
    }
    
    # Add nutrition data if available
    if 'nutrition' in recipe and isinstance(recipe['nutrition'], dict):
        clean_recipe['nutrition'] = recipe['nutrition']
    else:
        # legacy flat fields
        calories = recipe.get('calories'); protein = recipe.get('protein'); carbs = recipe.get('carbs'); fat = recipe.get('fat')
        if any(v is not None for v in [calories, protein, carbs, fat]):
            clean_recipe['nutrition'] = {
                'calories': calories or 0,
                'protein': protein or 0,
                'carbs': carbs or 0,
                'fat': fat or 0
            }
    
    # Normalizations
    if not isinstance(clean_recipe['ingredients'], list):
        clean_recipe['ingredients'] = []
    if not isinstance(clean_recipe['instructions'], list):
        if isinstance(clean_recipe['instructions'], str):
            clean_recipe['instructions'] = [clean_recipe['instructions']]
        else:
            clean_recipe['instructions'] = ['No instructions provided']
    if not isinstance(clean_recipe['cuisines'], list):
        clean_recipe['cuisines'] = []
    if not isinstance(clean_recipe['diets'], list):
        clean_recipe['diets'] = []
    
    return clean_recipe

def populate_railway_from_backup():
    """Populate Railway with recipes from backup file or URL"""
    try:
        print("🚀 Populating Railway from backup...")
        
        backup_recipes = load_backup_recipes()
        if not backup_recipes:
            print("❌ No recipes to populate")
            return False
        
        cache_service = RecipeCacheService()
        print(f"📝 Processing {len(backup_recipes)} recipes for Railway...")
        
        batch_size = 100
        successful_adds = 0
        failed_adds = 0
        
        for i in range(0, len(backup_recipes), batch_size):
            batch = backup_recipes[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(backup_recipes) + batch_size - 1) // batch_size
            print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} recipes)...")
            
            for recipe in batch:
                try:
                    clean_recipe = clean_recipe_for_railway(recipe)
                    if hasattr(cache_service, 'add_recipe'):
                        success = cache_service.add_recipe(clean_recipe)
                        if success:
                            successful_adds += 1
                        else:
                            failed_adds += 1
                    else:
                        print("⚠️ Cache service missing add_recipe method")
                        return False
                except Exception as e:
                    print(f"❌ Error processing '{recipe.get('title', 'Unknown')}': {e}")
                    failed_adds += 1
            print(f"📊 Progress: {min(i + batch_size, len(backup_recipes))}/{len(backup_recipes)}")
        
        try:
            final_count = cache_service.get_recipe_count()
            print(f"📊 Final recipe count in Railway: {final_count}")
        except Exception as e:
            print(f"⚠️ Could not get final recipe count: {e}")
        
        print("🎉 Population complete!")
        print(f"✅ Successfully added: {successful_adds}")
        print(f"❌ Failed additions: {failed_adds}")
        return successful_adds > 0
    except Exception as e:
        print(f"❌ Error populating Railway: {e}")
        return False

if __name__ == "__main__":
    populate_railway_from_backup()
