#!/usr/bin/env python3
"""
Comprehensive backup script for ChromaDB recipe data
Creates both a full directory backup and a JSON data backup
"""

import os
import shutil
import json
import chromadb
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_backup_folder():
    """Create a timestamped backup folder"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = f"chroma_db_backup_{timestamp}"
    
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
        logger.info(f"✅ Created backup folder: {backup_folder}")
    else:
        logger.warning(f"⚠️  Backup folder already exists: {backup_folder}")
    
    return backup_folder

def backup_chromadb_directory(backup_folder):
    """Backup the entire ChromaDB directory"""
    source_dir = "./chroma_db"
    
    if not os.path.exists(source_dir):
        logger.error(f"❌ Source directory not found: {source_dir}")
        return False
    
    try:
        # Copy the entire ChromaDB directory
        backup_path = os.path.join(backup_folder, "chroma_db")
        shutil.copytree(source_dir, backup_path)
        logger.info(f"✅ Successfully backed up ChromaDB directory to: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error backing up ChromaDB directory: {e}")
        return False

def backup_recipe_data_json(backup_folder):
    """Backup recipe data as JSON for extra safety"""
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # Try to get the recipe collection
        try:
            collection = client.get_collection("recipe_details_cache")
            logger.info("✅ Found recipe_details_cache collection")
        except Exception as e:
            try:
                collection = client.get_collection("recipe_search_cache")
                logger.info("✅ Found recipe_search_cache collection")
            except Exception as e2:
                logger.error(f"❌ Could not find recipe collection: {e2}")
                return False
        
        # Get all recipes
        results = collection.get()
        
        if not results or not results.get('documents'):
            logger.warning("⚠️  No recipes found in collection")
            return False
        
        recipes = []
        for i, doc in enumerate(results['documents']):
            try:
                # Parse the JSON document
                recipe = json.loads(doc)
                recipes.append(recipe)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"⚠️  Error parsing recipe {i}: {e}")
                continue
        
        logger.info(f"📊 Found {len(recipes)} recipes to backup")
        
        # Save to JSON file
        json_backup_path = os.path.join(backup_folder, "recipes_backup.json")
        with open(json_backup_path, 'w', encoding='utf-8') as f:
            json.dump(recipes, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Successfully backed up {len(recipes)} recipes to: {json_backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error backing up recipe data: {e}")
        return False

def get_backup_summary(backup_folder):
    """Get summary of backup contents"""
    try:
        # Get backup size
        total_size = 0
        file_count = 0
        
        for dirpath, dirnames, filenames in os.walk(backup_folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
                file_count += 1
        
        # Convert to human readable format
        if total_size > 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024):.2f} MB"
        else:
            size_str = f"{total_size / 1024:.2f} KB"
        
        logger.info(f"📊 Backup Summary:")
        logger.info(f"   - Backup location: {backup_folder}")
        logger.info(f"   - Total files: {file_count}")
        logger.info(f"   - Total size: {size_str}")
        
        return {
            "backup_folder": backup_folder,
            "file_count": file_count,
            "total_size": total_size
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting backup summary: {e}")
        return None

def main():
    """Main backup function"""
    logger.info("🔄 Starting ChromaDB backup process...")
    
    # Create backup folder
    backup_folder = create_backup_folder()
    
    # Backup ChromaDB directory
    chroma_backup_success = backup_chromadb_directory(backup_folder)
    
    # Backup recipe data as JSON
    json_backup_success = backup_recipe_data_json(backup_folder)
    
    # Get backup summary
    summary = get_backup_summary(backup_folder)
    
    # Final status
    logger.info("\n" + "="*50)
    logger.info("📋 BACKUP COMPLETE")
    logger.info("="*50)
    
    if chroma_backup_success:
        logger.info("✅ ChromaDB directory backup: SUCCESS")
    else:
        logger.error("❌ ChromaDB directory backup: FAILED")
    
    if json_backup_success:
        logger.info("✅ Recipe data JSON backup: SUCCESS")
    else:
        logger.warning("⚠️  Recipe data JSON backup: FAILED")
    
    if summary:
        logger.info(f"📁 Backup location: {summary['backup_folder']}")
        logger.info(f"📊 Files backed up: {summary['file_count']}")
    
    if chroma_backup_success:
        logger.info("\n🎉 Backup completed successfully!")
        logger.info("💡 You can now safely run the recipe import script")
        logger.info(f"📁 Your backup is stored in: {backup_folder}")
    else:
        logger.error("\n❌ Backup failed! Please check the errors above")
        logger.error("⚠️  Do not proceed with import until backup is successful")

if __name__ == "__main__":
    main() 