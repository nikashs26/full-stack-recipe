#!/usr/bin/env python3
"""
Script to populate Railway deployment with recipes from your backup file
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

def load_backup_recipes(backup_path: str = "../chroma_db_backup_20250812_204552/recipes_backup.json") -> List[Dict[str, Any]]:
    """Load recipes from your backup file"""
    try:
        print(f"📂 Loading recipes from backup: {backup_path}")
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_path}")
            return []
        
        with open(backup_path, 'r', encoding='utf-8') as f:
            recipes = json.load(f)
        
        print(f"✅ Loaded {len(recipes)} recipes from backup")
        return recipes
        
    except Exception as e:
        print(f"❌ Error loading backup: {e}")
        return []

def clean_recipe_for_railway(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and format recipe for Railway storage"""
    
    # Extract title and create a proper ID
    title = recipe.get('title', 'Untitled Recipe')
    recipe_id = f"backup-{hash(title) % 1000000}"
    
    # Clean recipe object
    clean_recipe = {
        'id': recipe_id,
        'title': title,
        'description': recipe.get('description', ''),
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
    if 'nutrition' in recipe:
        clean_recipe['nutrition'] = recipe['nutrition']
    elif 'calories' in recipe:
        clean_recipe['nutrition'] = {
            'calories': recipe.get('calories', 0),
            'protein': recipe.get('protein', 0),
            'carbs': recipe.get('carbs', 0),
            'fat': recipe.get('fat', 0)
        }
    
    # Ensure ingredients is a list
    if not isinstance(clean_recipe['ingredients'], list):
        clean_recipe['ingredients'] = []
    
    # Ensure instructions is a list
    if not isinstance(clean_recipe['instructions'], list):
        if isinstance(clean_recipe['instructions'], str):
            clean_recipe['instructions'] = [clean_recipe['instructions']]
        else:
            clean_recipe['instructions'] = ['No instructions provided']
    
    # Ensure cuisines is a list
    if not isinstance(clean_recipe['cuisines'], list):
        clean_recipe['cuisines'] = []
    
    # Ensure diets is a list
    if not isinstance(clean_recipe['diets'], list):
        clean_recipe['diets'] = []
    
    return clean_recipe

def populate_railway_from_backup():
    """Populate Railway with recipes from backup file"""
    try:
        print("🚀 Populating Railway from backup recipes...")
        
        # Load recipes from backup
        backup_recipes = load_backup_recipes()
        if not backup_recipes:
            print("❌ No recipes to populate")
            return False
        
        # Initialize Railway cache service
        cache_service = RecipeCacheService()
        
        print(f"📝 Processing {len(backup_recipes)} recipes for Railway...")
        
        # Process recipes in batches to avoid memory issues
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
                    # Clean recipe for Railway
                    clean_recipe = clean_recipe_for_railway(recipe)
                    
                    # Add to Railway cache
                    if hasattr(cache_service, 'add_recipe'):
                        success = cache_service.add_recipe(clean_recipe)
                        if success:
                            successful_adds += 1
                        else:
                            failed_adds += 1
                            print(f"⚠️ Failed to add: {clean_recipe['title']}")
                    else:
                        print(f"⚠️ Cache service doesn't have add_recipe method")
                        return False
                        
                except Exception as e:
                    print(f"❌ Error processing recipe '{recipe.get('title', 'Unknown')}': {e}")
                    failed_adds += 1
            
            # Progress update
            print(f"📊 Progress: {min(i + batch_size, len(backup_recipes))}/{len(backup_recipes)} recipes processed")
        
        # Verify final count
        try:
            final_count = cache_service.get_recipe_count()
            print(f"📊 Final recipe count in Railway: {final_count}")
        except Exception as e:
            print(f"⚠️ Could not get final recipe count: {e}")
        
        print(f"🎉 Population complete!")
        print(f"✅ Successfully added: {successful_adds} recipes")
        print(f"❌ Failed additions: {failed_adds} recipes")
        
        return successful_adds > 0
        
    except Exception as e:
        print(f"❌ Error populating Railway: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Railway Recipe Population from Backup")
    print("=" * 50)
    
    # Check if backup file exists
    backup_path = "../chroma_db_backup_20250812_204552/recipes_backup.json"
    if not os.path.exists(backup_path):
        print(f"❌ Backup file not found: {backup_path}")
        print("💡 Make sure you're running this from the backend directory")
        return
    
    # Confirm population
    print(f"📂 Found backup file: {backup_path}")
    confirm = input("\nProceed with populating Railway from backup? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Population cancelled")
        return
    
    # Perform population
    success = populate_railway_from_backup()
    
    if success:
        print(f"\n🎉 Railway population successful!")
        print(f"🌐 Your Railway deployment now has your full recipe collection!")
    else:
        print(f"\n❌ Railway population failed")
        print("💡 Check the logs above for error details")

if __name__ == "__main__":
    main()
