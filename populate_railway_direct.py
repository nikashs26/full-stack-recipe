#!/usr/bin/env python3
"""
Direct Railway Population Script
This script will populate Railway with all local recipes directly
"""

import os
import sys
import json
import requests
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

def create_railway_app_with_all_recipes():
    """Create a Railway app file with all local recipes embedded"""
    print("🚀 Creating Railway app with all local recipes...")
    
    try:
        # Initialize local recipe cache
        recipe_cache = RecipeCacheService()
        
        # Get all local recipes
        all_recipes = recipe_cache.recipe_collection.get(include=['metadatas', 'documents'])
        
        if not all_recipes['ids']:
            print("❌ No local recipes found")
            return False
        
        print(f"📊 Found {len(all_recipes['ids'])} local recipes")
        
        # Process recipes
        processed_recipes = []
        for i, (recipe_id, metadata, document) in enumerate(zip(all_recipes['ids'], all_recipes['metadatas'], all_recipes['documents'])):
            try:
                recipe_data = json.loads(document)
                
                # Merge metadata into recipe data
                merged_recipe = recipe_data.copy()
                for key, value in metadata.items():
                    if key not in merged_recipe or merged_recipe[key] is None or merged_recipe[key] == '':
                        merged_recipe[key] = value
                
                processed_recipes.append(merged_recipe)
                
                if (i + 1) % 100 == 0:
                    print(f"   Processed {i + 1}/{len(all_recipes['ids'])} recipes...")
                    
            except Exception as e:
                print(f"   ⚠️ Error processing recipe {recipe_id}: {e}")
                continue
        
        print(f"✅ Processed {len(processed_recipes)} recipes")
        
        # Create the Railway app file
        app_content = f'''from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["*"])

# Recipe data - {len(processed_recipes)} recipes loaded
RECIPES = {json.dumps(processed_recipes, indent=2)}

@app.route('/api/health')
def health():
    return jsonify({{"status": "healthy", "message": "Recipe app is running"}})

@app.route('/api/debug')
def debug():
    return jsonify({{
        "current_directory": os.getcwd(),
        "files_in_directory": os.listdir('.'),
        "recipes_loaded": len(RECIPES),
        "recipe_file_exists": False,
        "recipe_file_size": 0
    }})

@app.route('/api/recipe-counts')
def recipe_counts():
    cuisines = {{}}
    diets = {{}}
    
    for recipe in RECIPES:
        # Count cuisines
        for cuisine in recipe.get('cuisines', []):
            cuisines[cuisine] = cuisines.get(cuisine, 0) + 1
        
        # Count diets
        for diet in recipe.get('diets', []):
            diets[diet] = diets.get(diet, 0) + 1
    
    return jsonify({{
        "total": len(RECIPES),
        "by_cuisine": cuisines,
        "by_diet": diets
    }})

@app.route('/api/recipes')
def get_recipes():
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    cuisine = request.args.get('cuisine', '')
    diet = request.args.get('diet', '')
    search = request.args.get('search', '')
    
    filtered_recipes = RECIPES
    
    # Filter by cuisine
    if cuisine:
        filtered_recipes = [r for r in filtered_recipes if cuisine.lower() in [c.lower() for c in r.get('cuisines', [])]]
    
    # Filter by diet
    if diet:
        filtered_recipes = [r for r in filtered_recipes if diet.lower() in [d.lower() for d in r.get('diets', [])]]
    
    # Filter by search term
    if search:
        search_lower = search.lower()
        filtered_recipes = [r for r in filtered_recipes if 
                           search_lower in r.get('title', '').lower() or 
                           search_lower in r.get('description', '').lower() or
                           any(search_lower in ing.get('name', '').lower() for ing in r.get('ingredients', []))]
    
    # Apply pagination
    total = len(filtered_recipes)
    paginated_recipes = filtered_recipes[offset:offset + limit]
    
    return jsonify({{
        "results": paginated_recipes,
        "total": total,
        "limit": limit,
        "offset": offset
    }})

@app.route('/api/recipes/cuisines')
def get_cuisines():
    cuisines = set()
    for recipe in RECIPES:
        cuisines.update(recipe.get('cuisines', []))
    return jsonify(list(cuisines))

@app.route('/get_recipe_by_id')
def get_recipe_by_id():
    recipe_id = request.args.get('id')
    if not recipe_id:
        return jsonify({{"error": "Recipe ID is required"}}), 400
    
    recipe = next((r for r in RECIPES if r['id'] == recipe_id), None)
    if recipe:
        return jsonify(recipe)
    else:
        return jsonify({{"error": "Recipe not found"}}), 404

@app.route('/api/get_recipes')
def get_recipes_legacy():
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    cuisine = request.args.get('cuisine', '')
    diet = request.args.get('diet', '')
    search = request.args.get('search', '')
    
    filtered_recipes = RECIPES
    
    # Filter by cuisine
    if cuisine:
        filtered_recipes = [r for r in filtered_recipes if cuisine.lower() in [c.lower() for c in r.get('cuisines', [])]]
    
    # Filter by diet
    if diet:
        filtered_recipes = [r for r in filtered_recipes if diet.lower() in [d.lower() for d in r.get('diets', [])]]
    
    # Filter by search term
    if search:
        search_lower = search.lower()
        filtered_recipes = [r for r in filtered_recipes if 
                           search_lower in r.get('title', '').lower() or 
                           search_lower in r.get('description', '').lower() or
                           any(search_lower in ing.get('name', '').lower() for ing in r.get('ingredients', []))]
    
    # Apply pagination
    total = len(filtered_recipes)
    paginated_recipes = filtered_recipes[offset:offset + limit]
    
    return jsonify({{
        "results": paginated_recipes,
        "total": total,
        "limit": limit,
        "offset": offset
    }})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
'''
        
        # Write the app file
        with open('backend/railway_app_with_all_recipes.py', 'w', encoding='utf-8') as f:
            f.write(app_content)
        
        print(f"✅ Created railway_app_with_all_recipes.py with {len(processed_recipes)} recipes")
        
        # Update Dockerfile to use this new app
        dockerfile_path = 'backend/Dockerfile'
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        # Replace the CMD line
        new_dockerfile_content = dockerfile_content.replace(
            'CMD gunicorn app_railway:app',
            'CMD gunicorn railway_app_with_all_recipes:app'
        )
        
        with open(dockerfile_path, 'w') as f:
            f.write(new_dockerfile_content)
        
        print("✅ Updated Dockerfile to use railway_app_with_all_recipes.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating Railway app: {e}")
        return False

def main():
    """Main function"""
    print("🍳 Railway Direct Population Script")
    print("=" * 50)
    
    success = create_railway_app_with_all_recipes()
    
    if success:
        print("\n🎉 Railway app created successfully!")
        print("📤 Ready to deploy to Railway")
        print("💡 Run 'railway up' to deploy with all recipes")
    else:
        print("\n❌ Failed to create Railway app")
        sys.exit(1)

if __name__ == "__main__":
    main()
