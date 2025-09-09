#!/usr/bin/env python3
"""
Batch upload recipes to Railway in smaller chunks to ensure all recipes are uploaded
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

class BatchRecipeUploader:
    def __init__(self):
        self.railway_url = "https://full-stack-recipe-production.up.railway.app"
        self.api_url = f"{self.railway_url}/api"
        self.recipe_cache = RecipeCacheService()
        self.batch_size = 50  # Upload 50 recipes at a time
        
    def create_batch_sync_data(self, recipes_batch, batch_num):
        """Create sync data for a batch of recipes"""
        sync_data = {
            "recipes": [],
            "batch_number": batch_num,
            "sync_timestamp": datetime.now().isoformat(),
            "total_recipes": len(recipes_batch)
        }
        
        for recipe_id, metadata, document in recipes_batch:
            try:
                recipe_data = json.loads(document)
                
                recipe_entry = {
                    "id": recipe_id,
                    "metadata": metadata,
                    "data": recipe_data,
                    "source": "local_sync",
                    "sync_timestamp": datetime.now().isoformat()
                }
                
                sync_data['recipes'].append(recipe_entry)
                
            except Exception as e:
                print(f"   Error processing recipe {recipe_id}: {e}")
                continue
        
        return sync_data
    
    def upload_batch(self, batch_data, batch_num):
        """Upload a batch of recipes to Railway"""
        print(f"📤 Uploading batch {batch_num} ({len(batch_data['recipes'])} recipes)...")
        
        # Save batch to file
        batch_file = f"batch_{batch_num}_sync_data.json"
        with open(batch_file, 'w') as f:
            json.dump(batch_data, f, indent=2)
        
        try:
            # Upload to Railway
            with open(batch_file, 'rb') as f:
                files = {'file': (batch_file, f, 'application/json')}
                response = requests.post(f"{self.api_url}/upload-sync", files=files, timeout=120)
            
            if response.status_code == 200:
                print(f"✅ Batch {batch_num} uploaded successfully")
                
                # Trigger population for this batch
                populate_response = requests.post(f"{self.api_url}/populate-from-file", timeout=60)
                if populate_response.status_code in [200, 202]:
                    print(f"✅ Batch {batch_num} population triggered")
                    return True
                else:
                    print(f"⚠️ Batch {batch_num} population failed: {populate_response.status_code}")
                    return False
            else:
                print(f"❌ Batch {batch_num} upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Batch {batch_num} error: {e}")
            return False
        finally:
            # Clean up batch file
            if os.path.exists(batch_file):
                os.remove(batch_file)
    
    def upload_all_recipes_in_batches(self):
        """Upload all recipes in batches"""
        print("🚀 Starting Batch Recipe Upload")
        print("=" * 50)
        
        # Get all local recipes
        print("📊 Fetching all local recipes...")
        all_recipes = self.recipe_cache.recipe_collection.get(
            include=["documents", "metadatas"],
            limit=None
        )
        
        recipe_count = len(all_recipes['ids'])
        print(f"   Found {recipe_count} local recipes")
        
        # Split into batches
        batches = []
        for i in range(0, recipe_count, self.batch_size):
            batch_recipes = list(zip(
                all_recipes['ids'][i:i + self.batch_size],
                all_recipes['metadatas'][i:i + self.batch_size],
                all_recipes['documents'][i:i + self.batch_size]
            ))
            batches.append(batch_recipes)
        
        print(f"   Created {len(batches)} batches of {self.batch_size} recipes each")
        
        # Upload each batch
        successful_batches = 0
        failed_batches = 0
        
        for batch_num, batch_recipes in enumerate(batches, 1):
            print(f"\n--- Processing Batch {batch_num}/{len(batches)} ---")
            
            # Create batch sync data
            batch_data = self.create_batch_sync_data(batch_recipes, batch_num)
            
            # Upload batch
            if self.upload_batch(batch_data, batch_num):
                successful_batches += 1
            else:
                failed_batches += 1
            
            # Wait between batches to avoid overwhelming Railway
            if batch_num < len(batches):
                print("   Waiting 10 seconds before next batch...")
                time.sleep(10)
        
        print(f"\n📊 Batch Upload Summary:")
        print(f"   Total batches: {len(batches)}")
        print(f"   Successful: {successful_batches}")
        print(f"   Failed: {failed_batches}")
        
        return successful_batches > 0
    
    def verify_upload(self):
        """Verify that all recipes were uploaded"""
        print("\n🔍 Verifying upload...")
        
        try:
            response = requests.get(f"{self.api_url}/debug-recipes", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                recipe_count = data.get('recipe_collection_count', 0)
                print(f"✅ Railway now has {recipe_count} recipes")
                
                if recipe_count >= 1000:
                    print("🎉 Success! Most recipes have been uploaded")
                    return True
                else:
                    print(f"⚠️ Only {recipe_count} recipes uploaded, expected ~1115")
                    return False
            else:
                print(f"❌ Verification failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False

def main():
    uploader = BatchRecipeUploader()
    
    # Upload all recipes in batches
    success = uploader.upload_all_recipes_in_batches()
    
    if success:
        # Verify upload
        uploader.verify_upload()
        print("\n✅ Batch upload completed!")
        print("🌐 Your Netlify app should now have all recipes")
    else:
        print("\n❌ Batch upload failed")

if __name__ == "__main__":
    main()
