#!/usr/bin/env python3
"""
Simple Railway Population Script
Populates Railway with basic recipe data from sync file
"""

import json
import os
import sys
from typing import Dict, List, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def populate_railway_simple():
    """Populate Railway with basic recipe data"""
    try:
        from services.recipe_cache_service import RecipeCacheService
        
        print("🚀 Starting simple Railway population...")
        
        # Initialize cache service
        cache = RecipeCacheService()
        print("✓ Cache service initialized")
        
        # Load sync data
        sync_file = "railway_sync_data_20250907_210446.json"
        if not os.path.exists(sync_file):
            print(f"❌ Sync data file not found: {sync_file}")
            return False
            
        print(f"📂 Loading sync data from: {sync_file}")
        with open(sync_file, 'r') as f:
            sync_data = json.load(f)
        
        recipes = sync_data.get('recipes', [])
        print(f"📊 Found {len(recipes)} recipes in sync data")
        
        if not recipes:
            print("❌ No recipes found in sync data")
            return False
        
        # Populate recipes in batches
        batch_size = 50
        total_added = 0
        
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            print(f"📦 Processing batch {i//batch_size + 1}/{(len(recipes) + batch_size - 1)//batch_size} ({len(batch)} recipes)")
            
            for recipe in batch:
                try:
                    # Add recipe to cache
                    cache.add_recipe(recipe)
                    total_added += 1
                except Exception as e:
                    print(f"⚠️ Failed to add recipe {recipe.get('id', 'unknown')}: {e}")
                    continue
            
            print(f"✓ Added {total_added} recipes so far...")
        
        print(f"🎉 Successfully populated Railway with {total_added} recipes!")
        return True
        
    except Exception as e:
        print(f"❌ Error during population: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = populate_railway_simple()
    sys.exit(0 if success else 1)
