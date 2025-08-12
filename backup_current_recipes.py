#!/usr/bin/env python3
"""
Safe backup script for your current 63 recipes
This will create a backup before we do anything else
"""

import json
import chromadb
from datetime import datetime

def backup_current_recipes():
    """Create a safe backup of current recipes"""
    
    print("🔄 Creating backup of current recipes...")
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection("recipe_details_cache")
        
        # Get current recipe count
        current_count = collection.count()
        print(f"📊 Found {current_count} recipes to backup")
        
        if current_count == 0:
            print("❌ No recipes found to backup")
            return
        
        # Get all recipes
        results = collection.get(include=['documents', 'metadatas'])
        
        # Create backup data
        backup_data = {
            "backup_created": datetime.now().isoformat(),
            "total_recipes": current_count,
            "recipes": []
        }
        
        # Process each recipe
        for i, (recipe_id, document, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            try:
                # Parse the document
                if isinstance(document, str):
                    recipe_data = json.loads(document)
                else:
                    recipe_data = document
                
                # Add to backup
                backup_data["recipes"].append({
                    "id": recipe_id,
                    "data": recipe_data,
                    "metadata": metadata
                })
                
                print(f"✅ Backed up recipe {i+1}/{current_count}: {metadata.get('title', 'Unknown')}")
                
            except Exception as e:
                print(f"⚠️  Warning: Could not backup recipe {i+1}: {str(e)}")
        
        # Save backup to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"recipe_backup_{timestamp}_{current_count}_recipes.json"
        
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        print(f"✅ Backup completed successfully!")
        print(f"📁 Backup saved to: {backup_filename}")
        print(f"📊 Total recipes backed up: {len(backup_data['recipes'])}")
        
        return backup_filename
        
    except Exception as e:
        print(f"❌ Error creating backup: {str(e)}")
        return None

if __name__ == "__main__":
    backup_filename = backup_current_recipes()
    if backup_filename:
        print(f"\n🎉 Backup completed! Your recipes are safe in: {backup_filename}")
        print("💡 Now we can safely investigate what went wrong")
    else:
        print("\n❌ Backup failed - please check the error above") 