#!/usr/bin/env python3
"""
Restore cuisine data to the recipe_search_cache collection
"""

import asyncio
import chromadb
import json
from backend.services.recipe_cache_service import RecipeCacheService

async def restore_search_cache_cuisines():
    """Restore cuisine data to the recipe_search_cache collection"""
    
    print("🔧 Starting cuisine data restoration for search cache...")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    search_collection = client.get_collection("recipe_search_cache")
    
    print(f"📊 Total recipes in search cache: {search_collection.count()}")
    
    # Get all recipes from search cache
    results = search_collection.get(include=['documents', 'metadatas'])
    
    if not results['documents']:
        print("❌ No documents found in search cache")
        return
    
    print(f"📝 Processing {len(results['documents'])} recipes...")
    
    # Track progress
    updated_count = 0
    skipped_count = 0
    
    for i, doc in enumerate(results['documents']):
        try:
            metadata = results['metadatas'][i] if i < len(results['metadatas']) else {}
            if not metadata:
                continue
                
            recipe_title = metadata.get('title', 'Unknown')
            recipe_id = metadata.get('id', 'Unknown')
            
            # Check if cuisine data is missing
            current_cuisine = metadata.get('cuisine', '')
            current_cuisines = metadata.get('cuisines', '')
            
            if not current_cuisine and not current_cuisines:
                # Try to get cuisine from document content
                if doc and isinstance(doc, str):
                    try:
                        recipe_data = json.loads(doc)
                        doc_cuisine = recipe_data.get('cuisine', '')
                        doc_cuisines = recipe_data.get('cuisines', '')
                        
                        if doc_cuisine or doc_cuisines:
                            # Update metadata with cuisine information
                            updated_metadata = metadata.copy()
                            if doc_cuisine:
                                updated_metadata['cuisine'] = doc_cuisine
                            if doc_cuisines:
                                updated_metadata['cuisines'] = doc_cuisines
                            
                            # Update the collection
                            search_collection.update(
                                ids=[recipe_id],
                                metadatas=[updated_metadata]
                            )
                            
                            updated_count += 1
                            print(f"✅ Updated {recipe_title} with cuisine: {doc_cuisine or doc_cuisines}")
                        else:
                            skipped_count += 1
                            print(f"⏭️  Skipped {recipe_title} - no cuisine data found")
                    except json.JSONDecodeError:
                        skipped_count += 1
                        print(f"⏭️  Skipped {recipe_title} - JSON decode error")
                else:
                    skipped_count += 1
                    print(f"⏭️  Skipped {recipe_title} - no document content")
            else:
                skipped_count += 1
                print(f"⏭️  Skipped {recipe_title} - already has cuisine: {current_cuisine or current_cuisines}")
                
        except Exception as e:
            print(f"❌ Error processing recipe {i}: {e}")
            continue
    
    print(f"\n🎉 Cuisine restoration complete!")
    print(f"✅ Updated: {updated_count} recipes")
    print(f"⏭️  Skipped: {skipped_count} recipes")
    print(f"📊 Total processed: {updated_count + skipped_count}")

if __name__ == "__main__":
    asyncio.run(restore_search_cache_cuisines())
