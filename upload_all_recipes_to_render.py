#!/usr/bin/env python3
"""
Upload all recipes from backup to the deployed Render database
This will restore the full recipe dataset to the live site
"""

import json
import requests
import os
from pathlib import Path

def upload_recipes_to_render():
    """Upload all recipes from backup to Render database"""
    
    # Load the backup file
    backup_file = "production_recipes_backup.json"
    if not os.path.exists(backup_file):
        print(f"❌ Backup file {backup_file} not found")
        return False
    
    print(f"📂 Loading recipes from {backup_file}...")
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        recipes = backup_data.get('recipes', [])
        print(f"📊 Found {len(recipes)} recipes in backup")
        
        # Upload recipes in batches
        batch_size = 100
        total_uploaded = 0
        base_url = "https://dietary-delight.onrender.com"
        admin_token = "390a77929dbe4a50705a8d8cd2888678"
        
        print(f"📤 Uploading recipes to {base_url}...")
        
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            
            # Prepare the batch for upload
            upload_data = {
                "action": "upload_complete_recipes",
                "recipes": batch,
                "preserve_format": True
            }
            
            try:
                response = requests.post(
                    f"{base_url}/api/admin/migrate",
                    json=upload_data,
                    headers={
                        "Content-Type": "application/json",
                        "X-Admin-Token": admin_token
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    uploaded_count = result.get('uploaded', 0)
                    total_uploaded += uploaded_count
                    print(f"✅ Batch {i//batch_size + 1}: Uploaded {uploaded_count} recipes (Total: {total_uploaded})")
                else:
                    print(f"❌ Batch {i//batch_size + 1} failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Error uploading batch {i//batch_size + 1}: {e}")
                continue
        
        print(f"🎉 Successfully uploaded {total_uploaded} recipes!")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading recipes: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting recipe upload to Render...")
    success = upload_recipes_to_render()
    if success:
        print("✅ Recipe upload completed successfully!")
    else:
        print("❌ Recipe upload failed!")