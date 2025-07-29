import sqlite3
import json
from pathlib import Path

# Path to the ChromaDB SQLite file
db_path = Path("./chroma_db/chroma.sqlite3")

if not db_path.exists():
    print(f"Error: Database file not found at {db_path}")
    exit(1)

# Connect to the SQLite database
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("Connected to ChromaDB SQLite database")
print(f"Database file: {db_path.absolute()}")

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]

print("\nAll tables in the database:")
for table in tables:
    print(f"- {table}")

# Look for collections table
collections_table = next((t for t in tables if 'collections' in t.lower()), None)
if not collections_table:
    print("\nWarning: No collections table found in the database")
    exit(1)

print(f"\nFound collections table: {collections_table}")

# Get all collections
cursor.execute(f"SELECT * FROM {collections_table};")
collections = cursor.fetchall()

print(f"\nFound {len(collections)} collections:")
for i, collection in enumerate(collections, 1):
    print(f"{i}. ID: {collection[0]}, Name: {collection[1]}")
    
    # Try to find the embeddings table for this collection
    embeddings_table = f"embeddings_{collection[0].replace('-', '_')}"
    if embeddings_table in tables:
        print(f"   Found embeddings table: {embeddings_table}")
        
        # Count total embeddings
        cursor.execute(f"SELECT COUNT(*) FROM {embeddings_table};")
        count = cursor.fetchone()[0]
        print(f"   Total embeddings: {count}")
        
        # Check for metadata column
        cursor.execute(f"PRAGMA table_info({embeddings_table});")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'metadata' in columns:
            # Count embeddings with 'international' in metadata
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {embeddings_table} 
                WHERE metadata LIKE '%"cuisine":"%International%"%' 
                   OR metadata LIKE '%"cuisine":"%international%"%';
            """)
            international_count = cursor.fetchone()[0]
            print(f"   Recipes with 'International' cuisine: {international_count}")
            
            if international_count > 0:
                # Get some examples
                cursor.execute(f"""
                    SELECT metadata 
                    FROM {embeddings_table} 
                    WHERE metadata LIKE '%"cuisine":"%International%"%' 
                       OR metadata LIKE '%"cuisine":"%international%"%'
                    LIMIT 3;
                """)
                examples = cursor.fetchall()
                print("   Examples (first 3):")
                for i, example in enumerate(examples, 1):
                    try:
                        metadata = json.loads(example[0])
                        print(f"   {i}. ID: {metadata.get('id', 'N/A')}")
                        print(f"      Title: {metadata.get('title', 'N/A')}")
                        print(f"      Cuisine: {metadata.get('cuisine', 'N/A')}")
                    except:
                        print(f"   {i}. Could not parse metadata")
    
    print()  # Add space between collections

conn.close()
