#!/usr/bin/env python3
import chromadb
from chromadb.utils import embedding_functions
import os

def count_recipes():
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # Get the recipe collections
        recipe_collection = client.get_collection(
            name="recipe_details_cache",
            embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )
        
        # Get the count of recipes
        count = recipe_collection.count()
        print(f"Total recipes in ChromaDB: {count}")
        
        # Get unique cuisines
        results = recipe_collection.get(include=["metadatas"])
        cuisines = set()
        for meta in results["metadatas"]:
            if meta and "cuisine" in meta:
                cuisines.add(meta["cuisine"])
        
        print(f"\nFound {len(cuisines)} unique cuisines:")
        for cuisine in sorted(cuisines):
            print(f"- {cuisine}")
            
    except Exception as e:
        print(f"Error counting recipes: {e}")

if __name__ == "__main__":
    count_recipes()
