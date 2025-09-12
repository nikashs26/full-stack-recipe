#!/usr/bin/env python3
"""
Fix recipe data formatting and upload directly
"""

import json
import requests
import time

def fix_recipes_for_chromadb():
    """Fix recipe data to avoid ChromaDB metadata errors"""
    
    print("🔧 Fixing Recipe Data for ChromaDB Compatibility")
    print("=" * 50)
    
    # Load your recipes
    with open('recipes_data.json', 'r') as f:
        recipes = json.load(f)
    
    print(f"📋 Processing {len(recipes)} recipes...")
    
    fixed_recipes = []
    
    for i, recipe in enumerate(recipes):
        try:
            # Check if recipe has essential data
            if not (recipe.get('title') and recipe.get('ingredients')):
                continue
                
            # Create a fixed version of the recipe
            fixed_recipe = {
                'id': str(recipe.get('id', f'recipe_{i}')),
                'title': recipe.get('title', ''),
                'ingredients': recipe.get('ingredients', []),
                'instructions': recipe.get('instructions', []),
                'image': recipe.get('image', ''),
                'cuisines': recipe.get('cuisines', []),
                'diets': recipe.get('diets', ''),
                'tags': recipe.get('tags', ''),
                'dish_types': recipe.get('dish_types', ''),
                'type': recipe.get('type', 'imported'),
                'source': recipe.get('source', 'local'),
                'ready_in_minutes': recipe.get('ready_in_minutes', 30),
                'cooking_time': recipe.get('cooking_time', 30),
            }
            
            # Handle nutrition data properly - flatten it to avoid metadata issues
            if recipe.get('nutrition'):
                nutrition = recipe['nutrition']
                fixed_recipe['calories'] = nutrition.get('calories', 0)
                fixed_recipe['protein'] = nutrition.get('protein', 0)
                fixed_recipe['carbs'] = nutrition.get('carbs', 0)
                fixed_recipe['fat'] = nutrition.get('fat', 0)
            else:
                # Get nutrition from direct fields if available
                fixed_recipe['calories'] = recipe.get('calories', 0)
                fixed_recipe['protein'] = recipe.get('protein', 0)
                fixed_recipe['carbs'] = recipe.get('carbs', 0)
                fixed_recipe['fat'] = recipe.get('fat', 0)
            
            # Ensure arrays are arrays, not strings
            if isinstance(fixed_recipe['ingredients'], str):
                try:
                    fixed_recipe['ingredients'] = json.loads(fixed_recipe['ingredients'])
                except:
                    fixed_recipe['ingredients'] = []
            
            if isinstance(fixed_recipe['instructions'], str):
                try:
                    fixed_recipe['instructions'] = json.loads(fixed_recipe['instructions'])
                except:
                    fixed_recipe['instructions'] = [fixed_recipe['instructions']] if fixed_recipe['instructions'] else []
            
            if isinstance(fixed_recipe['cuisines'], str):
                fixed_recipe['cuisines'] = [fixed_recipe['cuisines']] if fixed_recipe['cuisines'] else []
            
            # Validate essential fields
            if (isinstance(fixed_recipe['ingredients'], list) and 
                len(fixed_recipe['ingredients']) > 0 and
                isinstance(fixed_recipe['instructions'], list) and
                len(fixed_recipe['instructions']) > 0):
                fixed_recipes.append(fixed_recipe)
        
        except Exception as e:
            print(f"Error processing recipe {i}: {e}")
            continue
    
    print(f"✅ Fixed {len(fixed_recipes)} recipes")
    
    # Save the fixed recipes
    with open('recipes_fixed_for_render.json', 'w') as f:
        json.dump(fixed_recipes, f, indent=2)
    
    print("💾 Saved fixed recipes to recipes_fixed_for_render.json")
    return fixed_recipes

def upload_fixed_recipes(recipes):
    """Upload the fixed recipes using a direct ChromaDB approach"""
    
    print(f"\n🚀 Uploading {len(recipes)} Fixed Recipes")
    print("=" * 40)
    
    render_url = "https://dietary-delight.onrender.com"
    admin_token = "390a77929dbe4a50705a8d8cd2888678"
    
    # Upload in small batches to avoid timeouts
    batch_size = 50
    total_uploaded = 0
    
    for i in range(0, len(recipes), batch_size):
        batch = recipes[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(recipes) + batch_size - 1) // batch_size
        
        print(f"\n📦 Batch {batch_num}/{total_batches}: Uploading {len(batch)} recipes...")
        
        try:
            # Save this batch to a temporary file
            batch_filename = f"batch_{batch_num}.json"
            with open(batch_filename, 'w') as f:
                json.dump(batch, f)
            
            # Use the admin seed endpoint with the batch file
            payload = {
                "limit": len(batch),
                "truncate": (batch_num == 1)  # Only truncate on first batch
            }
            
            response = requests.post(
                f"{render_url}/api/admin/seed",
                headers={
                    "Content-Type": "application/json",
                    "X-Admin-Token": admin_token
                },
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                imported = result.get('imported', 0)
                total_uploaded += imported
                print(f"✅ Batch {batch_num}: {imported} recipes uploaded")
            else:
                print(f"❌ Batch {batch_num} failed: {response.status_code}")
                print(f"Response: {response.text[:200]}")
        
        except Exception as e:
            print(f"❌ Batch {batch_num} error: {e}")
        
        # Small delay between batches
        if batch_num < total_batches:
            time.sleep(2)
    
    print(f"\n📊 Total uploaded: {total_uploaded} recipes")
    return total_uploaded

def verify_upload():
    """Check if recipes are now visible"""
    render_url = "https://dietary-delight.onrender.com"
    admin_token = "390a77929dbe4a50705a8d8cd2888678"
    
    print("\n🔍 Verifying Upload...")
    
    try:
        response = requests.get(
            f"{render_url}/api/admin/debug",
            params={"token": admin_token},
            timeout=15
        )
        
        if response.status_code == 200:
            debug_data = response.json()
            chroma_status = debug_data.get('chromadb_status', {})
            recipe_count = chroma_status.get('recipe_count', 0)
            print(f"✅ Render recipe count: {recipe_count}")
            return recipe_count
        else:
            print(f"⚠️ Could not verify: {response.status_code}")
    
    except Exception as e:
        print(f"⚠️ Verification error: {e}")
    
    return 0

def main():
    """Main function"""
    print("🎯 Fix and Upload Recipes to Render")
    print("This will fix formatting issues and upload your recipes")
    
    # Step 1: Fix the recipe data
    fixed_recipes = fix_recipes_for_chromadb()
    
    if not fixed_recipes:
        print("❌ No valid recipes found")
        return
    
    # Step 2: Upload the fixed recipes
    uploaded_count = upload_fixed_recipes(fixed_recipes)
    
    # Step 3: Verify
    final_count = verify_upload()
    
    if final_count > 100:
        print("\n🎉 SUCCESS!")
        print(f"✅ {final_count} recipes are now available on Render")
        print("🌐 Check your app: https://dietary-delight.onrender.com")
        print("🔍 Your recipes should now display with tags, cuisines, and images!")
    else:
        print(f"\n⚠️ Upload completed but recipe count is {final_count}")
        print("Check the error messages above for issues")

if __name__ == "__main__":
    main()

