#!/usr/bin/env python3
"""
Direct recipe upload to Railway - uploads recipes one by one to ensure exact data structure
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

class DirectRecipeUploader:
    def __init__(self):
        self.railway_url = "https://full-stack-recipe-production.up.railway.app"
        self.api_url = f"{self.railway_url}/api"
        self.recipe_cache = RecipeCacheService()
        
    def upload_recipe_directly(self, recipe_id, metadata, document):
        """Upload a single recipe directly to Railway"""
        try:
            recipe_data = json.loads(document)
            
            # Create the exact structure that matches local
            recipe_payload = {
                "id": recipe_id,
                "metadata": metadata,
                "data": recipe_data
            }
            
            # Upload via a direct endpoint (we'll need to create this)
            response = requests.post(
                f"{self.api_url}/upload-single-recipe",
                json=recipe_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"   Failed to upload {recipe_id}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   Error uploading {recipe_id}: {e}")
            return False
    
    def upload_all_recipes(self):
        """Upload all recipes directly"""
        print("🚀 Starting Direct Recipe Upload")
        print("=" * 50)
        
        # Get all local recipes
        print("📊 Fetching all local recipes...")
        all_recipes = self.recipe_cache.recipe_collection.get(
            include=["documents", "metadatas"],
            limit=None
        )
        
        recipe_count = len(all_recipes['ids'])
        print(f"   Found {recipe_count} local recipes")
        
        # Upload each recipe
        success_count = 0
        failed_count = 0
        
        for i, (recipe_id, metadata, document) in enumerate(zip(
            all_recipes['ids'], 
            all_recipes['metadatas'], 
            all_recipes['documents']
        )):
            try:
                if self.upload_recipe_directly(recipe_id, metadata, document):
                    success_count += 1
                else:
                    failed_count += 1
                
                if (i + 1) % 50 == 0:
                    print(f"   Processed {i + 1}/{recipe_count} recipes... (Success: {success_count}, Failed: {failed_count})")
                    time.sleep(1)  # Small delay to avoid overwhelming Railway
                    
            except Exception as e:
                print(f"   Error processing recipe {recipe_id}: {e}")
                failed_count += 1
                continue
        
        print(f"\n📊 Upload Summary:")
        print(f"   Total recipes: {recipe_count}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {failed_count}")
        
        return success_count > 0

def main():
    uploader = DirectRecipeUploader()
    success = uploader.upload_all_recipes()
    
    if success:
        print("\n✅ Direct upload completed!")
    else:
        print("\n❌ Direct upload failed")

if __name__ == "__main__":
    main()
