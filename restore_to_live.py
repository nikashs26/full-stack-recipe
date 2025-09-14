#!/usr/bin/env python3
"""
Restore recipes to live Render backend
"""

import requests
import json
import time
import os

# Configuration
BACKEND_URL = "https://dietary-delight.onrender.com"
BACKUP_FILE = "complete_railway_sync_data.json"
BATCH_SIZE = 50

def load_backup_data():
    """Load recipe data from backup file"""
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file {BACKUP_FILE} not found")
        return None
    
    print(f"📂 Loading recipes from {BACKUP_FILE}...")
    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different data structures
    if isinstance(data, dict):
        recipes = data.get('recipes', data.get('data', []))
    elif isinstance(data, list):
        recipes = data
    else:
        print("❌ Unknown data format in backup file")
        return None
    
    print(f"📊 Found {len(recipes)} recipes in backup")
    return recipes

def upload_recipe_batch(recipes_batch):
    """Upload a batch of recipes to the backend"""
    try:
        # Use the cache_recipes endpoint instead of admin import
        url = f"{BACKEND_URL}/api/cache_recipes"
        
        payload = {
            "recipes": recipes_batch,
            "query": "restore",
            "ingredient": ""
        }
        
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Batch uploaded successfully: {result}")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading batch: {e}")
        return False

def main():
    """Main restoration function"""
    print("🚀 Starting recipe restoration to live backend...")
    
    # Load backup data
    recipes = load_backup_data()
    if not recipes:
        return
    
    # Get current count
    try:
        count_response = requests.get(f"{BACKEND_URL}/api/recipe-counts", timeout=30)
        if count_response.status_code == 200:
            count_data = count_response.json()
            current_count = count_data.get('data', {}).get('total', 0)
            print(f"📊 Current recipe count: {current_count}")
        else:
            print("⚠️ Could not get current count")
    except Exception as e:
        print(f"⚠️ Error getting current count: {e}")
    
    # Upload in batches
    total_uploaded = 0
    total_batches = (len(recipes) + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"📦 Uploading {len(recipes)} recipes in {total_batches} batches...")
    
    for i in range(0, len(recipes), BATCH_SIZE):
        batch_num = (i // BATCH_SIZE) + 1
        batch = recipes[i:i + BATCH_SIZE]
        
        print(f"🔄 Uploading batch {batch_num}/{total_batches} ({len(batch)} recipes)...")
        
        if upload_recipe_batch(batch):
            total_uploaded += len(batch)
            print(f"✅ Batch {batch_num} completed. Total uploaded: {total_uploaded}")
        else:
            print(f"❌ Batch {batch_num} failed")
        
        # Rate limiting
        time.sleep(2)
    
    # Final count check
    try:
        count_response = requests.get(f"{BACKEND_URL}/api/recipe-counts", timeout=30)
        if count_response.status_code == 200:
            count_data = count_response.json()
            final_count = count_data.get('data', {}).get('total', 0)
            print(f"🎉 Restoration completed! Final count: {final_count}")
        else:
            print(f"📊 Uploaded {total_uploaded} recipes")
    except Exception as e:
        print(f"📊 Uploaded {total_uploaded} recipes (could not verify final count)")

if __name__ == "__main__":
    main()
