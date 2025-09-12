#!/usr/bin/env python3
"""
Check what recipes are currently stored in ChromaDB
"""

import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def check_chromadb_recipes():
    """Check what recipes are currently in ChromaDB"""
    try:
        from backend.services.recipe_cache_service import RecipeCacheService
        
        print("🔍 Checking ChromaDB recipe collections...")
        recipe_cache = RecipeCacheService()
        
        if not recipe_cache.recipe_collection:
            print("❌ Recipe collection not available")
            return
        
        # Get total count
        total_count = recipe_cache.recipe_collection.count()
        print(f"📊 Total recipes in ChromaDB: {total_count}")
        
        if total_count == 0:
            print("📭 No recipes found in ChromaDB")
            return
        
        # Get sample recipes to analyze sources
        sample_size = min(100, total_count)
        results = recipe_cache.recipe_collection.get(
            limit=sample_size,
            include=['documents', 'metadatas']
        )
        
        print(f"🔍 Analyzing sample of {len(results['documents'])} recipes...")
        
        # Analyze sources
        sources = {}
        cuisines = {}
        types = {}
        
        for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
            try:
                recipe_data = json.loads(doc)
                
                # Check source
                recipe_id = recipe_data.get('id', '')
                source = 'unknown'
                
                if str(recipe_id).startswith('mealdb_'):
                    source = 'TheMealDB'
                elif str(recipe_id).isdigit() and len(str(recipe_id)) >= 6:
                    source = 'Spoonacular'
                elif 'curated_' in str(recipe_id):
                    source = 'Curated (AI Generated)'
                elif recipe_data.get('source'):
                    source = recipe_data['source']
                else:
                    source = 'Static/Hardcoded'
                
                sources[source] = sources.get(source, 0) + 1
                
                # Check cuisine
                cuisine = recipe_data.get('cuisine', meta.get('cuisine', 'Unknown'))
                cuisines[cuisine] = cuisines.get(cuisine, 0) + 1
                
                # Check type
                recipe_type = recipe_data.get('type', meta.get('type', 'Unknown'))
                types[recipe_type] = types.get(recipe_type, 0) + 1
                
                # Show first few recipes
                if i < 5:
                    print(f"   Example {i+1}: {recipe_data.get('title', 'No Title')} ({source})")
                
            except Exception as e:
                print(f"   ⚠️ Error parsing recipe {i}: {e}")
                continue
        
        # Show statistics
        print(f"\n📊 Recipe Sources (from sample of {sample_size}):")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(results['documents'])) * 100
            estimated_total = int((count / len(results['documents'])) * total_count)
            print(f"   {source}: {count} ({percentage:.1f}%) - Est. {estimated_total} total")
        
        print(f"\n🌍 Top Cuisines:")
        for cuisine, count in sorted(cuisines.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {cuisine}: {count}")
        
        print(f"\n🏷️ Recipe Types:")
        for rtype, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
            print(f"   {rtype}: {count}")
        
        # Check search collection too
        if hasattr(recipe_cache, 'search_collection') and recipe_cache.search_collection:
            search_count = recipe_cache.search_collection.count()
            print(f"\n🔍 Search collection count: {search_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_chromadb_collections():
    """Check all ChromaDB collections"""
    try:
        from backend.utils.chromadb_singleton import get_chromadb_client
        
        client = get_chromadb_client()
        if not client:
            print("❌ Could not connect to ChromaDB")
            return
        
        collections = client.list_collections()
        print(f"\n📁 ChromaDB Collections ({len(collections)} total):")
        
        for collection in collections:
            count = collection.count()
            print(f"   {collection.name}: {count} items")
            
            # Show metadata for first few items if it's a recipe collection
            if 'recipe' in collection.name.lower() and count > 0:
                sample = collection.get(limit=3, include=['metadatas'])
                if sample['metadatas']:
                    print(f"      Sample metadata keys: {list(sample['metadatas'][0].keys())}")
        
    except Exception as e:
        print(f"❌ Error checking collections: {e}")

if __name__ == "__main__":
    print("🔍 ChromaDB Recipe Analysis")
    print("=" * 50)
    
    check_chromadb_recipes()
    check_chromadb_collections()
    
    print(f"\n🏁 Analysis completed")
