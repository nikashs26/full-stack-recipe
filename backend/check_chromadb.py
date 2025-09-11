import chromadb
import os

def check_chromadb():
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # List all collections
        collections = client.list_collections()
        print("\n=== ChromaDB Collections ===")
        for collection in collections:
            print(f"- {collection.name}: {collection.count()} items")
        
        # Check recipe collections
        for collection_name in ["recipe_search_cache", "recipe_details_cache"]:
            try:
                collection = client.get_collection(name=collection_name)
                print(f"\n=== {collection_name} (count: {collection.count()}) ===")
                
                # Get first few items
                if collection.count() > 0:
                    items = collection.get(limit=3)
                    print("Sample items:")
                    for i, (id, doc) in enumerate(zip(items['ids'], items.get('documents', []))):
                        print(f"\nItem {i+1} (ID: {id}):")
                        print(doc[:500] + (doc[500:] and '...'))  # Print first 500 chars
                
            except Exception as e:
                print(f"\nError checking {collection_name}: {str(e)}")
                
    except Exception as e:
        print(f"Error initializing ChromaDB: {str(e)}")

if __name__ == "__main__":
    check_chromadb()
