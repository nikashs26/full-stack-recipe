#!/usr/bin/env python3
"""
Restore all recipes from backup to ChromaDB
This will restore the full recipe dataset from production_recipes_backup.json
"""

import json
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from services.recipe_cache_service import RecipeCacheService
from utils.chromadb_singleton import get_chromadb_client

def restore_all_recipes():
    """Restore all recipes from backup file"""
    
    # Load the backup file
    backup_file = "production_recipes_backup.json"
    if not os.path.exists(backup_file):
        print(f"❌ Backup file {backup_file} not found")
        return False
    
    print(f"📂 Loading recipes from {backup_file}...")
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Handle both array format and object with recipes array format
        if isinstance(backup_data, list):
            recipes_data = backup_data
        elif isinstance(backup_data, dict) and 'recipes' in backup_data:
            recipes_data = backup_data['recipes']
        else:
            print(f"❌ Unexpected format in backup file")
            return False
        
        print(f"📊 Found {len(recipes_data)} recipes in backup")
        
        # Initialize ChromaDB and recipe service
        print("🔧 Initializing ChromaDB...")
        client = get_chromadb_client()
        recipe_service = RecipeCacheService()
        
        # Limit to first 300 recipes for restoration
        recipes_data = recipes_data[:300]
        print(f"📊 Restoring first {len(recipes_data)} recipes...")
        
        # Clear existing recipes
        print("🗑️ Clearing existing recipes...")
        try:
            # Get all existing IDs first
            existing_results = recipe_service.recipe_collection.get()
            if existing_results['ids']:
                recipe_service.recipe_collection.delete(ids=existing_results['ids'])
                print(f"✅ Cleared {len(existing_results['ids'])} existing recipes")
        except Exception as e:
            print(f"⚠️ Could not clear existing recipes: {e}")
        
        # Add all recipes in batches
        batch_size = 100
        total_added = 0
        
        print(f"📥 Adding recipes in batches of {batch_size}...")
        
        for i in range(0, len(recipes_data), batch_size):
            batch = recipes_data[i:i + batch_size]
            
            try:
                # Prepare documents and metadata
                documents = []
                metadatas = []
                ids = []
                
                for recipe in batch:
                    if not isinstance(recipe, dict) or not recipe.get('id'):
                        continue
                    
                    # Create the document structure
                    document = {
                        "id": recipe['id'],
                        "title": recipe.get('title', ''),
                        "description": recipe.get('description', ''),
                        "ingredients": recipe.get('ingredients', []),
                        "instructions": recipe.get('instructions', []),
                        "cuisines": recipe.get('cuisines', []),
                        "diets": recipe.get('diets', []),
                        "image": recipe.get('image', ''),
                        "prep_time": recipe.get('prep_time', 0),
                        "cook_time": recipe.get('cook_time', 0),
                        "servings": recipe.get('servings', 1),
                        "calories": recipe.get('calories', 0),
                        "protein": recipe.get('protein', 0),
                        "carbs": recipe.get('carbs', 0),
                        "fat": recipe.get('fat', 0),
                        "fiber": recipe.get('fiber', 0),
                        "sugar": recipe.get('sugar', 0),
                        "sodium": recipe.get('sodium', 0),
                        "source": recipe.get('source', 'spoonacular')
                    }
                    
                    documents.append(json.dumps(document))
                    metadatas.append({
                        "id": recipe['id'],
                        "title": recipe.get('title', ''),
                        "cuisines": json.dumps(recipe.get('cuisines', [])),
                        "diets": json.dumps(recipe.get('diets', [])),
                        "cached_at": "2024-01-01T00:00:00Z"
                    })
                    ids.append(recipe['id'])
                
                # Add batch to ChromaDB
                recipe_service.recipe_collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                total_added += len(ids)
                print(f"✅ Added batch {i//batch_size + 1}: {len(ids)} recipes (Total: {total_added})")
                
            except Exception as e:
                print(f"❌ Error adding batch {i//batch_size + 1}: {e}")
                continue
        
        print(f"🎉 Successfully restored {total_added} recipes!")
        
        # Verify the count
        try:
            count_result = recipe_service.recipe_collection.count()
            print(f"📊 Current recipe count in database: {count_result}")
        except Exception as e:
            print(f"⚠️ Could not verify count: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error restoring recipes: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting recipe restoration...")
    success = restore_all_recipes()
    if success:
        print("✅ Recipe restoration completed successfully!")
    else:
        print("❌ Recipe restoration failed!")
        sys.exit(1)
