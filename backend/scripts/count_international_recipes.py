#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from chromadb.utils import embedding_functions

def count_international_recipes() -> Tuple[int, int, List[Dict]]:
    """
    Count recipes with 'international' tag in the cache
    
    Returns:
        Tuple of (total_recipes, international_count, international_recipes)
    """
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # Get the recipe collection
        recipe_collection = client.get_collection(
            name="recipe_details_cache",
            embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )
        
        # Get all recipes
        results = recipe_collection.get(include=["metadatas"])
        total_recipes = len(results['ids'])
        
        international_recipes = []
        
        for i, metadata in enumerate(results['metadatas']):
            if not metadata:
                continue
                
            # Check cuisines field
            cuisines = []
            if 'cuisines' in metadata and metadata['cuisines']:
                if isinstance(metadata['cuisines'], str):
                    cuisines = [c.strip().lower() for c in metadata['cuisines'].split(',')]
                elif isinstance(metadata['cuisines'], list):
                    cuisines = [c.strip().lower() for c in metadata['cuisines'] if c]
            
            # Check cuisine field (singular)
            if 'cuisine' in metadata and metadata['cuisine']:
                if isinstance(metadata['cuisine'], str):
                    cuisines.append(metadata['cuisine'].strip().lower())
            
            # Check tags field
            tags = []
            if 'tags' in metadata and metadata['tags']:
                if isinstance(metadata['tags'], str):
                    tags = [t.strip().lower() for t in metadata['tags'].split(',')]
                elif isinstance(metadata['tags'], list):
                    tags = [t.strip().lower() for t in metadata['tags'] if t and isinstance(t, str)]
            
            # Check if 'international' is in any of the fields
            if ('international' in cuisines or 
                'international' in [t.lower() for t in tags] or
                any('international' in c for c in cuisines) or
                any('international' in t for t in tags)):
                
                recipe_info = {
                    'id': results['ids'][i],
                    'title': metadata.get('title', 'Untitled'),
                    'cuisines': cuisines,
                    'tags': tags
                }
                international_recipes.append(recipe_info)
        
        return total_recipes, len(international_recipes), international_recipes
        
    except Exception as e:
        print(f"Error counting international recipes: {e}", file=sys.stderr)
        return 0, 0, []

if __name__ == "__main__":
    print("Analyzing recipe cache for 'international' tags...\n")
    
    total, international_count, recipes = count_international_recipes()
    
    print(f"Total recipes in cache: {total}")
    print(f"Recipes with 'international' tag: {international_count} ({international_count/max(1, total)*100:.1f}%)\n")
    
    if international_count > 0:
        print("Recipes with 'international' tag:")
        for i, recipe in enumerate(recipes, 1):
            print(f"\n{i}. {recipe['title']} (ID: {recipe['id']})")
            print(f"   Cuisines: {', '.join(recipe['cuisines']) if recipe['cuisines'] else 'None'}")
            print(f"   Tags: {', '.join(recipe['tags']) if recipe['tags'] else 'None'}")
