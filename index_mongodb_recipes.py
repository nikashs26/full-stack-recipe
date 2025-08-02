#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from pymongo import MongoClient
from services.recipe_search_service import RecipeSearchService
import json

def index_mongodb_recipes():
    """Transfer recipes from MongoDB to ChromaDB"""
    
    print("Indexing MongoDB recipes to ChromaDB...")
    
    # Connect to MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.getenv("DB_NAME", "recipes_db")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "recipes")
    
    client = MongoClient(MONGO_URI)
    collection = client[DB_NAME][COLLECTION_NAME]
    
    # Get recipe count
    count = collection.count_documents({})
    print(f"Found {count} recipes in MongoDB")
    
    if count == 0:
        print("No recipes found in MongoDB!")
        return
    
    # Initialize search service
    search_service = RecipeSearchService()
    
    # Get recipes in batches
    batch_size = 100
    indexed_count = 0
    
    for skip in range(0, count, batch_size):
        recipes = list(collection.find({}).skip(skip).limit(batch_size))
        
        print(f"Processing batch {skip//batch_size + 1} ({len(recipes)} recipes)...")
        
        for recipe in recipes:
            try:
                # Convert MongoDB ObjectId to string
                recipe['id'] = str(recipe['_id'])
                
                # Index the recipe
                search_service.index_recipe(recipe)
                indexed_count += 1
                
                if indexed_count % 50 == 0:
                    print(f"Indexed {indexed_count} recipes...")
                    
            except Exception as e:
                print(f"Error indexing recipe {recipe.get('_id')}: {e}")
                continue
    
    print(f"Successfully indexed {indexed_count} recipes to ChromaDB!")
    
    # Verify the indexing
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("recipes")
    chroma_count = collection.count()
    print(f"ChromaDB now contains {chroma_count} documents")

if __name__ == "__main__":
    index_mongodb_recipes() 