#!/usr/bin/env python3
"""
Script to examine current recipe data and identify cuisine tag issues
"""

import json
from backend.services.recipe_cache_service import RecipeCacheService

def examine_recipes():
    """Examine current recipes in the cache"""
    try:
        rcs = RecipeCacheService()
        
        print("=== Recipe Search Cache ===")
        search_results = rcs.search_collection.get(limit=10, include=['metadatas'])
        print(f"Total recipes in search cache: {rcs.search_collection.count()}")
        
        for i, metadata in enumerate(search_results['metadatas']):
            if metadata:
                title = metadata.get('title', 'No title')
                cuisine = metadata.get('cuisine', 'No cuisine')
                cuisines = metadata.get('cuisines', 'No cuisines')
                tags = metadata.get('tags', 'No tags')
                
                print(f"\n{i+1}. {title}")
                print(f"   Cuisine: {cuisine}")
                print(f"   Cuisines: {cuisines}")
                print(f"   Tags: {tags}")
        
        print("\n=== Recipe Details Cache ===")
        recipe_results = rcs.recipe_collection.get(limit=10, include=['metadatas'])
        print(f"Total recipes in details cache: {rcs.recipe_collection.count()}")
        
        for i, metadata in enumerate(recipe_results['metadatas']):
            if metadata:
                title = metadata.get('title', 'No title')
                cuisine = metadata.get('cuisine', 'No cuisine')
                cuisines = metadata.get('cuisines', 'No cuisines')
                tags = metadata.get('tags', 'No tags')
                
                print(f"\n{i+1}. {title}")
                print(f"   Cuisine: {cuisine}")
                print(f"   Cuisines: {cuisines}")
                print(f"   Tags: {tags}")
                
    except Exception as e:
        print(f"Error examining recipes: {e}")

if __name__ == "__main__":
    examine_recipes()
