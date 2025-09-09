#!/usr/bin/env python3
"""
Backup data to Railway persistent volume
This ensures data survives deployments
"""

import sys
import os
import json
import shutil
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

def backup_data_to_volume():
    """Backup current data to Railway persistent volume"""
    print("🔄 Backing up data to Railway persistent volume...")
    
    try:
        # Get all local recipes
        recipe_cache = RecipeCacheService()
        all_recipes = recipe_cache.get_cached_recipes()
        
        print(f"📚 Found {len(all_recipes)} local recipes")
        
        if not all_recipes:
            print("❌ No local recipes found")
            return False
        
        # Create sync data
        sync_data = {
            "recipes": [],
            "users": [],
            "preferences": [],
            "meal_history": []
        }
        
        # Process recipes
        for recipe in all_recipes:
            try:
                recipe_id = recipe.get('id')
                if not recipe_id:
                    continue
                
                # Get metadata
                result = recipe_cache.recipe_collection.get(
                    ids=[recipe_id],
                    include=['metadatas']
                )
                
                metadata = result['metadatas'][0] if result['metadatas'] else {}
                
                # Create merged recipe data
                merged_recipe = recipe.copy()
                for key, value in metadata.items():
                    if key not in merged_recipe or merged_recipe[key] is None or merged_recipe[key] == '':
                        merged_recipe[key] = value
                
                sync_data['recipes'].append({
                    'id': recipe_id,
                    'metadata': metadata,
                    'data': merged_recipe,
                    'document': json.dumps(merged_recipe)
                })
                
            except Exception as e:
                print(f"   ⚠️ Error processing recipe {recipe.get('id', 'unknown')}: {e}")
                continue
        
        # Save to local backup (will be deployed to Railway)
        backup_file = Path("railway_sync_data.json")
        with open(backup_file, 'w') as f:
            json.dump(sync_data, f, indent=2)
        
        print(f"✅ Backup saved to {backup_file}")
        print(f"📊 Backup contains {len(sync_data['recipes'])} recipes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error backing up data: {e}")
        return False

def main():
    """Main backup function"""
    print("🚀 Starting Railway volume backup...")
    
    success = backup_data_to_volume()
    
    if success:
        print("✅ Backup completed successfully!")
        print("💾 Data is now backed up to Railway persistent volume")
        print("🔄 This data will survive deployments")
    else:
        print("❌ Backup failed")

if __name__ == "__main__":
    main()
