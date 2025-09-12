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
    
    # Prefer assistant recipes if present
    backup_file = "assistant_recipes_200.json"
    if not os.path.exists(backup_file):
        # Fallback to production backup structure
        backup_file = "production_recipes_backup.json"
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found")
            return False
    
    print(f"📂 Loading recipes from {backup_file}...")
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        recipes = data.get('recipes', data if isinstance(data, list) else [])
        print(f"📊 Found {len(recipes)} recipes in backup")
        
        # Upload recipes in batches
        batch_size = 100
        total_uploaded = 0
        base_url = "https://dietary-delight.onrender.com"
        admin_token = os.getenv("ADMIN_TOKEN", "390a77929dbe4a50705a8d8cd2888678")
        
        print(f"📤 Uploading recipes to {base_url}...")
        
        # Try bulk admin migrate first
        used_admin_endpoint = False
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            upload_data = {
                "action": "upload_complete_recipes",
                "recipes": batch,
                "preserve_format": True
            }
            try:
                resp = requests.post(
                    f"{base_url}/api/admin/migrate",
                    json=upload_data,
                    headers={
                        "Content-Type": "application/json",
                        "X-Admin-Token": admin_token
                    },
                    timeout=60
                )
                if resp.status_code == 200 and resp.headers.get('content-type','').startswith('application/json'):
                    result = resp.json()
                    uploaded_count = result.get('uploaded', 0)
                    total_uploaded += uploaded_count
                    used_admin_endpoint = True
                    print(f"✅ Batch {i//batch_size + 1}: Uploaded {uploaded_count} recipes (Total: {total_uploaded})")
                else:
                    print(f"ℹ️ Admin migrate not available or failed (status {resp.status_code}). Falling back to per-item create.")
                    used_admin_endpoint = False
                    break
            except Exception as e:
                print(f"ℹ️ Admin migrate error: {e}. Falling back to per-item create.")
                used_admin_endpoint = False
                break
        
        # Fallback: create via public create endpoint
        if not used_admin_endpoint:
            created = 0
            for idx, r in enumerate(recipes, 1):
                payload = {
                    "title": r.get("title", "Untitled Recipe"),
                    "summary": r.get("description", ""),
                    "readyInMinutes": r.get("readyInMinutes", 30),
                    "cuisines": r.get("cuisines", []),
                    "diets": r.get("diets", []),
                    "image": r.get("image", ""),
                    "ingredients": r.get("ingredients", []),
                    "instructions": r.get("instructions", [])
                }
                try:
                    resp = requests.post(
                        f"{base_url}/api/recipes",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=20
                    )
                    if resp.status_code in (200, 201):
                        created += 1
                        if created % 25 == 0:
                            print(f"✅ Created {created} recipes...")
                    else:
                        print(f"❌ Failed to create recipe {idx}: {resp.status_code}")
                except Exception as e:
                    print(f"❌ Error creating recipe {idx}: {e}")
            total_uploaded = created
        
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