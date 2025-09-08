#!/usr/bin/env python3
"""
Migration script to move ChromaDB data to persistent storage
This script helps migrate existing data to the new persistent volume structure
"""

import os
import shutil
import sys
from pathlib import Path

def migrate_chromadb_data():
    """Migrate ChromaDB data from old location to persistent storage"""
    
    # Determine source and destination paths
    old_path = "./chroma_db"
    new_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
    
    # For Railway deployment, use persistent volume
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        new_path = '/app/data/chroma_db'
    
    print(f"🔄 Migrating ChromaDB data...")
    print(f"   From: {old_path}")
    print(f"   To: {new_path}")
    
    # Check if old data exists
    if not os.path.exists(old_path):
        print(f"⚠️  No existing data found at {old_path}")
        return True
    
    # Create destination directory
    os.makedirs(new_path, exist_ok=True)
    
    try:
        # Copy data to new location
        if os.path.exists(new_path) and os.listdir(new_path):
            print(f"⚠️  Destination {new_path} already contains data")
            print(f"   Skipping migration to avoid data loss")
            return True
        
        # Copy all files and directories
        for item in os.listdir(old_path):
            src = os.path.join(old_path, item)
            dst = os.path.join(new_path, item)
            
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
        
        print(f"✅ Successfully migrated ChromaDB data to {new_path}")
        
        # Verify migration
        old_count = len(os.listdir(old_path)) if os.path.exists(old_path) else 0
        new_count = len(os.listdir(new_path)) if os.path.exists(new_path) else 0
        
        print(f"   Old location files: {old_count}")
        print(f"   New location files: {new_count}")
        
        if new_count >= old_count:
            print(f"✅ Migration verification successful")
            return True
        else:
            print(f"❌ Migration verification failed - file count mismatch")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def verify_persistent_storage():
    """Verify that persistent storage is working correctly"""
    
    new_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
    
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        new_path = '/app/data/chroma_db'
    
    print(f"🔍 Verifying persistent storage at {new_path}")
    
    # Check if directory exists and is writable
    if not os.path.exists(new_path):
        print(f"❌ Persistent storage directory does not exist")
        return False
    
    if not os.access(new_path, os.W_OK):
        print(f"❌ Persistent storage directory is not writable")
        return False
    
    # Test creating a file
    test_file = os.path.join(new_path, "test_persistence.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print(f"✅ Persistent storage is working correctly")
        return True
    except Exception as e:
        print(f"❌ Persistent storage test failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 ChromaDB Persistent Storage Migration")
    print("=" * 50)
    
    # Verify persistent storage
    if not verify_persistent_storage():
        print("❌ Cannot proceed - persistent storage not available")
        sys.exit(1)
    
    # Migrate data
    if migrate_chromadb_data():
        print("🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Deploy to Railway")
        print("2. Test that data persists across deployments")
        print("3. Verify all app features work correctly")
    else:
        print("❌ Migration failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
