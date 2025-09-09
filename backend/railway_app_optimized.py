from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["*"])

# Load recipes from JSON file
def load_recipes():
    try:
        # Try multiple possible paths
        possible_paths = [
            'recipes_data.json',
            './recipes_data.json',
            '/app/recipes_data.json',
            os.path.join(os.path.dirname(__file__), 'recipes_data.json')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Loading recipes from: {path}")
                with open(path, 'r') as f:
                    return json.load(f)
        
        print(f"Recipes file not found. Tried paths: {possible_paths}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Files in current directory: {os.listdir('.')}")
        return []
    except Exception as e:
        print(f"Error loading recipes: {e}")
        return []

# Load recipes at startup
RECIPES = load_recipes()
print(f"Loaded {len(RECIPES)} recipes")

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "message": "Recipe app is running"})

@app.route('/api/recipe-counts')
def recipe_counts():
    return jsonify({
        "total": len(RECIPES),
        "by_cuisine": {},
        "by_diet": {}
    })

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
    
    return jsonify({
        "results": paginated_recipes,
        "total": total,
        "limit": limit,
        "offset": offset
    })

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
        return jsonify({"error": "Recipe ID is required"}), 400
    
    recipe = next((r for r in RECIPES if r['id'] == recipe_id), None)
    if recipe:
        return jsonify(recipe)
    else:
        return jsonify({"error": "Recipe not found"}), 404

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
    
    return jsonify({
        "results": paginated_recipes,
        "total": total,
        "limit": limit,
        "offset": offset
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
