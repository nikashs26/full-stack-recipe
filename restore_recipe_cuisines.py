#!/usr/bin/env python3
"""
Restore missing cuisine data by merging metadata cuisine info back into recipe documents
"""

import asyncio
import chromadb
import json
from backend.services.recipe_cache_service import RecipeCacheService

async def restore_recipe_cuisines():
    """Restore missing cuisine data from metadata back into recipe documents"""
    
    print("🔧 Starting cuisine data restoration...")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    recipe_collection = client.get_collection("recipe_details_cache")
    
    print(f"📊 Total recipes to process: {recipe_collection.count()}")
    
    # Get all recipes
    results = recipe_collection.get(include=['documents', 'metadatas'])
    
    if not results['documents']:
        print("❌ No recipes found in database")
        return
    
    print(f"📋 Processing {len(results['documents'])} recipes...")
    
    restored_count = 0
    error_count = 0
    
    # Process each recipe
    for i, doc in enumerate(results['documents']):
        try:
            recipe_id = results['metadatas'][i].get('id', f'recipe_{i}')
            recipe_title = results['metadatas'][i].get('title', f'Recipe {i}')
            
            print(f"\n🍽️  Processing {i+1}/{len(results['documents'])}: {recipe_title}")
            
            # Get metadata cuisine info
            metadata = results['metadatas'][i]
            metadata_cuisine = metadata.get('cuisine', '')
            metadata_cuisines = metadata.get('cuisines', '')
            
            print(f"   📍 Metadata cuisine: {metadata_cuisine}")
            print(f"   📍 Metadata cuisines: {metadata_cuisines}")
            
            # Parse existing document
            existing_recipe_data = {}
            if doc and doc.strip():
                try:
                    existing_recipe_data = json.loads(doc)
                    print(f"   📄 Found existing document with {len(existing_recipe_data)} fields")
                except json.JSONDecodeError:
                    print(f"   ⚠️  Document is not valid JSON, will create new one")
                    existing_recipe_data = {}
            
            # Check if cuisine data is missing from document
            doc_cuisine = existing_recipe_data.get('cuisine', '')
            doc_cuisines = existing_recipe_data.get('cuisines', '')
            
            if not doc_cuisine and not doc_cuisines and (metadata_cuisine or metadata_cuisines):
                print(f"   🔧 Restoring missing cuisine data...")
                
                # Restore cuisine data from metadata
                if metadata_cuisine:
                    existing_recipe_data['cuisine'] = metadata_cuisine
                    print(f"   ✅ Restored cuisine: {metadata_cuisine}")
                
                if metadata_cuisines:
                    # Handle both string and list formats
                    if isinstance(metadata_cuisines, str):
                        existing_recipe_data['cuisines'] = [metadata_cuisines]
                    elif isinstance(metadata_cuisines, list):
                        existing_recipe_data['cuisines'] = metadata_cuisines
                    else:
                        existing_recipe_data['cuisines'] = [str(metadata_cuisines)]
                    print(f"   ✅ Restored cuisines: {existing_recipe_data['cuisines']}")
                
                # Also restore other missing fields from metadata if available
                if 'ingredients' not in existing_recipe_data and metadata.get('ingredients'):
                    existing_recipe_data['ingredients'] = metadata.get('ingredients')
                    print(f"   ✅ Restored ingredients from metadata")
                
                if 'instructions' not in existing_recipe_data and metadata.get('instructions'):
                    existing_recipe_data['instructions'] = metadata.get('instructions')
                    print(f"   ✅ Restored instructions from metadata")
                
                if 'diets' not in existing_recipe_data and metadata.get('diets'):
                    existing_recipe_data['diets'] = metadata.get('diets')
                    print(f"   ✅ Restored diets from metadata")
                
                # Update the document
                updated_doc = json.dumps(existing_recipe_data)
                
                recipe_collection.update(
                    ids=[recipe_id],
                    documents=[updated_doc]
                )
                
                print(f"   💾 Updated recipe document with restored cuisine data")
                restored_count += 1
                
            else:
                print(f"   ⏭️  Cuisine data already present in document")
                
        except Exception as e:
            print(f"   ❌ Error processing recipe {i}: {e}")
            error_count += 1
            continue
    
    print(f"\n🎉 Cuisine restoration complete!")
    print(f"📊 Results:")
    print(f"   ✅ Restored: {restored_count} recipes")
    print(f"   ❌ Failed: {error_count} recipes")
    
    if restored_count > 0:
        print(f"\n✅ Successfully restored cuisine data for {restored_count} recipes!")
        print(f"💡 Your Italian recipes should now display correctly instead of 'International'.")
    else:
        print(f"\n❌ No recipes needed cuisine restoration.")

if __name__ == "__main__":
    asyncio.run(restore_recipe_cuisines())
