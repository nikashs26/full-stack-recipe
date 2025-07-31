import chromadb
import json
from pathlib import Path

# Path to ChromaDB
chroma_path = Path("./chroma_db")

# Connect to ChromaDB
client = chromadb.PersistentClient(path=str(chroma_path))

# Get all collections
collections = client.list_collections()
print(f"Found {len(collections)} collections in ChromaDB")

# Look for recipe-related collections
recipe_collections = [
    col for col in collections 
    if 'recipe' in col.name.lower()
]

if not recipe_collections:
    print("No recipe collections found in ChromaDB")
    exit()

print("\nScanning recipe collections...")
for collection in recipe_collections:
    print(f"\nCollection: {collection.name} (id: {collection.id})")
    
    try:
        # Get all items in the collection
        items = collection.get(include=['metadatas'])
        total_items = len(items['ids'])
        print(f"  Total items: {total_items}")
        
        if total_items == 0:
            continue
            
        # Count items with 'International' cuisine
        international_count = 0
        for metadata in items['metadatas']:
            if not metadata:
                continue
                
            # Check both 'cuisine' and 'cuisines' fields
            if 'cuisine' in metadata and metadata['cuisine'] and 'international' in str(metadata['cuisine']).lower():
                international_count += 1
            elif 'cuisines' in metadata and metadata['cuisines']:
                if isinstance(metadata['cuisines'], str):
                    if 'international' in metadata['cuisines'].lower():
                        international_count += 1
                elif isinstance(metadata['cuisines'], list):
                    if any('international' in str(c).lower() for c in metadata['cuisines'] if c):
                        international_count += 1
        
        print(f"  Items with 'International' cuisine: {international_count}")
        if total_items > 0:
            print(f"  Percentage: {(international_count/total_items)*100:.2f}%")
            
    except Exception as e:
        print(f"  Error processing collection: {e}")

print("\nScan complete.")
