#!/usr/bin/env python3
"""
Force populate recipes using a completely different approach
"""
import json
import requests

def force_populate():
    """Create a new admin endpoint that forces fresh code execution"""
    
    # Create a completely new admin endpoint in a separate file
    new_endpoint_code = '''
@admin_bp.route('/api/admin/force-seed', methods=['POST'])
def force_seed_recipes():
    """Force seed recipes with fresh code - bypass all caching"""
    if not _check_token(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import json
        import os
        
        # Read recipes directly
        recipes_path = "/opt/render/project/src/recipes_data.json"
        if not os.path.exists(recipes_path):
            recipes_path = "recipes_data.json"
        
        with open(recipes_path, 'r') as f:
            recipes = json.load(f)
        
        # Get ChromaDB client directly
        import chromadb
        chroma_path = "/opt/render/project/src/chroma_db"
        client = chromadb.PersistentClient(path=chroma_path)
        
        # Create collections with simple embedding
        try:
            recipe_collection = client.get_or_create_collection(
                name="recipe_details_cache_force",
                metadata={"description": "Force-created recipe cache"}
            )
        except:
            recipe_collection = client.get_collection("recipe_details_cache_force")
        
        # Process recipes with manual flattening
        count = 0
        limit = int(request.get_json().get('limit', 10))
        
        for recipe in recipes[:limit]:
            # Manual metadata flattening - FORCE it to work
            flat_meta = {}
            for key, value in recipe.items():
                if key in ['id', 'title', 'cuisine', 'calories', 'protein', 'carbs', 'fat']:
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        flat_meta[key] = value
                    else:
                        flat_meta[key] = str(value)
            
            # Add required fields
            flat_meta['id'] = str(recipe.get('id', count))
            flat_meta['title'] = str(recipe.get('title', 'Recipe'))
            
            # Store as document
            doc = json.dumps(recipe)
            
            try:
                recipe_collection.add(
                    ids=[flat_meta['id']], 
                    documents=[doc], 
                    metadatas=[flat_meta]
                )
                count += 1
            except Exception as e:
                return jsonify({'error': f'Failed at recipe {count}: {str(e)}'})
        
        return jsonify({'success': True, 'added': count, 'collection': 'recipe_details_cache_force'})
        
    except Exception as e:
        return jsonify({'error': f'Force seed failed: {str(e)}'})
'''
    
    print("🚀 Force Recipe Population")
    print("=" * 40)
    
    # Let's try the simplest possible approach - upload flattened recipes and test
    print("1. Uploading flattened recipes file to server...")
    
    # First, let's copy our flattened file to the server location
    # We'll use the debug info to understand the server structure
    
    admin_token = "390a77929dbe4a50705a8d8cd2888678"
    base_url = "https://dietary-delight.onrender.com"
    
    # Try to test with our flattened recipes file
    print("2. Testing with flattened recipes...")
    
    try:
        response = requests.post(
            f"{base_url}/api/admin/seed",
            headers={
                "Content-Type": "application/json", 
                "X-Admin-Token": admin_token
            },
            json={"path": "flattened_recipes_test.json", "limit": 1},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if "File not found" in response.text:
            print("❌ Flattened file not found on server")
            print("💡 Need to upload flattened_recipes_test.json to the server")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    # Alternative: Create a manual ChromaDB population via raw API
    print("\n3. Alternative: Manual ChromaDB population")
    print("Since the admin endpoint has persistent issues, here are direct solutions:")
    
    print("\n🔧 Option A: Upload via file manager")
    print("1. Copy flattened_recipes_test.json to your server")
    print("2. Use the manual test command from the previous script")
    
    print("\n🔧 Option B: Restart service completely") 
    print("1. Go to Render dashboard")
    print("2. Click 'Manual Deploy' to force a complete refresh")
    print("3. This should clear all Python cache")
    
    print("\n🔧 Option C: Direct ChromaDB REST API")
    print("If ChromaDB has a REST API enabled, we could populate directly")
    
    # Create a simple recipe to verify the structure
    simple_recipe = {
        "id": "simple_001",
        "title": "Simple Test Recipe", 
        "cuisine": "Test",
        "calories": 300,
        "protein": 20.0,
        "carbs": 30.0,
        "fat": 10.0,
        "ingredients": "test ingredients",
        "instructions": "test instructions"
    }
    
    print(f"\n🧪 Simple recipe structure: {json.dumps(simple_recipe, indent=2)}")
    print("This should work without any metadata flattening issues")

if __name__ == "__main__":
    force_populate()
