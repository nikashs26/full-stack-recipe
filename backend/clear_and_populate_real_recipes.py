#!/usr/bin/env python3
"""
Clear Railway database and populate with real 1115 recipes
"""

import json
import os
import sys
from typing import Dict, List, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def clear_and_populate_real_recipes():
    """Clear current data and populate with real recipes"""
    try:
        from services.recipe_cache_service import RecipeCacheService
        
        print("🧹 Clearing current database...")
        
        # Initialize cache service
        cache = RecipeCacheService()
        print("✓ Cache service initialized")
        
        # Clear existing collections
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
        
        # Load real recipe data
        print("📂 Loading real recipe data...")
        sync_file = "sync_data.json"
        
        if not os.path.exists(sync_file):
            print(f"❌ Sync data file not found: {sync_file}")
            return False
        
        with open(sync_file, 'r') as f:
            sync_data = json.load(f)
        
        recipes = sync_data.get('recipes', [])
        print(f"📊 Found {len(recipes)} real recipes to populate")
        
        if not recipes:
            print("❌ No recipes found in sync data")
            return False
        
        # Add recipes in batches
        batch_size = 100
        total_added = 0
        
        print(f"🔄 Adding {len(recipes)} real recipes to Railway...")
        
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            print(f"📦 Processing batch {i//batch_size + 1}/{(len(recipes) + batch_size - 1)//batch_size} ({len(batch)} recipes)")
            
            # Prepare batch data
            ids = []
            documents = []
            metadatas = []
            search_texts = []
            
            for recipe in batch:
                try:
                    # Extract recipe ID
                    recipe_id = str(recipe.get('id', f"recipe_{total_added}"))
                    
                    # Create metadata
                    metadata = {
                        'id': recipe_id,
                        'title': recipe.get('title', 'Unknown Recipe'),
                        'cuisine': recipe.get('cuisine', 'International'),
                        'cuisines': ','.join(recipe.get('cuisines', [])),
                        'diets': ','.join(recipe.get('diets', [])),
                        'calories': recipe.get('calories', 0),
                        'readyInMinutes': recipe.get('readyInMinutes', 30),
                        'source': recipe.get('source', 'unknown'),
                        'cached_at': str(int(time.time()))
                    }
                    
                    # Create search text
                    search_terms = [
                        recipe.get('title', ''),
                        *[ing.get('name', '') for ing in recipe.get('ingredients', [])],
                        *recipe.get('cuisines', []),
                        *recipe.get('diets', [])
                    ]
                    search_text = ' '.join(filter(None, search_terms)).lower()
                    
                    # Store recipe as JSON document
                    recipe_doc = json.dumps(recipe)
                    
                    ids.append(recipe_id)
                    documents.append(recipe_doc)
                    metadatas.append(metadata)
                    search_texts.append(search_text)
                    
                    total_added += 1
                    
                except Exception as e:
                    print(f"⚠️ Error processing recipe {recipe.get('title', 'Unknown')}: {e}")
                    continue
            
            # Add batch to collections
            try:
                cache.recipe_collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                
                cache.search_collection.upsert(
                    ids=ids,
                    documents=search_texts,
                    metadatas=metadatas
                )
                
                print(f"✓ Added batch of {len(ids)} recipes")
                
            except Exception as e:
                print(f"❌ Error adding batch: {e}")
                continue
        
        print(f"🎉 Successfully populated Railway with {total_added} real recipes!")
        
        # Verify population
        print("\n🔍 Verifying population...")
        if cache.recipe_collection:
            count = cache.recipe_collection.count()
            print(f"  - recipe_details_cache: {count} items")
        
        if cache.search_collection:
            search_count = cache.search_collection.count()
            print(f"  - recipe_search_cache: {search_count} items")
        
        return True
            
    except Exception as e:
        print(f"❌ Error during population: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import time
    success = clear_and_populate_real_recipes()
    sys.exit(0 if success else 1)
