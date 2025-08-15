#!/usr/bin/env python3
"""
Debug what's happening with the cuisine data in the backend
"""

from backend.services.recipe_cache_service import RecipeCacheService
import json

def debug_recipe_cuisine():
    """Debug cuisine data extraction"""
    
    print("🔍 Debugging cuisine data extraction...")
    print("=" * 50)
    
    try:
        rcs = RecipeCacheService()
        
        # Get a few recipes from the cache
        results = rcs.recipe_collection.get(limit=3, include=['documents', 'metadatas'])
        
        for i, doc in enumerate(results['documents']):
            metadata = results['metadatas'][i]
            if metadata:
                print(f"\n🍳 Recipe {i+1}: {metadata.get('title', 'No title')}")
                print(f"  ID: {metadata.get('id', 'No ID')}")
                
                # Check metadata cuisine fields
                print(f"  Metadata cuisine: {metadata.get('cuisine', 'No cuisine')}")
                print(f"  Metadata cuisines: {metadata.get('cuisines', 'No cuisines')}")
                
                # Check document content
                if doc:
                    if isinstance(doc, str):
                        try:
                            recipe_data = json.loads(doc)
                            print(f"  Document cuisine: {recipe_data.get('cuisine', 'No cuisine')}")
                            print(f"  Document cuisines: {recipe_data.get('cuisines', 'No cuisines')}")
                            print(f"  Document keys: {list(recipe_data.keys())}")
                        except json.JSONDecodeError:
                            print(f"  Document: JSON decode error")
                    elif isinstance(doc, dict):
                        print(f"  Document cuisine: {doc.get('cuisine', 'No cuisine')}")
                        print(f"  Document cuisines: {doc.get('cuisines', 'No cuisines')}")
                        print(f"  Document keys: {list(doc.keys())}")
                    else:
                        print(f"  Document type: {type(doc)}")
                else:
                    print(f"  Document: None")
                
                print("---")
        
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    debug_recipe_cuisine()
