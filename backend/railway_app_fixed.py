from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["*"])

# Load recipes from the large file
def load_recipes():
    try:
        with open('railway_app_with_recipes.py', 'r') as f:
            content = f.read()
            # Extract the RECIPES array from the file
            start_marker = "RECIPES = ["
            end_marker = "]"
            start_idx = content.find(start_marker)
            if start_idx != -1:
                end_idx = content.find(end_marker, start_idx)
                if end_idx != -1:
                    recipes_str = content[start_idx + len(start_marker):end_idx]
                    # Add the brackets back
                    recipes_str = "[" + recipes_str + "]"
                    return json.loads(recipes_str)
    except Exception as e:
        print(f"Error loading recipes: {e}")
    return []

# Load recipes at startup
RECIPES = load_recipes()
print(f"Loaded {len(RECIPES)} recipes")

@app.route('/')
def root():
    return jsonify({
        "message": "Recipe App API", 
        "status": "running",
        "total_recipes": len(RECIPES),
        "endpoints": ["/api/health", "/api/recipes", "/api/recipes/cuisines", "/get_recipe_by_id"]
    })

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "message": "Recipe app is running"})

@app.route('/api/recipe-counts')
def recipe_counts():
    return jsonify({
        "status": "success",
        "data": {
            "total": len(RECIPES),
            "valid": len(RECIPES),
            "expired": 0
        }
    })

@app.route('/api/recipes')
def get_recipes():
    query = request.args.get('query', '').strip().lower()
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    
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
    
    # Apply pagination
    total = len(filtered_recipes)
    paginated_recipes = filtered_recipes[offset:offset + limit]
    
    return jsonify({
        "results": paginated_recipes,
        "total": total,
        "limit": limit,
        "offset": offset
    })

@app.route('/api/recipes/cuisines')
def get_cuisines():
    cuisines = list(set(recipe['cuisine'].lower() for recipe in RECIPES if recipe.get('cuisine')))
    return jsonify({"cuisines": cuisines})

@app.route('/get_recipe_by_id')
def get_recipe_by_id():
    recipe_id = request.args.get('id')
    if not recipe_id:
        return jsonify({"error": "Recipe ID required"}), 400
    
    recipe = next((r for r in RECIPES if r['id'] == recipe_id), None)
    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404
    
    return jsonify(recipe)

# Add alias for frontend compatibility
@app.route('/api/get_recipes')
def get_recipes_alias():
    return get_recipes()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
