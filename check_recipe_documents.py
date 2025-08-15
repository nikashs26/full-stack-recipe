#!/usr/bin/env python3
"""
Check the actual recipe document content to see what happened during the macro update
"""

from backend.services.recipe_cache_service import RecipeCacheService
import json

def check_recipe_documents():
    """Check the actual recipe document content"""
    try:
        rcs = RecipeCacheService()
        results = rcs.recipe_collection.get(limit=3, include=['documents', 'metadatas'])
        
        print(f"Found {len(results['documents'])} recipes")
        print("=" * 50)
        
        for i, doc in enumerate(results['documents']):
            metadata = results['metadatas'][i]
            if metadata:
                print(f"\nRecipe {i+1}: {metadata.get('title', 'No title')}")
                print(f"  Metadata cuisine: {metadata.get('cuisine', 'No cuisine')}")
                print(f"  Metadata cuisines: {metadata.get('cuisines', 'No cuisines')}")
                
                # Check document content
                if doc and doc.strip():
                    try:
                        recipe_data = json.loads(doc)
                        print(f"  Document cuisine: {recipe_data.get('cuisine', 'No cuisine')}")
                        print(f"  Document cuisines: {recipe_data.get('cuisines', 'No cuisines')}")
                        print(f"  Document keys: {list(recipe_data.keys())}")
                    except json.JSONDecodeError:
                        print(f"  Document is not valid JSON: {doc[:100]}...")
                else:
                    print(f"  Document is empty or None")
                
                print("-" * 30)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_recipe_documents()
