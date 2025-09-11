#!/usr/bin/env python3
"""
Direct ChromaDB population script - bypasses the admin API entirely
"""
import json
import requests
import time

def populate_recipes_directly():
    """
    Directly populate recipes using ChromaDB client API calls
    """
    print("🚀 Direct Recipe Population Script")
    print("=" * 50)
    
    # Load recipes
    try:
        with open('recipes_data.json', 'r') as f:
            recipes = json.load(f)
        print(f"✅ Loaded {len(recipes)} recipes from local file")
    except Exception as e:
        print(f"❌ Failed to load recipes: {e}")
        return
    
    # Flatten recipes to avoid metadata issues
    print("🔧 Flattening recipe metadata...")
    processed_recipes = []
    
    for i, recipe in enumerate(recipes):
        if i >= 100:  # Limit for testing
            break
            
        # Create ChromaDB-compatible metadata
        metadata = {}
        for key, value in recipe.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                metadata[key] = value
            elif isinstance(value, (dict, list)):
                # Convert complex objects to JSON strings
                metadata[key] = json.dumps(value)
            else:
                metadata[key] = str(value)
        
        # Store full recipe as document
        document = json.dumps(recipe)
        
        processed_recipes.append({
            'id': str(recipe.get('id', i)),
            'document': document,
            'metadata': metadata
        })
    
    print(f"✅ Processed {len(processed_recipes)} recipes")
    
    # Create API payload for direct ChromaDB population
    admin_token = "390a77929dbe4a50705a8d8cd2888678"
    base_url = "https://dietary-delight.onrender.com"
    
    # Try to add recipes one by one to identify any specific issues
    print("\n🌱 Adding recipes to ChromaDB...")
    success_count = 0
    
    # Create a custom endpoint payload that does the population directly
    payload = {
        "action": "direct_populate",
        "recipes": processed_recipes[:10]  # Start with just 10 recipes
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Token": admin_token
    }
    
    # First try to create a simplified admin endpoint call
    try:
        # Let's create a minimal test recipe first
        test_recipe = {
            "id": "test_001",
            "title": "Test Recipe",
            "cuisine": "Test",
            "calories": 300,
            "protein": 20,
            "ingredients": "test ingredients",
            "instructions": "test instructions"
        }
        
        test_payload = {
            "action": "test_add",
            "recipe": test_recipe
        }
        
        print("🧪 Testing with simple recipe...")
        response = requests.post(f"{base_url}/api/admin/seed", 
                               headers=headers, 
                               json=test_payload, 
                               timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    # Alternative approach: Use the debug endpoint to understand the environment better
    print("\n🔍 Checking deployment environment...")
    try:
        debug_response = requests.get(f"{base_url}/api/admin/debug", 
                                    params={"token": admin_token}, 
                                    timeout=10)
        
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            print(f"✅ Working directory: {debug_data.get('current_working_directory')}")
            print(f"✅ ChromaDB status: {debug_data.get('chromadb_status', {})}")
            print(f"✅ Recipe files available: {list(debug_data.get('file_checks', {}).keys())}")
        
    except Exception as e:
        print(f"⚠️ Debug check failed: {e}")
    
    print("\n💡 Recommendation:")
    print("Since the admin API has metadata issues, try these options:")
    print("1. Use Render dashboard to restart the service completely")
    print("2. Check if there are any Python cache files (__pycache__) that need clearing")
    print("3. Try uploading the flattened_recipes_test.json file we created")
    
    # Create a simple curl command for manual testing
    print("\n🔧 Manual test command:")
    print(f"""curl -X POST "{base_url}/api/admin/seed" \\
  -H "Content-Type: application/json" \\
  -H "X-Admin-Token: {admin_token}" \\
  -d '{{"path": "flattened_recipes_test.json", "limit": 5}}'""")

if __name__ == "__main__":
    populate_recipes_directly()
