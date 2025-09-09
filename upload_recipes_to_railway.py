#!/usr/bin/env python3
"""
Upload all local recipes to Railway one by one
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
    """Upload all local recipes to Railway one by one"""
    print("🚀 Uploading Recipes to Railway")
    print("=" * 50)
    
    # Initialize local recipe cache
    recipe_cache = RecipeCacheService()
    
    # Get all local recipes
    all_recipes = recipe_cache.recipe_collection.get(include=['metadatas', 'documents'])
    
    if not all_recipes['ids']:
        print("❌ No local recipes found")
        return False
    
    print(f"📊 Found {len(all_recipes['ids'])} local recipes")
    
    # Prepare sync data
    sync_data = {
        'recipes': [],
        'metadata': {
            'total_recipes': len(all_recipes['ids']),
            'upload_timestamp': time.time(),
            'source': 'local_chromadb'
        }
    }
    
    # Process all recipes
    for i, (recipe_id, metadata, document) in enumerate(zip(all_recipes['ids'], all_recipes['metadatas'], all_recipes['documents'])):
        try:
            recipe_data = json.loads(document)
            
            # Merge metadata into recipe data
            merged_recipe = recipe_data.copy()
            for key, value in metadata.items():
                if key not in merged_recipe or merged_recipe[key] is None or merged_recipe[key] == '':
                    merged_recipe[key] = value
            
            sync_data['recipes'].append({
                'id': recipe_id,
                'metadata': metadata,
                'data': merged_recipe,
                'document': json.dumps(merged_recipe)
            })
            
            if (i + 1) % 100 == 0:
                print(f"   Processed {i + 1}/{len(all_recipes['ids'])} recipes...")
                
        except Exception as e:
            print(f"   ⚠️ Error processing recipe {recipe_id}: {e}")
            continue
    
    print(f"✅ Prepared {len(sync_data['recipes'])} recipes for upload")
    
    # Save sync data to file
    sync_file = 'railway_sync_data.json'
    with open(sync_file, 'w', encoding='utf-8') as f:
        json.dump(sync_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved sync data to {sync_file}")
    
    # Upload to Railway
    print("📤 Uploading to Railway...")
    
    try:
        # Upload the file
        with open(sync_file, 'rb') as f:
            files = {'file': (sync_file, f, 'application/json')}
            response = requests.post(
                "https://full-stack-recipe-production.up.railway.app/api/upload-sync",
                files=files,
                timeout=60
            )
        
        if response.status_code == 200:
            print("✅ File uploaded successfully")
            
            # Trigger population from the uploaded file
            print("🔄 Triggering population...")
            populate_response = requests.post(
                "https://full-stack-recipe-production.up.railway.app/api/populate-from-file",
                timeout=120
            )
            
            if populate_response.status_code == 200:
                result = populate_response.json()
                print(f"✅ Population successful: {result.get('message', 'Unknown result')}")
                
                # Verify the upload
                print("🔍 Verifying upload...")
                verify_response = requests.get(
                    "https://full-stack-recipe-production.up.railway.app/api/get_recipes?limit=1"
                )
                
                if verify_response.status_code == 200:
                    data = verify_response.json()
                    total_recipes = data.get('total', 0)
                    print(f"📊 Railway now has {total_recipes} recipes")
                    
                    if total_recipes > 1000:
                        print("🎉 SUCCESS! Railway has all your recipes!")
                        return True
                    else:
                        print(f"⚠️ Only {total_recipes} recipes found - may need manual intervention")
                        return False
                else:
                    print(f"❌ Verification failed: {verify_response.status_code}")
                    return False
            else:
                print(f"❌ Population failed: {populate_response.status_code} - {populate_response.text}")
                return False
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

if __name__ == "__main__":
    success = upload_recipes_to_railway()
    if success:
        print("\n🎉 Recipe upload completed successfully!")
        print("🌐 Your Netlify site now has all your recipes!")
    else:
        print("\n❌ Recipe upload failed")
        sys.exit(1)
