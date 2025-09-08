#!/usr/bin/env python3
"""
Sync recipes from main ChromaDB to backend ChromaDB
"""
import chromadb
from chromadb.utils import embedding_functions

def sync_recipes_to_backend():
    """Copy recipes from main ChromaDB to backend ChromaDB"""
    print("Syncing recipes from main ChromaDB to backend ChromaDB...")
    
    # Initialize main ChromaDB
    main_client = chromadb.PersistentClient(path="./chroma_db")
    main_collection = main_client.get_collection("recipes")
    
    # Initialize backend ChromaDB
    backend_client = chromadb.PersistentClient(path="./backend/chroma_db")
    backend_recipe_collection = backend_client.get_collection("recipe_details_cache")
    backend_search_collection = backend_client.get_collection("recipe_search_cache")
    
    # Get all recipes from main ChromaDB
    main_recipes = main_collection.get()
    print(f"Found {len(main_recipes['ids'])} recipes in main ChromaDB")
    
    if not main_recipes['ids']:
        print("No recipes found in main ChromaDB!")
        return
    
    # Clear backend collections
    print("Clearing backend collections...")
    try:
        backend_recipe_collection.delete(where={})
        backend_search_collection.delete(where={})
    except:
        pass
    
    # Copy recipes to backend collections
    print("Copying recipes to backend ChromaDB...")
    
    # Prepare data for backend collections
    documents = []
    metadatas = []
    ids = []
    
    for i, recipe_id in enumerate(main_recipes['ids']):
        # Get recipe data
        doc_text = main_recipes['documents'][i]
        metadata = main_recipes['metadatas'][i]
        
        # Convert to backend format
        backend_metadata = {
            'id': recipe_id,
            'title': metadata.get('title', ''),
            'cuisine': metadata.get('cuisine', ''),
            'cuisines': metadata.get('cuisines', ''),
            'diets': metadata.get('diets', ''),
            'calories': metadata.get('calories', 0),
            'protein': metadata.get('protein', 0),
            'carbs': metadata.get('carbs', 0),
            'fat': metadata.get('fat', 0),
            'readyInMinutes': metadata.get('readyInMinutes', 30)
        }
        
        documents.append(doc_text)
        metadatas.append(backend_metadata)
        ids.append(recipe_id)
        
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(main_recipes['ids'])} recipes...")
    
    # Add to recipe_details_cache collection
    print("Adding to recipe_details_cache...")
    backend_recipe_collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    # Add to recipe_search_cache collection (same data)
    print("Adding to recipe_search_cache...")
    backend_search_collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    # Verify the sync
    backend_recipe_count = backend_recipe_collection.count()
    backend_search_count = backend_search_collection.count()
    
    print(f"✅ Sync complete!")
    print(f"Backend recipe_details_cache: {backend_recipe_count} recipes")
    print(f"Backend recipe_search_cache: {backend_search_count} recipes")

if __name__ == "__main__":
    sync_recipes_to_backend()
