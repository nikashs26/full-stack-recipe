#!/usr/bin/env python3
"""
Railway Startup Script
This ensures data is always available on Railway
"""

import os
import sys
import json
import time
from pathlib import Path

def ensure_data_directory():
    """Ensure the data directory exists and is writable"""
    data_dir = Path("/app/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Test if we can write to the directory
    test_file = data_dir / "test_write.txt"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print(f"✅ Data directory is writable: {data_dir}")
        return True
    except Exception as e:
        print(f"❌ Data directory not writable: {e}")
        return False

def check_chromadb_data():
    """Check if ChromaDB has data"""
    try:
        from services.recipe_cache_service import RecipeCacheService
        recipe_cache = RecipeCacheService()
        
        # Check if we have any recipes
        result = recipe_cache.recipe_collection.get(limit=1)
        recipe_count = len(result['ids']) if result['ids'] else 0
        
        print(f"📊 ChromaDB has {recipe_count} recipes")
        return recipe_count > 0
    except Exception as e:
        print(f"❌ Error checking ChromaDB: {e}")
        return False

def restore_from_backup():
    """Restore data from the backup file"""
    try:
        # Check if we have a backup file
        backup_file = Path("railway_sync_data.json")
        if not backup_file.exists():
            print("❌ No backup file found")
            return False
        
        print("📁 Found backup file, restoring data...")
        
        # Load backup data
        with open(backup_file, 'r') as f:
            sync_data = json.load(f)
        
        print(f"📚 Backup contains {len(sync_data['recipes'])} recipes")
        
        # Restore to ChromaDB
        from services.recipe_cache_service import RecipeCacheService
        recipe_cache = RecipeCacheService()
        
        restored_count = 0
        for recipe_data in sync_data['recipes']:
            try:
                recipe_id = recipe_data['id']
                metadata = recipe_data.get('metadata', {})
                document = recipe_data.get('document', '')
                
                if document:
                    # Store in ChromaDB
                    recipe_cache.recipe_collection.upsert(
                        ids=[recipe_id],
                        documents=[document],
                        metadatas=[metadata]
                    )
                    restored_count += 1
                    
            except Exception as e:
                print(f"   ⚠️ Error restoring recipe {recipe_data.get('id', 'unknown')}: {e}")
                continue
        
        print(f"✅ Restored {restored_count} recipes to ChromaDB")
        return restored_count > 0
        
    except Exception as e:
        print(f"❌ Error restoring from backup: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Railway startup - ensuring data persistence...")
    
    # Wait a bit for the app to start
    time.sleep(5)
    
    # Ensure data directory exists
    if not ensure_data_directory():
        print("❌ Cannot create data directory")
        return False
    
    # Check if ChromaDB has data
    if check_chromadb_data():
        print("✅ ChromaDB has data - persistence is working")
        return True
    
    print("⚠️ ChromaDB is empty - attempting restore...")
    
    # Try to restore from backup
    if restore_from_backup():
        print("✅ Data restored successfully")
        return True
    else:
        print("❌ Failed to restore data")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("🎉 Startup completed successfully")
    else:
        print("⚠️ Startup failed - manual intervention needed")
