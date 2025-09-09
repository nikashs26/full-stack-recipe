#!/usr/bin/env python3
"""
Direct recipe upload to Railway
Simple script to upload all local recipes to Railway
"""

import os
import sys
import json
import requests
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

def upload_recipes_to_railway():
    """Upload all local recipes directly to Railway"""
    print("🚀 Direct Recipe Upload to Railway")
    print("=" * 50)
    
    # Initialize local recipe cache
    recipe_cache = RecipeCacheService()
    
    # Get all local recipes
    all_recipes = recipe_cache.recipe_collection.get(include=['metadatas', 'documents'])
    
    if not all_recipes['ids']:
        print("❌ No local recipes found")
        return False
    
    print(f"📊 Found {len(all_recipes['ids'])} local recipes")
    
    # Process and upload recipes in batches
    batch_size = 50
    uploaded_count = 0
    
    for i in range(0, len(all_recipes['ids']), batch_size):
        batch_recipes = []
        
        # Process batch
        for j in range(i, min(i + batch_size, len(all_recipes['ids']))):
            recipe_id = all_recipes['ids'][j]
            metadata = all_recipes['metadatas'][j]
            document = all_recipes['documents'][j]
            
            try:
                recipe_data = json.loads(document)
                batch_recipes.append({
                    'id': recipe_id,
                    'metadata': metadata,
                    'data': recipe_data
                })
            except Exception as e:
                print(f"   ⚠️  Error processing recipe {recipe_id}: {e}")
                continue
        
        # Upload batch to Railway
        print(f"   📤 Uploading batch {i//batch_size + 1} ({len(batch_recipes)} recipes)...")
        
        try:
            # Try to upload via a simple POST endpoint
            response = requests.post(
                "https://full-stack-recipe-production.up.railway.app/api/upload-recipes",
                json={'recipes': batch_recipes},
                timeout=30
            )
            
            if response.status_code == 200:
                uploaded_count += len(batch_recipes)
                print(f"   ✅ Uploaded {len(batch_recipes)} recipes")
            else:
                print(f"   ❌ Upload failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Upload error: {e}")
        
        # Small delay between batches
        time.sleep(1)
    
    print(f"\n📊 Upload Summary:")
    print(f"   Total recipes processed: {len(all_recipes['ids'])}")
    print(f"   Successfully uploaded: {uploaded_count}")
    
    # Verify upload
    print(f"\n🔍 Verifying upload...")
    try:
        response = requests.get("https://full-stack-recipe-production.up.railway.app/api/get_recipes?limit=1")
        if response.status_code == 200:
            data = response.json()
            total_recipes = data.get('total', 0)
            print(f"   📊 Railway now has {total_recipes} recipes")
            
            if total_recipes > 1000:
                print("   🎉 SUCCESS! Railway has all your recipes!")
                return True
            else:
                print("   ⚠️  Upload may not have completed successfully")
                return False
        else:
            print(f"   ❌ Verification failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    upload_recipes_to_railway()
