#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import chromadb
from services.recipe_search_service import RecipeSearchService

def debug_chroma():
    """Debug ChromaDB contents"""
    
    print("Debugging ChromaDB...")
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path="./chroma_db")
    
    try:
        # Get the collection
        collection = client.get_collection("recipes")
        print(f"Collection found: {collection.name}")
        
        # Get collection info
        count = collection.count()
        print(f"Total documents in collection: {count}")
        
        if count > 0:
            # Get a few sample documents
            results = collection.get(limit=5)
            
            print("\nSample documents:")
            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                print(f"\nDocument {i+1}:")
                print(f"  ID: {results['ids'][i]}")
                print(f"  Name: {metadata.get('name', 'N/A')}")
                print(f"  Cuisine: {metadata.get('cuisine', 'N/A')}")
                print(f"  Document preview: {doc[:200]}...")
                
        else:
            print("No documents found in collection!")
            
    except Exception as e:
        print(f"Error accessing ChromaDB: {e}")
        import traceback
        traceback.print_exc()

def test_simple_search():
    """Test a simple search"""
    
    print("\nTesting simple search...")
    
    search_service = RecipeSearchService()
    
    # Test a simple search
    try:
        results = search_service.semantic_search("chicken", limit=5)
        print(f"Simple 'chicken' search returned {len(results)} results")
        
        if results:
            print("\nTop results:")
            for i, recipe in enumerate(results[:3], 1):
                title = recipe.get('title', recipe.get('name', 'No title'))
                print(f"{i}. {title}")
        else:
            print("No results found!")
            
    except Exception as e:
        print(f"Error in simple search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_chroma()
    test_simple_search() 