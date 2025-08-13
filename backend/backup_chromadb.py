#!/usr/bin/env python3
"""
ChromaDB Backup and Restore Script

This script provides comprehensive backup and restore functionality for your ChromaDB.
It creates timestamped backups with metadata and allows you to restore from any backup.
"""

import os
import sys
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import zipfile

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_chromadb_path() -> Path:
    """Get the ChromaDB data directory path"""
    # Default ChromaDB path in the backend directory
    chroma_path = Path(__file__).parent / "chroma_db"
    
    if not chroma_path.exists():
        print(f"❌ ChromaDB directory not found at: {chroma_path}")
        print("Please ensure ChromaDB is properly initialized.")
        sys.exit(1)
    
    return chroma_path

def get_backup_dir() -> Path:
    """Get or create the backup directory"""
    backup_dir = Path(__file__).parent / "chromadb_backups"
    backup_dir.mkdir(exist_ok=True)
    return backup_dir

def create_backup_metadata(chroma_path: Path) -> Dict[str, Any]:
    """Create metadata about the current ChromaDB state"""
    metadata = {
        "backup_timestamp": datetime.now().isoformat(),
        "chromadb_version": "unknown",  # Could be enhanced to detect actual version
        "backup_type": "full",
        "source_path": str(chroma_path.absolute()),
        "collections": [],
        "total_size_bytes": 0,
        "file_count": 0
    }
    
    # Count files and calculate size
    total_size = 0
    file_count = 0
    
    for root, dirs, files in os.walk(chroma_path):
        for file in files:
            file_path = Path(root) / file
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
    
    metadata["total_size_bytes"] = total_size
    metadata["file_count"] = file_count
    
    # Try to get collection info from ChromaDB
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Connect to existing ChromaDB
        client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        metadata["collections"] = [
            {
                "name": col.name,
                "count": col.count(),
                "metadata": col.metadata
            }
            for col in collections
        ]
        
    except Exception as e:
        print(f"⚠️ Could not get collection info: {e}")
        metadata["collections"] = []
    
    return metadata

def create_backup(backup_name: Optional[str] = None) -> str:
    """Create a full backup of ChromaDB"""
    chroma_path = get_chromadb_path()
    backup_dir = get_backup_dir()
    
    # Generate backup name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if backup_name:
        backup_name = f"{backup_name}_{timestamp}"
    else:
        backup_name = f"chromadb_backup_{timestamp}"
    
    backup_path = backup_dir / backup_name
    
    print(f"🔍 Creating backup: {backup_name}")
    print(f"📁 Source: {chroma_path}")
    print(f"💾 Destination: {backup_path}")
    
    try:
        # Create metadata first
        metadata = create_backup_metadata(chroma_path)
        
        # Create backup directory
        backup_path.mkdir(exist_ok=True)
        
        # Copy all ChromaDB files
        print("📋 Copying ChromaDB files...")
        shutil.copytree(chroma_path, backup_path / "chroma_db", dirs_exist_ok=True)
        
        # Save metadata
        metadata_path = backup_path / "backup_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create a compressed archive
        archive_path = backup_dir / f"{backup_name}.zip"
        print(f"🗜️ Creating compressed archive: {archive_path.name}")
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(backup_path)
                    zipf.write(file_path, arcname)
        
        # Remove uncompressed backup directory
        shutil.rmtree(backup_path)
        
        print(f"✅ Backup created successfully: {archive_path.name}")
        print(f"📊 Backup size: {archive_path.stat().st_size / (1024*1024):.2f} MB")
        print(f"📅 Timestamp: {metadata['backup_timestamp']}")
        print(f"📁 Collections: {len(metadata['collections'])}")
        print(f"📄 Files backed up: {metadata['file_count']}")
        
        return str(archive_path)
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        # Cleanup on failure
        if backup_path.exists():
            shutil.rmtree(backup_path)
        if 'archive_path' in locals() and archive_path.exists():
            archive_path.unlink()
        raise

def list_backups() -> List[Dict[str, Any]]:
    """List all available backups with metadata"""
    backup_dir = get_backup_dir()
    backups = []
    
    for backup_file in backup_dir.glob("*.zip"):
        try:
            # Extract metadata from zip
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                try:
                    with zipf.open("backup_metadata.json") as f:
                        metadata = json.load(f)
                        backups.append({
                            "filename": backup_file.name,
                            "path": str(backup_file),
                            "size_bytes": backup_file.stat().st_size,
                            "metadata": metadata
                        })
                except:
                    # Fallback if metadata not found
                    backups.append({
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "size_bytes": backup_file.stat().st_size,
                        "metadata": {
                            "backup_timestamp": "unknown",
                            "collections": [],
                            "file_count": 0
                        }
                    })
        except Exception as e:
            print(f"⚠️ Could not read backup {backup_file.name}: {e}")
    
    # Sort by timestamp (newest first)
    backups.sort(key=lambda x: x["metadata"].get("backup_timestamp", ""), reverse=True)
    return backups

def restore_backup(backup_filename: str, force: bool = False) -> bool:
    """Restore ChromaDB from a backup"""
    backup_dir = get_backup_dir()
    backup_path = backup_dir / backup_filename
    
    if not backup_path.exists():
        print(f"❌ Backup not found: {backup_filename}")
        return False
    
    chroma_path = get_chromadb_path()
    
    print(f"🔄 Restoring from backup: {backup_filename}")
    print(f"📁 Source: {backup_path}")
    print(f"💾 Destination: {chroma_path}")
    
    if not force:
        # Check if ChromaDB is currently in use
        try:
            import chromadb
            from chromadb.config import Settings
            
            client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Try to list collections to see if it's active
            collections = client.list_collections()
            if collections:
                print("⚠️ ChromaDB appears to be in use with collections:")
                for col in collections:
                    print(f"   - {col.name} ({col.count()} items)")
                
                response = input("Do you want to continue with the restore? This will overwrite current data. (y/N): ")
                if response.lower() != 'y':
                    print("❌ Restore cancelled")
                    return False
        except Exception as e:
            print(f"⚠️ Could not check ChromaDB status: {e}")
    
    try:
        # Create a temporary directory for extraction
        temp_dir = backup_dir / f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_dir.mkdir(exist_ok=True)
        
        print("📋 Extracting backup...")
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        # Find the chroma_db directory in the extracted backup
        extracted_chroma = None
        for item in temp_dir.iterdir():
            if item.is_dir() and item.name == "chroma_db":
                extracted_chroma = item
                break
        
        if not extracted_chroma:
            print("❌ Could not find chroma_db directory in backup")
            shutil.rmtree(temp_dir)
            return False
        
        # Backup current ChromaDB if it exists
        if chroma_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = backup_dir / f"pre_restore_backup_{timestamp}"
            print(f"💾 Backing up current ChromaDB to: {current_backup.name}")
            shutil.copytree(chroma_path, current_backup)
        
        # Remove current ChromaDB
        if chroma_path.exists():
            shutil.rmtree(chroma_path)
        
        # Restore from backup
        print("🔄 Restoring ChromaDB files...")
        shutil.copytree(extracted_chroma, chroma_path)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        
        print("✅ Restore completed successfully!")
        
        # Show restored metadata
        try:
            metadata_file = temp_dir / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    print(f"📅 Restored from backup created: {metadata.get('backup_timestamp', 'unknown')}")
                    print(f"📁 Collections: {len(metadata.get('collections', []))}")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

def show_backup_info(backup_filename: str):
    """Show detailed information about a specific backup"""
    backup_dir = get_backup_dir()
    backup_path = backup_dir / backup_filename
    
    if not backup_path.exists():
        print(f"❌ Backup not found: {backup_filename}")
        return
    
    try:
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            try:
                with zipf.open("backup_metadata.json") as f:
                    metadata = json.load(f)
                    
                    print(f"\n📊 Backup Information: {backup_filename}")
                    print("=" * 50)
                    print(f"📅 Created: {metadata.get('backup_timestamp', 'unknown')}")
                    print(f"📁 Collections: {len(metadata.get('collections', []))}")
                    print(f"📄 Files: {metadata.get('file_count', 0)}")
                    print(f"💾 Size: {metadata.get('total_size_bytes', 0) / (1024*1024):.2f} MB")
                    
                    if metadata.get('collections'):
                        print(f"\n📚 Collections:")
                        for col in metadata['collections']:
                            print(f"   - {col.get('name', 'unknown')}: {col.get('count', 0)} items")
                    
            except:
                print(f"⚠️ Could not read metadata from {backup_filename}")
                
    except Exception as e:
        print(f"❌ Error reading backup: {e}")

def main():
    """Main function with interactive menu"""
    print("🔒 ChromaDB Backup & Restore Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Create backup")
        print("2. List backups")
        print("3. Show backup info")
        print("4. Restore backup")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == "1":
            backup_name = input("Enter backup name (optional, press Enter for timestamped name): ").strip()
            if not backup_name:
                backup_name = None
            
            try:
                backup_path = create_backup(backup_name)
                print(f"\n✅ Backup created: {backup_path}")
            except Exception as e:
                print(f"\n❌ Backup failed: {e}")
        
        elif choice == "2":
            backups = list_backups()
            if not backups:
                print("\n📭 No backups found")
            else:
                print(f"\n📚 Found {len(backups)} backups:")
                for i, backup in enumerate(backups, 1):
                    size_mb = backup["size_bytes"] / (1024*1024)
                    timestamp = backup["metadata"].get("backup_timestamp", "unknown")
                    collections = len(backup["metadata"].get("collections", []))
                    print(f"{i}. {backup['filename']}")
                    print(f"   📅 {timestamp}")
                    print(f"   📁 {collections} collections")
                    print(f"   💾 {size_mb:.2f} MB")
                    print()
        
        elif choice == "3":
            backups = list_backups()
            if not backups:
                print("\n📭 No backups found")
            else:
                print("\nAvailable backups:")
                for i, backup in enumerate(backups, 1):
                    print(f"{i}. {backup['filename']}")
                
                try:
                    backup_num = int(input("Enter backup number: ")) - 1
                    if 0 <= backup_num < len(backups):
                        show_backup_info(backups[backup_num]["filename"])
                    else:
                        print("❌ Invalid backup number")
                except ValueError:
                    print("❌ Please enter a valid number")
        
        elif choice == "4":
            backups = list_backups()
            if not backups:
                print("\n📭 No backups found")
            else:
                print("\nAvailable backups:")
                for i, backup in enumerate(backups, 1):
                    print(f"{i}. {backup['filename']}")
                
                try:
                    backup_num = int(input("Enter backup number: ")) - 1
                    if 0 <= backup_num < len(backups):
                        force = input("Force restore (overwrites current data)? (y/N): ").lower() == 'y'
                        restore_backup(backups[backup_num]["filename"], force)
                    else:
                        print("❌ Invalid backup number")
                except ValueError:
                    print("❌ Please enter a valid number")
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please select 1-5.")

if __name__ == "__main__":
    main() 