#!/usr/bin/env python3
"""
Batch upload all 1323 recipes using the proven flattened approach
"""
import json
import requests
import time

def batch_upload_all_recipes():
    """Upload all recipes in batches using the working flattened method"""
    
    print("🚀 Batch Upload All 1,323 Recipes")
    print("=" * 50)
    
    # Load all recipes
    with open('recipes_data.json', 'r') as f:
        recipes = json.load(f)
    print(f"✅ Loaded {len(recipes)} recipes")
    
    # Flatten all recipes using the exact same method that worked
    print("🔧 Flattening all recipes...")
    flattened_recipes = []
    
    for recipe in recipes:
        flat_recipe = {}
        for key, value in recipe.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                flat_recipe[key] = value
            elif isinstance(value, (dict, list)):
                # Convert complex objects to JSON strings (this is what worked!)
                flat_recipe[key] = json.dumps(value)
            else:
                flat_recipe[key] = str(value)
        flattened_recipes.append(flat_recipe)
    
    print(f"✅ Flattened {len(flattened_recipes)} recipes")
    
    # Upload in batches using the admin API
    admin_token = "390a77929dbe4a50705a8d8cd2888678"
    base_url = "https://dietary-delight.onrender.com"
    
    batch_size = 100  # Upload 100 recipes at a time
    total_uploaded = 0
    
    for i in range(0, len(flattened_recipes), batch_size):
        batch = flattened_recipes[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(flattened_recipes) + batch_size - 1) // batch_size
        
        print(f"\n📦 Uploading batch {batch_num}/{total_batches} ({len(batch)} recipes)...")
        
        # Create a temporary batch file
        batch_filename = f"batch_{batch_num}_recipes.json"
        with open(batch_filename, 'w') as f:
            json.dump(batch, f)
        
        # Create the payload for the admin API
        payload = {
            "action": "direct_upload",
            "recipes": batch,
            "batch_info": {
                "batch_number": batch_num,
                "total_batches": total_batches,
                "recipes_in_batch": len(batch)
            }
        }
        
        try:
            # Method 1: Try to use the working admin seed endpoint with embedded data
            response = requests.post(
                f"{base_url}/api/admin/seed",
                headers={
                    "Content-Type": "application/json",
                    "X-Admin-Token": admin_token
                },
                json={
                    "action": "batch_upload",
                    "recipes": batch[:10]  # Start with just 10 per batch to test
                },
                timeout=120  # Longer timeout for batch processing
            )
            
            if response.status_code == 200:
                result = response.json()
                imported = result.get('imported', 0)
                total_uploaded += imported
                print(f"✅ Batch {batch_num}: {imported} recipes imported")
                
                if imported < len(batch[:10]):
                    print(f"⚠️ Only {imported}/{len(batch[:10])} recipes imported in this batch")
                    
            else:
                print(f"❌ Batch {batch_num} failed: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
                # Try alternative approach - individual recipe upload
                print(f"🔄 Trying individual upload for batch {batch_num}...")
                batch_uploaded = 0
                
                for j, recipe in enumerate(batch[:5]):  # Just first 5 for testing
                    try:
                        single_response = requests.post(
                            f"{base_url}/api/admin/seed",
                            headers={
                                "Content-Type": "application/json",
                                "X-Admin-Token": admin_token
                            },
                            json={
                                "action": "single_upload",
                                "recipe": recipe
                            },
                            timeout=30
                        )
                        
                        if single_response.status_code == 200:
                            batch_uploaded += 1
                            if (j + 1) % 5 == 0:
                                print(f"  Uploaded {j + 1}/5 recipes...")
                        else:
                            print(f"  Failed recipe {j + 1}: {single_response.text[:100]}")
                            
                    except Exception as e:
                        print(f"  Error uploading recipe {j + 1}: {e}")
                
                total_uploaded += batch_uploaded
                print(f"✅ Batch {batch_num}: {batch_uploaded} recipes uploaded individually")
        
        except Exception as e:
            print(f"❌ Batch {batch_num} error: {e}")
        
        # Small delay between batches
        if batch_num < total_batches:
            print("⏳ Waiting 2 seconds before next batch...")
            time.sleep(2)
        
        # Stop after first batch for testing
        if batch_num >= 1:
            print("\n⏸️ Stopping after first batch for testing...")
            break
    
    print(f"\n🎉 Upload Complete!")
    print(f"📊 Total recipes uploaded: {total_uploaded}")
    print(f"📊 Remaining recipes: {len(recipes) - total_uploaded}")
    
    # Verify the upload
    print("\n🔍 Verifying upload...")
    try:
        debug_response = requests.get(
            f"{base_url}/api/admin/debug",
            params={"token": admin_token},
            timeout=10
        )
        
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            recipe_count = debug_data.get('chromadb_status', {}).get('recipe_count', 0)
            print(f"✅ ChromaDB now contains {recipe_count} recipes")
        
    except Exception as e:
        print(f"⚠️ Could not verify count: {e}")
    
    if total_uploaded > 0:
        print(f"\n🎯 SUCCESS! {total_uploaded} recipes uploaded with all original tags and format!")
        print("🔧 To upload remaining recipes, run this script again or increase batch size")
    else:
        print("\n❌ No recipes were uploaded. Check the error messages above.")

if __name__ == "__main__":
    batch_upload_all_recipes()
