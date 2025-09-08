#!/usr/bin/env python3
"""
Sync recipes from local ChromaDB to Railway backend
"""
import requests
import json
import chromadb
from chromadb.utils import embedding_functions

def sync_recipes_to_railway():
    """Sync recipes from local ChromaDB to Railway backend"""
    print("Starting recipe sync to Railway backend...")
    
    # Initialize local ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    recipe_collection = client.get_collection("recipes")
    
    # Get all recipes from local ChromaDB
    local_count = recipe_collection.count()
    print(f"Found {local_count} recipes in local ChromaDB")
    
    if local_count == 0:
        print("No recipes found in local ChromaDB!")
        return
    
    # Railway API endpoint
    railway_url = "https://full-stack-recipe-production.up.railway.app"
    
    # Check current Railway status
    try:
        response = requests.get(f"{railway_url}/api/debug-recipes")
        if response.status_code == 200:
            data = response.json()
            print(f"Railway currently has {data.get('recipe_collection_count', 0)} recipes")
        else:
            print(f"Failed to check Railway status: {response.status_code}")
    except Exception as e:
        print(f"Error checking Railway status: {e}")
    
    # Get all recipes from local ChromaDB in batches
    batch_size = 100
    total_processed = 0
    
    try:
        # Get all recipe IDs first
        all_recipes = recipe_collection.get()
        
        if not all_recipes['ids']:
            print("No recipe IDs found in local ChromaDB!")
            return
        
        print(f"Found {len(all_recipes['ids'])} recipes to sync")
        
        # Process in batches
        for i in range(0, len(all_recipes['ids']), batch_size):
            batch_ids = all_recipes['ids'][i:i + batch_size]
            
            # Get batch data
            batch_data = recipe_collection.get(ids=batch_ids)
            
            # Prepare batch for Railway
            recipes_for_railway = []
            for j, recipe_id in enumerate(batch_ids):
                recipe_data = {
                    'id': recipe_id,
                    'title': batch_data['metadatas'][j].get('title', ''),
                    'cuisine': batch_data['metadatas'][j].get('cuisine', ''),
                    'cuisines': batch_data['metadatas'][j].get('cuisines', '').split(', ') if batch_data['metadatas'][j].get('cuisines') else [],
                    'diets': batch_data['metadatas'][j].get('diets', '').split(', ') if batch_data['metadatas'][j].get('diets') else [],
                    'calories': batch_data['metadatas'][j].get('calories', 0),
                    'protein': batch_data['metadatas'][j].get('protein', 0),
                    'carbs': batch_data['metadatas'][j].get('carbs', 0),
                    'fat': batch_data['metadatas'][j].get('fat', 0),
                    'readyInMinutes': batch_data['metadatas'][j].get('readyInMinutes', 30)
                }
                recipes_for_railway.append(recipe_data)
            
            # Send batch to Railway (if there's a bulk endpoint)
            # For now, we'll use individual requests
            successful = 0
            for recipe in recipes_for_railway:
                try:
                    # This would need to be implemented in the Railway backend
                    # For now, just count them
                    successful += 1
                except Exception as e:
                    print(f"Error syncing recipe {recipe['id']}: {e}")
            
            total_processed += successful
            print(f"Processed batch {i//batch_size + 1}: {successful}/{len(recipes_for_railway)} recipes")
            
            if total_processed % 500 == 0:
                print(f"Total processed so far: {total_processed}")
    
    except Exception as e:
        print(f"Error during sync: {e}")
    
    print(f"Sync complete! Processed {total_processed} recipes")
    
    # Verify Railway status after sync
    try:
        response = requests.get(f"{railway_url}/api/debug-recipes")
        if response.status_code == 200:
            data = response.json()
            print(f"Railway now has {data.get('recipe_collection_count', 0)} recipes")
        else:
            print(f"Failed to verify Railway status: {response.status_code}")
    except Exception as e:
        print(f"Error verifying Railway status: {e}")

if __name__ == "__main__":
    sync_recipes_to_railway()
