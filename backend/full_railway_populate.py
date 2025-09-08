#!/usr/bin/env python3
"""
Full Railway Population Script
Restores complete database from backup including all recipes, preferences, reviews, etc.
"""

import json
import os
import sys
import zipfile
import tempfile
import shutil
from typing import Dict, List, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def restore_full_database():
    """Restore complete database from backup to Railway"""
    try:
        from services.recipe_cache_service import RecipeCacheService
        import chromadb
        
        print("🚀 Starting full Railway population from backup...")
        
        # Initialize cache service
        cache = RecipeCacheService()
        print("✓ Cache service initialized")
        
        # Path to the backup file (copied to Railway container)
        backup_file = "/app/backup.zip"
        
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found: {backup_file}")
            return False
            
        print(f"📂 Found backup file: {backup_file}")
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"📦 Extracting backup to temporary directory...")
            
            # Extract backup
            with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Path to extracted ChromaDB
            extracted_db_path = os.path.join(temp_dir, "chroma_db")
            
            if not os.path.exists(extracted_db_path):
                print("❌ ChromaDB directory not found in backup")
                return False
            
            print("✓ Backup extracted successfully")
            
            # Create a temporary ChromaDB client to read from backup
            temp_client = chromadb.PersistentClient(path=extracted_db_path)
            
            # Get all collections from backup
            collections = temp_client.list_collections()
            print(f"📊 Found {len(collections)} collections in backup:")
            
            total_items = 0
            for collection in collections:
                count = collection.count()
                total_items += count
                print(f"  - {collection.name}: {count} items")
            
            print(f"📈 Total items to migrate: {total_items}")
            
            # Migrate each collection
            migrated_count = 0
            
            for collection in collections:
                collection_name = collection.name
                print(f"\\n🔄 Migrating collection: {collection_name}")
                
                try:
                    # Get all data from source collection
                    source_data = collection.get(include=['documents', 'metadatas', 'embeddings'])
                    
                    if not source_data.get('ids'):
                        print(f"  ⚠️ No data in {collection_name}, skipping...")
                        continue
                    
                    # Get or create target collection
                    try:
                        target_collection = cache.client.get_collection(collection_name)
                    except:
                        target_collection = cache.client.create_collection(
                            name=collection_name,
                            metadata=collection.metadata or {}
                        )
                    
                    # Prepare data for migration
                    ids = source_data['ids']
                    documents = source_data.get('documents', [])
                    metadatas = source_data.get('metadatas', [])
                    embeddings = source_data.get('embeddings', [])
                    
                    # Migrate in batches to avoid memory issues
                    batch_size = 100
                    for i in range(0, len(ids), batch_size):
                        batch_ids = ids[i:i + batch_size]
                        batch_docs = documents[i:i + batch_size] if documents else None
                        batch_metas = metadatas[i:i + batch_size] if metadatas else None
                        batch_embeds = embeddings[i:i + batch_size] if embeddings else None
                        
                        # Prepare upsert data
                        upsert_data = {'ids': batch_ids}
                        if batch_docs:
                            upsert_data['documents'] = batch_docs
                        if batch_metas:
                            upsert_data['metadatas'] = batch_metas
                        if batch_embeds:
                            upsert_data['embeddings'] = batch_embeds
                        
                        # Upsert to target collection
                        target_collection.upsert(**upsert_data)
                        
                        migrated_count += len(batch_ids)
                        print(f"  ✓ Migrated batch {i//batch_size + 1}/{(len(ids) + batch_size - 1)//batch_size} ({len(batch_ids)} items)")
                    
                    print(f"  ✅ Successfully migrated {collection_name}: {len(ids)} items")
                    
                except Exception as e:
                    print(f"  ❌ Failed to migrate {collection_name}: {e}")
                    continue
            
            print(f"\\n🎉 Migration completed!")
            print(f"📊 Total items migrated: {migrated_count}")
            
            # Verify migration
            print("\\n🔍 Verifying migration...")
            current_collections = cache.client.list_collections()
            for collection in current_collections:
                count = collection.count()
                print(f"  - {collection.name}: {count} items")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during full population: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = restore_full_database()
    sys.exit(0 if success else 1)
