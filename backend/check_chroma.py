import chromadb
import json
import os

def check_chroma_collections():
    print("Checking ChromaDB collections...")
    
    # Check if ChromaDB directory exists
    if not os.path.exists("./chroma_db"):
        print("\nNo ChromaDB directory found. Run the population script first.")
        return
    
    # Initialize ChromaDB client with persistent storage
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # List all collections
    collections = client.list_collections()
    print(f"\nFound {len(collections)} collections:")
    for collection in collections:
        print(f"\nCollection: {collection.name}")
        
        # Get collection metadata safely
        metadata = getattr(collection, 'metadata', None) or {}
        print(f"Description: {metadata.get('description', 'No description')}")
        
        try:
            # Get all items in collection
            results = collection.get()
            
            print(f"Total items: {len(results['ids'])}")
            if results['ids']:
                print("\nSample items:")
                for i in range(min(3, len(results['ids']))):
                    print(f"\nItem {i+1}:")
                    print(f"ID: {results['ids'][i]}")
                    
                    # Print metadata if available
                    if results.get('metadatas') and i < len(results['metadatas']):
                        print(f"Metadata: {json.dumps(results['metadatas'][i], indent=2)}")
                    
                    # Print document if available
                    if results.get('documents') and i < len(results['documents']):
                        doc = results['documents'][i]
                        if isinstance(doc, str):
                            try:
                                # Try to parse JSON for better formatting
                                doc_json = json.loads(doc)
                                print(f"Document: {json.dumps(doc_json, indent=2)[:500]}...")
                            except:
                                print(f"Document preview: {doc[:200]}...")
                        else:
                            print(f"Document: {str(doc)[:200]}...")
        except Exception as e:
            print(f"Error getting items from collection: {e}")

if __name__ == "__main__":
    check_chroma_collections() 