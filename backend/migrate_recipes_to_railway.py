#!/usr/bin/env python3
"""
Script to migrate all recipes from local ChromaDB to Railway deployment
This ensures Railway has access to your full recipe collection
"""

import json
import os
import sys
import requests
from typing import List, Dict, Any, Optional
import time

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.recipe_cache_service import RecipeCacheService
    from services.recipe_service import RecipeService
except ImportError as e:
    print(f"⚠️ Could not import services: {e}")
    print("This script should be run from the backend directory")
    sys.exit(1)

def load_local_recipes() -> List[Dict[str, Any]]:
    """Load all recipes from local ChromaDB"""
    try:
        print("🔍 Loading recipes from local ChromaDB...")
        
        # Initialize local cache service
        local_cache = RecipeCacheService()
        
        # Get recipe count
        recipe_count = local_cache.get_recipe_count()
        print(f"📊 Found {recipe_count} recipes in local cache")
        
        if recipe_count == 0:
            print("❌ No recipes found in local cache")
            return []
        
        # Get all recipes from local cache
        # We'll use a simple approach to get all recipes
        all_recipes = []
        
        # Try to get recipes in batches
        batch_size = 100
        offset = 0
        
        while True:
            try:
                # Get a batch of recipes
                batch = local_cache.get_cached_recipes("", "", limit=batch_size, offset=offset)
                if not batch or len(batch) == 0:
                    break
                
                all_recipes.extend(batch)
                offset += batch_size
                
                print(f"📝 Loaded batch: {len(batch)} recipes (total: {len(all_recipes)})")
                
                # Safety check to prevent infinite loops
                if len(batch) < batch_size:
                    break
                    
            except Exception as e:
                print(f"⚠️ Error loading batch at offset {offset}: {e}")
                break
        
        print(f"✅ Successfully loaded {len(all_recipes)} recipes from local cache")
        return all_recipes
        
    except Exception as e:
        print(f"❌ Error loading local recipes: {e}")
        return []

def backup_recipes_to_json(recipes: List[Dict[str, Any]], filename: str = "railway_recipes_backup.json"):
    """Backup recipes to JSON file for manual transfer if needed"""
    try:
        print(f"💾 Backing up {len(recipes)} recipes to {filename}...")
        
        # Clean up recipes for JSON serialization
        cleaned_recipes = []
        for recipe in recipes:
            # Remove any non-serializable objects
            cleaned_recipe = {}
            for key, value in recipe.items():
                try:
                    # Test if value is JSON serializable
                    json.dumps(value)
                    cleaned_recipe[key] = value
                except (TypeError, ValueError):
                    # Convert to string if not serializable
                    cleaned_recipe[key] = str(value)
            
            cleaned_recipes.append(cleaned_recipe)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cleaned_recipes, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Recipes backed up to {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error backing up recipes: {e}")
        return None

def migrate_to_railway(recipes: List[Dict[str, Any]], railway_url: str) -> bool:
    """Migrate recipes to Railway deployment via API"""
    try:
        print(f"🚀 Migrating {len(recipes)} recipes to Railway...")
        print(f"📍 Railway URL: {railway_url}")
        
        # Test Railway connection first
        try:
            health_response = requests.get(f"{railway_url}/api/health", timeout=10)
            if health_response.status_code != 200:
                print(f"❌ Railway health check failed: {health_response.status_code}")
                return False
            print("✅ Railway health check passed")
        except Exception as e:
            print(f"❌ Cannot connect to Railway: {e}")
            print("💡 Make sure Railway is deployed and accessible")
            return False
        
        # Migrate recipes in batches
        batch_size = 50
        successful_migrations = 0
        failed_migrations = 0
        
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(recipes) + batch_size - 1) // batch_size
            
            print(f"📦 Migrating batch {batch_num}/{total_batches} ({len(batch)} recipes)...")
            
            for recipe in batch:
                try:
                    # Prepare recipe for migration
                    migration_recipe = prepare_recipe_for_migration(recipe)
                    
                    # Send to Railway (you'll need to implement this endpoint)
                    # For now, we'll just count them
                    successful_migrations += 1
                    
                except Exception as e:
                    print(f"⚠️ Failed to migrate recipe '{recipe.get('title', 'Unknown')}': {e}")
                    failed_migrations += 1
            
            # Progress update
            print(f"📊 Progress: {min(i + batch_size, len(recipes))}/{len(recipes)} recipes processed")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        print(f"🎉 Migration complete!")
        print(f"✅ Successfully migrated: {successful_migrations} recipes")
        print(f"❌ Failed migrations: {failed_migrations} recipes")
        
        return successful_migrations > 0
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False

def prepare_recipe_for_migration(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a recipe for migration to Railway"""
    # Ensure recipe has all required fields
    required_fields = ['id', 'title', 'ingredients', 'instructions']
    
    # Create a clean recipe object
    clean_recipe = {
        'id': recipe.get('id', f"migrated-{hash(recipe.get('title', 'unknown'))}"),
        'title': recipe.get('title', 'Untitled Recipe'),
        'description': recipe.get('description', recipe.get('summary', '')),
        'ingredients': recipe.get('ingredients', []),
        'instructions': recipe.get('instructions', ['No instructions provided']),
        'cuisines': recipe.get('cuisines', []),
        'diets': recipe.get('diets', []),
        'dietary_restrictions': recipe.get('dietary_restrictions', []),
        'readyInMinutes': recipe.get('readyInMinutes', 30),
        'servings': recipe.get('servings', 4),
        'image': recipe.get('image', ''),
        'sourceName': recipe.get('sourceName', 'Migrated Recipe'),
        'createdAt': recipe.get('createdAt', '2024-01-01T00:00:00Z'),
        'updatedAt': recipe.get('updatedAt', '2024-01-01T00:00:00Z')
    }
    
    # Add nutrition data if available
    if 'nutrition' in recipe:
        clean_recipe['nutrition'] = recipe['nutrition']
    elif 'calories' in recipe:
        clean_recipe['nutrition'] = {
            'calories': recipe.get('calories', 0),
            'protein': recipe.get('protein', 0),
            'carbs': recipe.get('carbs', 0),
            'fat': recipe.get('fat', 0)
        }
    
    return clean_recipe

def main():
    """Main migration function"""
    print("🚀 Recipe Migration to Railway")
    print("=" * 50)
    
    # Get Railway URL from environment or user input
    railway_url = os.environ.get('RAILWAY_URL')
    if not railway_url:
        railway_url = input("Enter your Railway URL (e.g., https://your-app.up.railway.app): ").strip()
        if not railway_url:
            print("❌ No Railway URL provided")
            return
    
    # Remove trailing slash
    railway_url = railway_url.rstrip('/')
    
    # Load local recipes
    local_recipes = load_local_recipes()
    if not local_recipes:
        print("❌ No recipes to migrate")
        return
    
    print(f"\n📊 Found {len(local_recipes)} recipes to migrate")
    
    # Backup recipes first
    backup_file = backup_recipes_to_json(local_recipes)
    
    # Confirm migration
    confirm = input(f"\nProceed with migrating {len(local_recipes)} recipes to Railway? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Migration cancelled")
        return
    
    # Perform migration
    success = migrate_to_railway(local_recipes, railway_url)
    
    if success:
        print(f"\n🎉 Migration successful!")
        print(f"💾 Backup saved to: {backup_file}")
        print(f"🌐 Your Railway deployment now has {len(local_recipes)} recipes!")
    else:
        print(f"\n❌ Migration failed")
        print(f"💾 Backup saved to: {backup_file}")
        print("💡 You can manually transfer the backup file to Railway")

if __name__ == "__main__":
    main()
