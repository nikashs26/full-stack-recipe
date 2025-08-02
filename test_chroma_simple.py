#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import chromadb

def test_chroma_basic():
    """Test basic ChromaDB functionality"""
    
    print("Testing basic ChromaDB...")
    
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
            results = collection.get(limit=3)
            
            print("\nSample documents:")
            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                print(f"\nDocument {i+1}:")
                print(f"  ID: {results['ids'][i]}")
                print(f"  Name: {metadata.get('name', 'N/A')}")
                print(f"  Cuisine: {metadata.get('cuisine', 'N/A')}")
                print(f"  Document preview: {doc[:100]}...")
                
            # Test a simple search
            print("\nTesting simple search...")
            search_results = collection.query(
                query_texts=["chicken"],
                n_results=5,
                include=['documents', 'metadatas', 'distances']
            )
            
            print(f"Search for 'chicken' returned {len(search_results['documents'][0])} results")
            
            if search_results['documents'][0]:
                print("\nSearch results:")
                for i, (doc, metadata) in enumerate(zip(search_results['documents'][0], search_results['metadatas'][0])):
                    print(f"{i+1}. {metadata.get('name', 'No name')} - {metadata.get('cuisine', 'No cuisine')}")
                    print(f"   Distance: {search_results['distances'][0][i]}")
                    print(f"   Preview: {doc[:80]}...")
            else:
                print("No search results found!")
                
        else:
            print("No documents found in collection!")
            
    except Exception as e:
        print(f"Error accessing ChromaDB: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chroma_basic() 