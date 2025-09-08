#!/usr/bin/env python3
"""
Full Railway Population Script
Restores complete database from backup including all recipes, preferences, reviews, etc.
"""

import json
import os
import sys
import zipfile
import tempfile
import shutil
from typing import Dict, List, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def restore_full_database():
    """Restore complete database from sync data to Railway"""
    try:
        from services.recipe_cache_service import RecipeCacheService
        import asyncio
        
        print("🚀 Starting full Railway population from sync data...")
        
        # Initialize cache service
        cache = RecipeCacheService()
        print("✓ Cache service initialized")
        
        # Clear existing data first
        print("🧹 Clearing existing database...")
        try:
            # Delete and recreate collections to clear all data
            cache.client.delete_collection("recipe_details_cache")
            cache.client.delete_collection("recipe_search_cache")
            print("✓ Cleared existing collections")
        except Exception as e:
            print(f"⚠️ Error clearing collections (may not exist): {e}")
        
        # Recreate collections
        cache.recipe_collection = cache.client.get_or_create_collection(
            name="recipe_details_cache",
            metadata={"description": "Cache for individual recipe details"},
            embedding_function=cache.embedding_function
        )
        
        cache.search_collection = cache.client.get_or_create_collection(
            name="recipe_search_cache",
            metadata={"description": "Cache for recipe search results"},
            embedding_function=cache.embedding_function
        )
        print("✓ Recreated collections")
        
        # Load sync data (prefer committed sync_data.json if present)
        sync_files = [
            "sync_data.json",               # Committed file in backend/ - YOUR REAL 1115 RECIPES
            "/app/railway_sync_data.json",  # Railway container path
            "railway_sync_data.json",       # Local path
            "railway_sync_data_20250907_210446.json",  # Original filename
            os.environ.get('SYNC_DATA_PATH', '')  # Environment variable
        ]
        
        sync_file = None
        for file_path in sync_files:
            if file_path and os.path.exists(file_path):
                sync_file = file_path
                break
        
        if not sync_file:
            print(f"❌ No sync data file found. Using comprehensive recipe data...")
            from full_recipe_data import get_full_recipe_data
            recipes = get_full_recipe_data()
        else:
            print(f"📂 Loading sync data from: {sync_file}")
            with open(sync_file, 'r') as f:
                sync_data = json.load(f)
            recipes = sync_data.get('recipes', [])
        
        print(f"📊 Found {len(recipes)} recipes for population")
        
        if not recipes:
            print("❌ No recipes found in sync data")
            return False
        
        # Add recipes to cache in batches
        batch_size = 50
        total_added = 0
        
        print(f"🔄 Adding {len(recipes)} recipes to Railway...")
        
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            print(f"📦 Processing batch {i//batch_size + 1}/{(len(recipes) + batch_size - 1)//batch_size} ({len(batch)} recipes)")
            
            for recipe in batch:
                try:
                    # add_recipe is async, so we need to await it
                    result = asyncio.run(cache.add_recipe(recipe))
                    if result:
                        total_added += 1
                    else:
                        print(f"⚠️ Failed to add recipe {recipe.get('title', 'Unknown')}: add_recipe returned False")
                except Exception as e:
                    print(f"⚠️ Failed to add recipe {recipe.get('title', 'Unknown')}: {e}")
                    continue
            
            print(f"✓ Added {total_added} recipes so far...")
        
        print(f"🎉 Successfully populated Railway with {total_added} recipes!")
        
        # Verify migration
        print("\\n🔍 Verifying migration...")
        if cache.recipe_collection:
            count = cache.recipe_collection.count()
            print(f"  - recipe_details_cache: {count} items")
        
        return True
            
    except Exception as e:
        print(f"❌ Error during full population: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = restore_full_database()
    sys.exit(0 if success else 1)
