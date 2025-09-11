"""
Simple Recipe App with Real Recipe Data
Loads your 1000+ recipes directly from recipes_data.json
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json

# Simple Flask app
app = Flask(__name__)
CORS(app)

# Global recipe storage
RECIPES = []
RECIPES_LOADED = False

def load_recipes():
    """Load recipes from recipes_data.json"""
    global RECIPES, RECIPES_LOADED
    
    if RECIPES_LOADED:
        return
    
    try:
        # Look for recipes_data.json
        recipe_file = 'recipes_data.json'
        if os.path.exists(recipe_file):
            print(f"📖 Loading recipes from {recipe_file}...")
            with open(recipe_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different JSON structures
            if isinstance(data, list):
                RECIPES = data
            elif isinstance(data, dict):
                if 'recipes' in data:
                    RECIPES = data['recipes']
                elif 'results' in data:
                    RECIPES = data['results']
                else:
                    # Take the first list value
                    for value in data.values():
                        if isinstance(value, list):
                            RECIPES = value
                            break
            
            print(f"✅ Loaded {len(RECIPES)} recipes")
            RECIPES_LOADED = True
            
        else:
            print(f"⚠️ Recipe file {recipe_file} not found")
            RECIPES = []
            
    except Exception as e:
        print(f"⚠️ Error loading recipes: {e}")
        RECIPES = []

@app.route('/api/health')
def health():
    return {"status": "healthy", "message": f"Recipe app with {len(RECIPES)} recipes"}

@app.route('/api/recipes')
def get_recipes():
    """Get all recipes with pagination"""
    load_recipes()
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_recipes = RECIPES[start:end]
    
    return jsonify({
        "recipes": paginated_recipes,
        "total": len(RECIPES),
        "page": page,
        "per_page": per_page,
        "total_pages": (len(RECIPES) + per_page - 1) // per_page
    })

@app.route('/api/recipes/<recipe_id>')
def get_recipe(recipe_id):
    """Get a specific recipe"""
    load_recipes()
    
    # Find recipe by id
    recipe = None
    for r in RECIPES:
        if str(r.get('id')) == recipe_id or str(r.get('recipe_id')) == recipe_id:
            recipe = r
            break
    
    if recipe:
        return jsonify(recipe)
    return jsonify({"error": "Recipe not found"}), 404

@app.route('/api/recipes/search')
def search_recipes():
    """Search recipes by title or ingredient"""
    load_recipes()
    
    query = request.args.get('q', '').lower()
    if not query:
        return get_recipes()  # Return paginated results
    
    # Simple search
    filtered_recipes = []
    for recipe in RECIPES:
        title = recipe.get('title', '').lower()
        description = recipe.get('description', '').lower()
        ingredients = str(recipe.get('ingredients', '')).lower()
        
        if (query in title or 
            query in description or 
            query in ingredients):
            filtered_recipes.append(recipe)
    
    # Pagination for search results
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_results = filtered_recipes[start:end]
    
    return jsonify({
        "recipes": paginated_results,
        "total": len(filtered_recipes),
        "query": query,
        "page": page,
        "per_page": per_page,
        "total_pages": (len(filtered_recipes) + per_page - 1) // per_page
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting recipe app on port {port}...")
    load_recipes()
    app.run(host="0.0.0.0", port=port, debug=False)
