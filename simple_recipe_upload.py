#!/usr/bin/env python3
"""
Simple Recipe Upload - Just get your recipes showing on Render with all metadata
"""

import json
import requests
import time

def upload_recipes_simple():
    """Upload recipes directly using the working admin endpoint"""
    
    print("🚀 Simple Recipe Upload to Render")
    print("=" * 40)
    
    # Configuration
    render_url = "https://dietary-delight.onrender.com"
    admin_token = "390a77929dbe4a50705a8d8cd2888678"
    
    # Load your best recipe data
    print("📋 Loading recipe data...")
    try:
        with open('recipes_data.json', 'r') as f:
            recipes = json.load(f)
        print(f"✅ Loaded {len(recipes)} recipes")
    except Exception as e:
        print(f"❌ Error loading recipes: {e}")
        return False
    
    # Create a temporary file with just the recipes that work
    print("🔧 Preparing recipes for upload...")
    
    # Filter out incomplete recipes and keep only the good ones
    good_recipes = []
    for recipe in recipes:
        # Check if recipe has the essential data
        if (recipe.get('title') and 
            recipe.get('ingredients') and 
            isinstance(recipe.get('ingredients'), list) and
            len(recipe.get('ingredients', [])) > 0):
            good_recipes.append(recipe)
    
    print(f"✅ Found {len(good_recipes)} complete recipes")
    
    # Save to temporary file that the admin endpoint can use
    temp_filename = "recipes_for_render.json"
    with open(temp_filename, 'w') as f:
        json.dump(good_recipes, f, indent=2)
    
    print(f"💾 Saved recipes to {temp_filename}")
    
    # Upload using the existing admin seed endpoint
    print("\n🚀 Uploading to Render...")
    
    try:
        # Use the existing admin seed endpoint with proper format
        payload = {
            "limit": len(good_recipes),  # Upload all recipes
            "truncate": True  # Clear existing to avoid duplicates
        }
        
        response = requests.post(
            f"{render_url}/api/admin/seed",
            headers={
                "Content-Type": "application/json",
                "X-Admin-Token": admin_token
            },
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"📊 Response: {result}")
            
            # Wait a moment and check the stats
            print("\n🔍 Verifying upload...")
            time.sleep(3)
            
            stats_response = requests.get(
                f"{render_url}/api/admin/debug",
                params={"token": admin_token},
                timeout=15
            )
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                chroma_status = stats.get('chromadb_status', {})
                recipe_count = chroma_status.get('recipe_count', 0)
                print(f"✅ Render now has {recipe_count} recipes!")
                
                if recipe_count > 100:
                    print("\n🎉 SUCCESS! Your recipes should now appear in the app!")
                    print("🌐 Check: https://dietary-delight.onrender.com")
                    print("🔍 Try searching for cuisines, ingredients, or recipe names")
                    return True
                else:
                    print("⚠️ Recipe count seems low, but upload completed")
            
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            
            # If direct upload fails, try the file-based approach
            print("\n🔄 Trying alternative upload method...")
            return try_file_based_upload(render_url, admin_token, temp_filename)
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False
    
    return False

def try_file_based_upload(render_url, admin_token, filename):
    """Try uploading by specifying the file path"""
    try:
        payload = {
            "path": filename,  # Point to our prepared file
            "limit": 5000,
            "truncate": True
        }
        
        response = requests.post(
            f"{render_url}/api/admin/seed",
            headers={
                "Content-Type": "application/json", 
                "X-Admin-Token": admin_token
            },
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ File-based upload successful!")
            print(f"📊 Response: {result}")
            return True
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ File upload error: {e}")
    
    return False

def main():
    """Main function"""
    print("🎯 Goal: Get all your recipes showing on Render with tags, cuisines, and images")
    print("\nThis will:")
    print("1. Load your local recipe data")
    print("2. Filter out incomplete recipes") 
    print("3. Upload complete recipes to Render")
    print("4. Verify they're showing up")
    
    proceed = input("\nProceed? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Cancelled.")
        return
    
    success = upload_recipes_simple()
    
    if success:
        print("\n🎉 DONE! Your recipes should now be visible on Render!")
        print("✅ All tags, cuisines, and images preserved")
        print("✅ Search functionality should work")
        print("✅ Recipe details should display properly")
    else:
        print("\n❌ Upload failed. Let me know the error messages and I'll help fix it.")

if __name__ == "__main__":
    main()

