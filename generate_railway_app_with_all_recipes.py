#!/usr/bin/env python3
"""
Generate a new Railway app file with all local recipes
This will create a static file that Railway can use
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

def generate_railway_app_with_all_recipes():
    """Generate Railway app file with all local recipes"""
    print("🚀 Generating Railway app with all local recipes...")
    
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
        recipes = []
        for i, (recipe_id, metadata, document) in enumerate(zip(all_recipes['ids'], all_recipes['metadatas'], all_recipes['documents'])):
            try:
                recipe_data = json.loads(document)
                
                # Ensure required fields exist
                recipe = {
                    'id': recipe_id,
                    'title': recipe_data.get('title', 'Unknown Recipe'),
                    'cuisine': recipe_data.get('cuisine', 'unknown'),
                    'cuisines': recipe_data.get('cuisines', [recipe_data.get('cuisine', 'unknown')]),
                    'diets': recipe_data.get('diets', []),
                    'ingredients': recipe_data.get('ingredients', []),
                    'instructions': recipe_data.get('instructions', []),
                    'image': recipe_data.get('image', ''),
                    'description': recipe_data.get('description', ''),
                    'calories': recipe_data.get('calories', 0),
                    'protein': recipe_data.get('protein', 0),
                    'carbs': recipe_data.get('carbs', 0),
                    'fat': recipe_data.get('fat', 0),
                    'readyInMinutes': recipe_data.get('readyInMinutes', 0),
                    'servings': recipe_data.get('servings', 1),
                    'source': recipe_data.get('source', 'local'),
                    'sourceUrl': recipe_data.get('sourceUrl', ''),
                    'spoonacularScore': recipe_data.get('spoonacularScore', 0),
                    'healthScore': recipe_data.get('healthScore', 0),
                    'pricePerServing': recipe_data.get('pricePerServing', 0),
                    'cheap': recipe_data.get('cheap', False),
                    'dairyFree': recipe_data.get('dairyFree', False),
                    'glutenFree': recipe_data.get('glutenFree', False),
                    'ketogenic': recipe_data.get('ketogenic', False),
                    'lowFodmap': recipe_data.get('lowFodmap', False),
                    'sustainable': recipe_data.get('sustainable', False),
                    'vegan': recipe_data.get('vegan', False),
                    'vegetarian': recipe_data.get('vegetarian', False),
                    'veryHealthy': recipe_data.get('veryHealthy', False),
                    'veryPopular': recipe_data.get('veryPopular', False),
                    'whole30': recipe_data.get('whole30', False),
                    'weightWatcherSmartPoints': recipe_data.get('weightWatcherSmartPoints', 0),
                    'dishTypes': recipe_data.get('dishTypes', []),
                    'occasions': recipe_data.get('occasions', []),
                    'winePairing': recipe_data.get('winePairing', {}),
                    'analyzedInstructions': recipe_data.get('analyzedInstructions', []),
                    'extendedIngredients': recipe_data.get('extendedIngredients', []),
                    'summary': recipe_data.get('summary', ''),
                    'winePairingText': recipe_data.get('winePairingText', ''),
                    'tags': recipe_data.get('tags', []),
                    'usedIngredientCount': recipe_data.get('usedIngredientCount', 0),
                    'missedIngredientCount': recipe_data.get('missedIngredientCount', 0),
                    'likes': recipe_data.get('likes', 0),
                    'favorite': recipe_data.get('favorite', False),
                    'comments': recipe_data.get('comments', [])
                }
                
                recipes.append(recipe)
                
                if (i + 1) % 100 == 0:
                    print(f"   📦 Processed {i + 1} recipes...")
                    
            except Exception as e:
                print(f"   ⚠️  Error processing recipe {recipe_id}: {e}")
                continue
        
        print(f"   ✅ Processed {len(recipes)} recipes successfully")
        
        # Generate the Railway app file
        app_content = f'''from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["*"])

# Recipe data - {len(recipes)} recipes loaded
RECIPES = {json.dumps(recipes, indent=2)}

@app.route('/api/health')
def health():
    return jsonify({{"status": "healthy", "message": "Recipe app is running"}})

@app.route('/api/recipe-counts')
def recipe_counts():
    return jsonify({{
        "total": len(RECIPES),
        "by_cuisine": {{}},
        "by_diet": {{}}
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
        
        # Write the new Railway app file
        output_file = 'backend/railway_app_with_all_recipes.py'
        with open(output_file, 'w') as f:
            f.write(app_content)
        
        print(f"✅ Generated Railway app file: {output_file}")
        print(f"📊 Contains {len(recipes)} recipes")
        
        # Also create a backup of the original
        original_file = 'backend/railway_app_with_recipes.py'
        backup_file = 'backend/railway_app_with_recipes_backup.py'
        
        if os.path.exists(original_file):
            import shutil
            shutil.copy2(original_file, backup_file)
            print(f"💾 Created backup: {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating Railway app: {e}")
        return False

if __name__ == "__main__":
    generate_railway_app_with_all_recipes()
