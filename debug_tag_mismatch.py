#!/usr/bin/env python3
"""
Debug script to find exact differences between local and Railway tags
"""

import requests
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

def get_local_recipe(recipe_id):
    """Get a recipe from local cache"""
    cache = RecipeCacheService()
    result = cache.recipe_collection.get(
        ids=[recipe_id], 
        include=['metadatas', 'documents']
    )
    
    if result['ids']:
        metadata = result['metadatas'][0]
        document = json.loads(result['documents'][0])
        return metadata, document
    return None, None

def get_railway_recipe(recipe_id):
    """Get a recipe from Railway"""
    try:
        response = requests.get(f"https://full-stack-recipe-production.up.railway.app/get_recipe_by_id?id={recipe_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Railway error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching from Railway: {e}")
        return None

def compare_all_fields(recipe_id):
    """Compare ALL fields between local and Railway"""
    print(f"=== DETAILED COMPARISON FOR RECIPE {recipe_id} ===")
    
    # Get local recipe
    local_metadata, local_data = get_local_recipe(recipe_id)
    if not local_metadata:
        print("❌ Recipe not found locally")
        return
    
    # Get Railway recipe
    railway_data = get_railway_recipe(recipe_id)
    if not railway_data:
        print("❌ Recipe not found on Railway")
        return
    
    railway_data_section = railway_data.get('data', {})
    railway_metadata = railway_data.get('metadata', {})
    
    print("\n--- LOCAL METADATA (ALL FIELDS) ---")
    for key, value in sorted(local_metadata.items()):
        print(f"{key}: {value}")
    
    print("\n--- LOCAL DATA (ALL FIELDS) ---")
    for key, value in sorted(local_data.items()):
        print(f"{key}: {value}")
    
    print("\n--- RAILWAY DATA (ALL FIELDS) ---")
    for key, value in sorted(railway_data_section.items()):
        print(f"{key}: {value}")
    
    print("\n--- RAILWAY METADATA (ALL FIELDS) ---")
    for key, value in sorted(railway_metadata.items()):
        print(f"{key}: {value}")
    
    print("\n--- FIELD-BY-FIELD COMPARISON ---")
    
    # Get all unique keys from both sources
    all_keys = set()
    all_keys.update(local_metadata.keys())
    all_keys.update(local_data.keys())
    all_keys.update(railway_data_section.keys())
    all_keys.update(railway_metadata.keys())
    
    for key in sorted(all_keys):
        local_val = local_metadata.get(key, local_data.get(key, 'NOT_FOUND'))
        railway_val = railway_data_section.get(key, railway_metadata.get(key, 'NOT_FOUND'))
        
        if local_val != railway_val:
            print(f"❌ {key}:")
            print(f"   Local: '{local_val}'")
            print(f"   Railway: '{railway_val}'")
        else:
            print(f"✅ {key}: '{local_val}'")

if __name__ == "__main__":
    # Test with a few recipe IDs
    test_ids = ['52961', '52796', '52839']
    
    for recipe_id in test_ids:
        compare_all_fields(recipe_id)
        print("\n" + "="*80 + "\n")
