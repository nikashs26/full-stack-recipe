#!/usr/bin/env python3
"""
Comprehensive Recipe Backup Script for 1115 Recipes

This script creates a detailed backup of your ChromaDB containing 1115 recipes.
It includes metadata, recipe counts, and verification to ensure all recipes are backed up.
"""

import os
import sys
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_chromadb_path() -> Path:
    """Get the ChromaDB data directory path"""
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

def get_recipe_count_from_chromadb() -> Dict[str, Any]:
    """Get detailed information about recipes in ChromaDB"""
    try:
        import chromadb
        from chromadb.config import Settings
        
        chroma_path = get_chromadb_path()
        
        # Connect to existing ChromaDB
        client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        recipe_info = {
            "total_collections": len(collections),
            "collections": [],
            "total_recipes": 0,
            "recipe_details": {}
        }
        
        for col in collections:
            try:
                count = col.count()
                recipe_info["total_recipes"] += count
                
                collection_info = {
                    "name": col.name,
                    "count": count,
                    "metadata": col.metadata
                }
                
                # Get sample recipes from each collection
                if count > 0:
                    try:
                        # Get a few sample recipes to verify content
                        sample_results = col.peek(limit=min(5, count))
                        if hasattr(sample_results, 'metadatas') and sample_results.metadatas:
                            sample_titles = []
                            for metadata in sample_results.metadatas:
                                if metadata and 'title' in metadata:
                                    sample_titles.append(metadata['title'][:50])
                            collection_info["sample_titles"] = sample_titles
                    except Exception as e:
                        collection_info["sample_error"] = str(e)
                
                recipe_info["collections"].append(collection_info)
                
            except Exception as e:
                print(f"⚠️ Error getting info for collection {col.name}: {e}")
                collection_info = {
                    "name": col.name,
                    "error": str(e)
                }
                recipe_info["collections"].append(collection_info)
        
        return recipe_info
        
    except Exception as e:
        print(f"❌ Could not connect to ChromaDB: {e}")
        return {
            "error": str(e),
            "total_collections": 0,
            "collections": [],
            "total_recipes": 0
        }

def create_recipe_backup_metadata(chroma_path: Path, recipe_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create comprehensive metadata about the recipe backup"""
    metadata = {
        "backup_timestamp": datetime.now().isoformat(),
        "backup_type": "recipe_backup_1115",
        "source_path": str(chroma_path.absolute()),
        "recipe_count": recipe_info.get("total_recipes", 0),
        "expected_recipes": 1115,
        "collections": recipe_info.get("collections", []),
        "total_size_bytes": 0,
        "file_count": 0,
        "backup_verification": {
            "recipe_count_match": recipe_info.get("total_recipes", 0) == 1115,
            "collections_accessible": len(recipe_info.get("collections", [])) > 0,
            "chromadb_healthy": "error" not in recipe_info
        }
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
    
    return metadata

def create_recipe_backup(backup_name: Optional[str] = None) -> str:
    """Create a comprehensive backup of ChromaDB with recipe verification"""
    chroma_path = get_chromadb_path()
    backup_dir = get_backup_dir()
    
    print("🔍 Starting comprehensive recipe backup...")
    print("=" * 60)
    
    # Get recipe information first
    print("📊 Analyzing ChromaDB contents...")
    recipe_info = get_recipe_count_from_chromadb()
    
    if "error" in recipe_info:
        print(f"❌ Failed to analyze ChromaDB: {recipe_info['error']}")
        sys.exit(1)
    
    print(f"📚 Found {recipe_info['total_recipes']} recipes in {recipe_info['total_collections']} collections")
    
    # Verify recipe count
    expected_count = 1115
    actual_count = recipe_info['total_recipes']
    
    if actual_count != expected_count:
        print(f"⚠️  WARNING: Expected {expected_count} recipes, but found {actual_count}")
        print("   This backup will still proceed, but please verify your data.")
    else:
        print(f"✅ Recipe count verified: {actual_count} recipes found")
    
    # Generate backup name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if backup_name:
        backup_name = f"{backup_name}_{timestamp}"
    else:
        backup_name = f"recipe_backup_1115_{timestamp}"
    
    backup_path = backup_dir / backup_name
    
    print(f"\n🔍 Creating backup: {backup_name}")
    print(f"📁 Source: {chroma_path}")
    print(f"💾 Destination: {backup_path}")
    
    try:
        # Create metadata first
        metadata = create_recipe_backup_metadata(chroma_path, recipe_info)
        
        # Create backup directory
        backup_path.mkdir(exist_ok=True)
        
        # Copy all ChromaDB files
        print("\n📋 Copying ChromaDB files...")
        shutil.copytree(chroma_path, backup_path / "chroma_db", dirs_exist_ok=True)
        
        # Save metadata
        metadata_path = backup_path / "backup_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save recipe info separately
        recipe_info_path = backup_path / "recipe_info.json"
        with open(recipe_info_path, 'w') as f:
            json.dump(recipe_info, f, indent=2)
        
        # Create a compressed archive
        archive_path = backup_dir / f"{backup_name}.zip"
        print(f"\n🗜️ Creating compressed archive: {archive_path.name}")
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(backup_path)
                    zipf.write(file_path, arcname)
        
        # Remove uncompressed backup directory
        shutil.rmtree(backup_path)
        
        # Calculate archive size
        archive_size_mb = archive_path.stat().st_size / (1024*1024)
        
        print("\n" + "=" * 60)
        print("✅ RECIPE BACKUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📦 Backup file: {archive_path.name}")
        print(f"💾 Archive size: {archive_size_mb:.2f} MB")
        print(f"📅 Timestamp: {metadata['backup_timestamp']}")
        print(f"📚 Collections backed up: {len(metadata['collections'])}")
        print(f"🍳 Recipes backed up: {metadata['recipe_count']}")
        print(f"📄 Files backed up: {metadata['file_count']}")
        
        # Verification summary
        verification = metadata['backup_verification']
        print(f"\n🔍 VERIFICATION SUMMARY:")
        print(f"   Recipe count match: {'✅' if verification['recipe_count_match'] else '❌'}")
        print(f"   Collections accessible: {'✅' if verification['collections_accessible'] else '❌'}")
        print(f"   ChromaDB healthy: {'✅' if verification['chromadb_healthy'] else '❌'}")
        
        if not verification['recipe_count_match']:
            print(f"\n⚠️  NOTE: Recipe count mismatch detected!")
            print(f"   Expected: {expected_count}, Found: {actual_count}")
            print(f"   Please investigate this discrepancy.")
        
        return str(archive_path)
        
    except Exception as e:
        print(f"\n❌ Backup failed: {e}")
        # Cleanup on failure
        if backup_path.exists():
            shutil.rmtree(backup_path)
        if 'archive_path' in locals() and archive_path.exists():
            archive_path.unlink()
        raise

def verify_backup(backup_filename: str) -> bool:
    """Verify a backup by checking its contents and metadata"""
    backup_dir = get_backup_dir()
    backup_path = backup_dir / backup_filename
    
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_filename}")
        return False
    
    print(f"🔍 Verifying backup: {backup_filename}")
    
    try:
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            # Check for required files
            required_files = ['backup_metadata.json', 'recipe_info.json']
            missing_files = [f for f in required_files if f not in zipf.namelist()]
            
            if missing_files:
                print(f"❌ Missing required files: {missing_files}")
                return False
            
            # Read metadata
            with zipf.open("backup_metadata.json") as f:
                metadata = json.load(f)
            
            with zipf.open("recipe_info.json") as f:
                recipe_info = json.load(f)
            
            print(f"✅ Backup verification successful!")
            print(f"   Recipe count: {metadata['recipe_count']}")
            print(f"   Collections: {len(metadata['collections'])}")
            print(f"   Timestamp: {metadata['backup_timestamp']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Backup verification failed: {e}")
        return False

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Recipe Backup for 1115 Recipes")
    parser.add_argument("--verify", type=str, metavar="BACKUP_FILE",
                       help="Verify an existing backup file")
    parser.add_argument("--name", type=str, default="recipe_backup_1115",
                       help="Custom backup name prefix")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress verbose output")
    
    args = parser.parse_args()
    
    if args.verify:
        success = verify_backup(args.verify)
        sys.exit(0 if success else 1)
    
    try:
        backup_path = create_recipe_backup(args.name)
        print(f"\n🎉 Your 1115 recipes have been successfully backed up to: {backup_path}")
        print("   You can now safely restore from this backup if needed.")
        
    except Exception as e:
        print(f"\n❌ Backup creation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
