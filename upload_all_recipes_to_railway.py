#!/usr/bin/env python3
"""
Upload all local recipes to Railway backend
This script will extract all recipes from local ChromaDB and upload them to Railway
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

class RecipeUploader:
    def __init__(self, railway_url: str = "https://full-stack-recipe-production.up.railway.app"):
        self.railway_url = railway_url.rstrip('/')
        self.api_url = f"{self.railway_url}/api"
        
        # Local services
        self.local_recipe_cache = RecipeCacheService()
        
        print(f"🚀 Recipe Uploader initialized")
        print(f"   Railway URL: {self.railway_url}")
        print(f"   API URL: {self.api_url}")
    
    def get_all_local_recipes(self):
        """Get all recipes from local ChromaDB"""
        try:
            print("📊 Fetching all recipes from local ChromaDB...")
            
            # Get all recipes from local cache
            all_recipes = self.local_recipe_cache.recipe_collection.get(
                include=['metadatas', 'documents']
            )
            
            recipe_count = len(all_recipes['ids'])
            print(f"   Found {recipe_count} recipes locally")
            
            # Process recipes
            processed_recipes = []
            for i, (recipe_id, metadata, document) in enumerate(zip(
                all_recipes['ids'], 
                all_recipes['metadatas'], 
                all_recipes['documents']
            )):
                try:
                    # Parse the document (should be JSON)
                    recipe_data = json.loads(document)
                    
                    # Ensure we have all required fields
                    processed_recipe = {
                        'id': recipe_id,
                        'title': recipe_data.get('title', 'Unknown Recipe'),
                        'cuisine': recipe_data.get('cuisine', 'unknown'),
                        'cuisines': recipe_data.get('cuisines', [recipe_data.get('cuisine', 'unknown')]),
                        'diets': recipe_data.get('diets', []),
                        'ingredients': recipe_data.get('ingredients', []),
                        'instructions': recipe_data.get('instructions', []),
                        'calories': recipe_data.get('calories', 0),
                        'protein': recipe_data.get('protein', 0),
                        'carbs': recipe_data.get('carbs', 0),
                        'fat': recipe_data.get('fat', 0),
                        'image': recipe_data.get('image', ''),
                        'description': recipe_data.get('description', ''),
                        'metadata': metadata
                    }
                    
                    processed_recipes.append(processed_recipe)
                    
                    if (i + 1) % 100 == 0:
                        print(f"   Processed {i + 1}/{recipe_count} recipes...")
                        
                except Exception as e:
                    print(f"   ⚠️  Error processing recipe {recipe_id}: {e}")
                    continue
            
       
            return processed_recipes
            
        except Exception as e:
            print(f"   ❌ Error fetching local recipes: {e}")
            return []
    
    def upload_recipes_batch(self, recipes, batch_size=50):
        """Upload recipes in batches to Railway"""
        total_recipes = len(recipes)
        uploaded_count = 0
        failed_count = 0
        
        print(f"📤 Uploading {total_recipes} recipes to Railway in batches of {batch_size}...")
        
        for i in range(0, total_recipes, batch_size):
            batch = recipes[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_recipes + batch_size - 1) // batch_size
            
            print(f"   📦 Uploading batch {batch_num}/{total_batches} ({len(batch)} recipes)...")
            
            try:
                # Create upload data
                upload_data = {
                    'recipes': batch,
                    'batch_info': {
                        'batch_number': batch_num,
                        'total_batches': total_batches,
                        'total_recipes': total_recipes
                    }
                }
                
                # Upload to Railway
                response = requests.post(
                    f"{self.api_url}/upload-recipes",
                    json=upload_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    batch_uploaded = result.get('uploaded_count', len(batch))
                    uploaded_count += batch_uploaded
                    print(f"   ✅ Batch {batch_num} uploaded successfully ({batch_uploaded} recipes)")
                else:
                    print(f"   ❌ Batch {batch_num} failed: {response.status_code} - {response.text}")
                    failed_count += len(batch)
                
                # Small delay between batches
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error uploading batch {batch_num}: {e}")
                failed_count += len(batch)
        
        return uploaded_count, failed_count
    
    def upload_recipes_simple(self, recipes):
        """Upload recipes one by one using simple endpoint"""
        total_recipes = len(recipes)
        uploaded_count = 0
        failed_count = 0
        
        print(f"📤 Uploading {total_recipes} recipes to Railway one by one...")
        
        for i, recipe in enumerate(recipes):
            try:
                # Try to upload individual recipe
                response = requests.post(
                    f"{self.api_url}/add-recipe",
                    json=recipe,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    uploaded_count += 1
                    if (i + 1) % 50 == 0:
                        print(f"   ✅ Uploaded {i + 1}/{total_recipes} recipes...")
                else:
                    print(f"   ❌ Failed to upload recipe {i + 1}: {response.status_code}")
                    failed_count += 1
                
                # Small delay between uploads
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   ❌ Error uploading recipe {i + 1}: {e}")
                failed_count += 1
        
        return uploaded_count, failed_count
    
    def run_upload(self):
        """Run the complete upload process"""
        print("🚀 Starting Recipe Upload to Railway")
        print("=" * 60)
        
        # Step 1: Get all local recipes
        print("\n1️⃣ Fetching local recipes...")
        local_recipes = self.get_all_local_recipes()
        
        if not local_recipes:
            print("   ❌ No recipes found locally. Exiting.")
            return False
        
        print(f"   ✅ Found {len(local_recipes)} recipes to upload")
        
        # Step 2: Check Railway status
        print("\n2️⃣ Checking Railway status...")
        try:
            health_response = requests.get(f"{self.api_url}/health", timeout=10)
            if health_response.status_code != 200:
                print("   ❌ Railway backend not accessible")
                return False
            print("   ✅ Railway backend is accessible")
        except Exception as e:
            print(f"   ❌ Cannot connect to Railway: {e}")
            return False
        
        # Step 3: Upload recipes
        print("\n3️⃣ Uploading recipes...")
        
        # Try batch upload first, fallback to individual uploads
        uploaded_count, failed_count = self.upload_recipes_batch(local_recipes)
        
        if uploaded_count == 0 and failed_count > 0:
            print("   ⚠️  Batch upload failed, trying individual uploads...")
            uploaded_count, failed_count = self.upload_recipes_simple(local_recipes)
        
        # Step 4: Verify upload
        print("\n4️⃣ Verifying upload...")
        try:
            verify_response = requests.get(f"{self.api_url}/get_recipes?limit=1", timeout=10)
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                total_on_railway = verify_data.get('total', 0)
                print(f"   📊 Total recipes on Railway: {total_on_railway}")
            else:
                print("   ⚠️  Could not verify upload")
        except Exception as e:
            print(f"   ⚠️  Error verifying upload: {e}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("📊 UPLOAD SUMMARY")
        print(f"   Recipes to upload: {len(local_recipes)}")
        print(f"   Successfully uploaded: {uploaded_count}")
        print(f"   Failed uploads: {failed_count}")
        print(f"   Success rate: {(uploaded_count / len(local_recipes) * 100):.1f}%")
        
        if uploaded_count > 0:
            print(f"\n🎉 SUCCESS! {uploaded_count} recipes uploaded to Railway!")
            print(f"🌐 Your app is live at: {self.railway_url}")
            return True
        else:
            print("\n❌ No recipes were uploaded successfully")
            return False

def main():
    """Main function"""
    uploader = RecipeUploader()
    uploader.run_upload()

if __name__ == "__main__":
    main()
