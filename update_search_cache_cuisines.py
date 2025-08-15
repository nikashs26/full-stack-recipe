#!/usr/bin/env python3
"""
Update the search cache to include the cuisines field from the cuisine field
"""

import asyncio
import chromadb
import json

async def update_search_cache_cuisines():
    """Update search cache to include cuisines field"""
    
    print("🔧 Updating search cache cuisines field...")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    search_collection = client.get_collection("recipe_search_cache")
    
    print(f"📊 Total recipes in search cache: {search_collection.count()}")
    
    # Get all recipes from search cache
    results = search_collection.get(include=['metadatas'])
    
    if not results['metadatas']:
        print("❌ No metadata found in search cache")
        return
    
    print(f"📝 Processing {len(results['metadatas'])} recipes...")
    
    # Track progress
    updated_count = 0
    skipped_count = 0
    
    for i, metadata in enumerate(results['metadatas']):
        try:
            if not metadata:
                continue
                
            recipe_title = metadata.get('title', 'Unknown')
            recipe_id = metadata.get('id', 'Unknown')
            
            # Check if cuisine data exists but cuisines is missing
            current_cuisine = metadata.get('cuisine', '')
            current_cuisines = metadata.get('cuisines', '')
            
            if current_cuisine and not current_cuisines:
                # Create cuisines as a comma-separated string (ChromaDB metadata doesn't support lists)
                if isinstance(current_cuisine, str):
                    cuisines_string = current_cuisine.lower()
                elif isinstance(current_cuisine, list):
                    cuisines_string = ','.join([c.lower() for c in current_cuisine if c])
                else:
                    cuisines_string = str(current_cuisine).lower()
                
                # Update metadata to include cuisines field
                updated_metadata = metadata.copy()
                updated_metadata['cuisines'] = cuisines_string
                
                # Update the collection
                search_collection.update(
                    ids=[recipe_id],
                    metadatas=[updated_metadata]
                )
                
                updated_count += 1
                print(f"✅ Updated {recipe_title} with cuisines: {cuisines_string}")
            else:
                skipped_count += 1
                if current_cuisine:
                    print(f"⏭️  Skipped {recipe_title} - already has cuisines: {current_cuisines}")
                else:
                    print(f"⏭️  Skipped {recipe_title} - no cuisine data")
                
        except Exception as e:
            print(f"❌ Error processing recipe {i}: {e}")
            continue
    
    print(f"\n🎉 Cuisines update complete!")
    print(f"✅ Updated: {updated_count} recipes")
    print(f"⏭️  Skipped: {skipped_count} recipes")
    print(f"📊 Total processed: {updated_count + skipped_count}")

if __name__ == "__main__":
    asyncio.run(update_search_cache_cuisines())
