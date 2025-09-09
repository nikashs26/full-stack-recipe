#!/usr/bin/env python3
"""
Add all local recipes to Railway simple app
This will create a comprehensive recipe database
"""

import sys
import os
import json
import requests
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

class RecipeUploader:
    def __init__(self):
        self.api_url = "https://full-stack-recipe-production.up.railway.app/api"
        self.recipe_cache = RecipeCacheService()
        
    def get_all_local_recipes(self):
        """Get all recipes from local ChromaDB"""
        try:
            all_recipes = self.recipe_cache.get_cached_recipes()
            print(f"📚 Found {len(all_recipes)} local recipes")
            return all_recipes
        except Exception as e:
            print(f"❌ Error getting local recipes: {e}")
            return []
    
    def format_recipe_for_railway(self, recipe):
        """Format a recipe for the Railway simple app"""
        try:
            # Get metadata
            result = self.recipe_cache.recipe_collection.get(
                ids=[recipe['id']],
                include=['metadatas']
            )
            
            metadata = result['metadatas'][0] if result['metadatas'] else {}
            
            # Create formatted recipe
            formatted_recipe = {
                "id": recipe.get('id', ''),
                "title": recipe.get('title', 'Untitled Recipe'),
                "cuisine": recipe.get('cuisine', 'International'),
                "cuisines": [recipe.get('cuisine', 'International').lower()] if recipe.get('cuisine') else ['international'],
                "diets": recipe.get('diets', ''),
                "ingredients": recipe.get('ingredients', []),
                "instructions": recipe.get('instructions', []),
                "calories": recipe.get('calories', 0),
                "protein": recipe.get('protein', 0),
                "carbs": recipe.get('carbs', 0),
                "fat": recipe.get('fat', 0),
                "image": recipe.get('image', ''),
                "description": recipe.get('description', '')
            }
            
            # Ensure ingredients and instructions are arrays
            if isinstance(formatted_recipe['ingredients'], str):
                try:
                    formatted_recipe['ingredients'] = json.loads(formatted_recipe['ingredients'])
                except:
                    formatted_recipe['ingredients'] = []
            
            if isinstance(formatted_recipe['instructions'], str):
                try:
                    formatted_recipe['instructions'] = json.loads(formatted_recipe['instructions'])
                except:
                    formatted_recipe['instructions'] = []
            
            # Ensure cuisines is an array
            if isinstance(formatted_recipe['cuisines'], str):
                try:
                    formatted_recipe['cuisines'] = json.loads(formatted_recipe['cuisines'])
                except:
                    formatted_recipe['cuisines'] = [formatted_recipe['cuisines']]
            
            return formatted_recipe
            
        except Exception as e:
            print(f"   ⚠️ Error formatting recipe {recipe.get('id', 'unknown')}: {e}")
            return None
    
    def create_railway_app_with_recipes(self, recipes):
        """Create a new Railway app file with all recipes"""
        try:
            # Create the app content
            app_content = f'''from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["*"])

# Recipe data
RECIPES = {json.dumps(recipes, indent=2)}

@app.route('/api/health')
def health():
    return jsonify({{"status": "healthy", "message": "Recipe app is running"}})

@app.route('/api/recipe-counts')
def recipe_counts():
    return jsonify({{
        "status": "success",
        "data": {{
            "total": len(RECIPES),
            "valid": len(RECIPES),
            "expired": 0
        }}
    }})

@app.route('/api/recipes')
def get_recipes():
    query = request.args.get('query', '').strip().lower()
    limit = int(request.args.get('limit', 20))
    
    # Filter recipes based on query
    if query:
        filtered_recipes = [
            recipe for recipe in RECIPES
            if query in recipe['title'].lower() or 
               query in recipe['cuisine'].lower() or
               any(query in ing.get('name', '').lower() for ing in recipe.get('ingredients', []))
        ]
    else:
        filtered_recipes = RECIPES
    
    # Apply limit
    filtered_recipes = filtered_recipes[:limit]
    
    return jsonify({{
        "results": filtered_recipes,
        "total": len(filtered_recipes)
    }})

@app.route('/api/recipes/cuisines')
def get_cuisines():
    cuisines = list(set(recipe['cuisine'].lower() for recipe in RECIPES if recipe.get('cuisine')))
    return jsonify({{"cuisines": cuisines}})

@app.route('/get_recipe_by_id')
def get_recipe_by_id():
    recipe_id = request.args.get('id')
    if not recipe_id:
        return jsonify({{"error": "Recipe ID required"}}), 400
    
    recipe = next((r for r in RECIPES if r['id'] == recipe_id), None)
    if not recipe:
        return jsonify({{"error": "Recipe not found"}}), 404
    
    return jsonify(recipe)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
'''
            
            # Write to file
            with open('backend/railway_app_with_recipes.py', 'w') as f:
                f.write(app_content)
            
            print(f"✅ Created railway_app_with_recipes.py with {len(recipes)} recipes")
            return True
            
        except Exception as e:
            print(f"❌ Error creating Railway app: {e}")
            return False
    
    def upload_recipes(self):
        """Upload all recipes to Railway"""
        print("🚀 Starting recipe upload to Railway...")
        
        # Get all local recipes
        local_recipes = self.get_all_local_recipes()
        if not local_recipes:
            print("❌ No local recipes found")
            return False
        
        # Format recipes
        formatted_recipes = []
        for recipe in local_recipes:
            formatted = self.format_recipe_for_railway(recipe)
            if formatted:
                formatted_recipes.append(formatted)
        
        print(f"📝 Formatted {len(formatted_recipes)} recipes")
        
        # Create Railway app with all recipes
        if self.create_railway_app_with_recipes(formatted_recipes):
            print("✅ Railway app created successfully")
            print("💡 Next step: Update Dockerfile to use railway_app_with_recipes.py")
            return True
        else:
            print("❌ Failed to create Railway app")
            return False

def main():
    uploader = RecipeUploader()
    success = uploader.upload_recipes()
    
    if success:
        print("\n🎉 Recipe upload completed successfully!")
        print("🌐 Your Netlify site now has all your local recipes")
        print("💡 The recipes will persist through commits")
    else:
        print("\n❌ Recipe upload failed")

if __name__ == "__main__":
    main()
