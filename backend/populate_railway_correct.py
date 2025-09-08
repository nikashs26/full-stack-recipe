#!/usr/bin/env python3
"""
Correct Railway Population Script
Populates Railway with the actual 1115 recipes from sync_data.json
"""

import json
import os
import sys
import time
from typing import Dict, List, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def populate_railway_correct():
    """Populate Railway with the correct 1115 recipes from sync_data.json"""
    try:
        import chromadb
        
        print("🚀 Starting correct Railway population with 1115 recipes...")
        
        # Initialize ChromaDB with persistent storage
        chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
        
        # For Railway deployment, use persistent volume
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
        
        chroma_path = os.path.abspath(chroma_path)
        os.makedirs(chroma_path, exist_ok=True)
        
        client = chromadb.PersistentClient(path=chroma_path)
        print(f"✓ ChromaDB initialized at {chroma_path}")
        
        # Clear existing collections
        print("🧹 Clearing existing collections...")
        try:
            client.delete_collection("recipe_details_cache")
            client.delete_collection("recipe_search_cache")
            print("✓ Cleared existing collections")
        except Exception as e:
            print(f"⚠️ Error clearing collections (may not exist): {e}")
        
        # Create new collections
        recipe_collection = client.get_or_create_collection(
            name="recipe_details_cache",
            metadata={"description": "Cache for individual recipe details"}
        )
        
        search_collection = client.get_or_create_collection(
            name="recipe_search_cache",
            metadata={"description": "Cache for recipe search results"}
        )
        print("✓ Created new collections")
        
        # Load sync data
        sync_file = "sync_data.json"
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
        
        # Process recipes in batches
        batch_size = 100
        total_added = 0
        
        print(f"🔄 Processing {len(recipes)} recipes in batches of {batch_size}...")
        
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(recipes) + batch_size - 1) // batch_size
            
            print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} recipes)")
            
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
                    
                    # Create search text for semantic search
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
                recipe_collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                
                search_collection.upsert(
                    ids=ids,
                    documents=search_texts,
                    metadatas=metadatas
                )
                
                print(f"✓ Added batch of {len(ids)} recipes")
                
            except Exception as e:
                print(f"❌ Error adding batch: {e}")
                continue
        
        print(f"🎉 Successfully populated Railway with {total_added} recipes!")
        
        # Verify population
        print("\n🔍 Verifying population...")
        recipe_count = recipe_collection.count()
        search_count = search_collection.count()
        
        print(f"  - recipe_details_cache: {recipe_count} items")
        print(f"  - recipe_search_cache: {search_count} items")
        
        if recipe_count > 1000:
            print("✅ Population successful - found over 1000 recipes!")
            return True
        else:
            print(f"⚠️ Population may be incomplete - only found {recipe_count} recipes")
            return False
            
    except Exception as e:
        print(f"❌ Error during population: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = populate_railway_correct()
    sys.exit(0 if success else 1)
