#!/usr/bin/env python3
"""
Restore recipes from complete_sync_data.json to ChromaDB
"""
import json
import chromadb
from chromadb.utils import embedding_functions

def restore_recipes_from_sync_data():
    """Restore recipes from complete_sync_data.json"""
    print("Starting recipe restoration from complete_sync_data.json...")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    
    # Get or create the recipes collection
    recipe_collection = client.get_or_create_collection(
        name="recipes",
        metadata={"description": "Main recipe collection"},
        embedding_function=embedding_function
    )
    
    # Load the sync data
    try:
        with open('complete_sync_data.json', 'r') as f:
            data = json.load(f)
        
        recipes = data.get('recipes', [])
        print(f"Found {len(recipes)} recipes in sync data")
        
        if not recipes:
            print("No recipes found in sync data!")
            return
        
        # Process and store recipes
        successful = 0
        for i, recipe in enumerate(recipes):
            try:
                # Create document text for embedding
                doc_text = f"{recipe.get('title', '')} {recipe.get('cuisine', '')} {' '.join(recipe.get('cuisines', []))}"
                
                # Prepare metadata
                metadata = {
                    'id': recipe.get('id', f'recipe_{i}'),
                    'title': recipe.get('title', ''),
                    'cuisine': recipe.get('cuisine', ''),
                    'cuisines': ', '.join(recipe.get('cuisines', [])),
                    'diets': ', '.join(recipe.get('diets', [])),
                    'calories': recipe.get('calories', 0),
                    'protein': recipe.get('protein', 0),
                    'carbs': recipe.get('carbs', 0),
                    'fat': recipe.get('fat', 0),
                    'readyInMinutes': recipe.get('readyInMinutes', 30)
                }
                
                # Add to collection
                recipe_collection.add(
                    documents=[doc_text],
                    metadatas=[metadata],
                    ids=[recipe.get('id', f'recipe_{i}')]
                )
                successful += 1
                
                if (i + 1) % 100 == 0:
                    print(f"Processed {i + 1}/{len(recipes)} recipes...")
                    
            except Exception as e:
                print(f"Error processing recipe {i}: {e}")
                continue
        
        print(f"Successfully restored {successful} recipes to ChromaDB")
        
        # Verify the count
        final_count = recipe_collection.count()
        print(f"Final recipe count in ChromaDB: {final_count}")
        
    except Exception as e:
        print(f"Error loading sync data: {e}")

if __name__ == "__main__":
    restore_recipes_from_sync_data()
