#!/usr/bin/env python3
"""
Check what recipe collections exist and how many recipes are in each
"""

from backend.services.recipe_cache_service import RecipeCacheService
import chromadb

def check_recipe_collections():
    """Check recipe collections"""
    
    print("🔍 Checking recipe collections...")
    print("=" * 50)
    
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # List all collections
        collections = client.list_collections()
        print(f"📚 Found {len(collections)} collections:")
        for collection in collections:
            print(f"  - {collection.name}")
        
        print("\n" + "=" * 50)
        
        # Check each collection
        for collection in collections:
            print(f"\n📖 Collection: {collection.name}")
            try:
                count = collection.count()
                print(f"  Recipe count: {count}")
                
                if count > 0:
                    # Get a sample recipe
                    sample = collection.get(limit=1, include=['metadatas'])
                    if sample['metadatas'] and sample['metadatas'][0]:
                        metadata = sample['metadatas'][0]
                        print(f"  Sample recipe: {metadata.get('title', 'No title')}")
                        print(f"  Sample cuisine: {metadata.get('cuisine', 'No cuisine')}")
                        print(f"  Sample cuisines: {metadata.get('cuisines', 'No cuisines')}")
                
            except Exception as e:
                print(f"  Error accessing collection: {e}")
        
        print("\n" + "=" * 50)
        
        # Check the RecipeCacheService specifically
        print("\n🔧 Checking RecipeCacheService...")
        rcs = RecipeCacheService()
        
        # Check search collection
        if rcs.search_collection:
            search_count = rcs.search_collection.count()
            print(f"  Search collection count: {search_count}")
        else:
            print("  Search collection: Not initialized")
        
        # Check recipe collection
        if rcs.recipe_collection:
            recipe_count = rcs.recipe_collection.count()
            print(f"  Recipe collection count: {recipe_count}")
        else:
            print("  Recipe collection: Not initialized")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_recipe_collections()
