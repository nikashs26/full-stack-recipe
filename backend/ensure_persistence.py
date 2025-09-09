#!/usr/bin/env python3
"""
Ensure ChromaDB persistence on Railway
This script runs on startup to check and restore data if needed
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

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
    """Restore data from backup file"""
    try:
        # Check if we have a backup file
        backup_file = Path("/app/data/railway_sync_data.json")
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

def create_data_directory():
    """Ensure data directory exists"""
    try:
        data_dir = Path("/app/data")
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Data directory exists: {data_dir}")
        return True
    except Exception as e:
        print(f"❌ Error creating data directory: {e}")
        return False

def main():
    """Main persistence check"""
    print("🔍 Checking ChromaDB persistence...")
    
    # Ensure data directory exists
    if not create_data_directory():
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
        print("💡 Data will need to be synced manually")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("🎉 Persistence check completed successfully")
    else:
        print("⚠️ Persistence check failed - manual intervention needed")
