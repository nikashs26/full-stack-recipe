#!/usr/bin/env python3
"""
Check the current recipe metadata structure to understand the cuisine issue
"""

from backend.services.recipe_cache_service import RecipeCacheService

def check_recipe_metadata():
    """Check the current recipe metadata structure"""
    try:
        rcs = RecipeCacheService()
        results = rcs.recipe_collection.get(limit=5, include=['metadatas'])
        
        print(f"Found {len(results['metadatas'])} recipes")
        print("=" * 50)
        
        for i, metadata in enumerate(results['metadatas']):
            if metadata:
                print(f"\nRecipe {i+1}: {metadata.get('title', 'No title')}")
                print(f"  Metadata keys: {list(metadata.keys())}")
                print(f"  Cuisine: {metadata.get('cuisine', 'No cuisine')}")
                print(f"  Cuisines: {metadata.get('cuisines', 'No cuisines')}")
                print(f"  Type: {type(metadata.get('cuisine', 'No cuisine'))}")
                print("-" * 30)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_recipe_metadata()
