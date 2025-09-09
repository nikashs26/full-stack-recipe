from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["*"])

# Load recipes from the exported JSON file
def load_recipes():
    try:
        # Try to load from the recipes_data.json file
        with open('recipes_data.json', 'r', encoding='utf-8') as f:
            recipes = json.load(f)
            print(f"Loaded {len(recipes)} recipes from recipes_data.json")
            return recipes
    except FileNotFoundError:
        print("recipes_data.json not found, returning empty list")
        return []
    except Exception as e:
        print(f"Error loading recipes: {e}")
        return []

# Load recipes at startup
RECIPES = load_recipes()
print(f"Total recipes loaded: {len(RECIPES)}")

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "message": "Recipe app is running"})

@app.route('/api/debug')
def debug():
    return jsonify({
        "current_directory": os.getcwd(),
        "files_in_directory": os.listdir('.'),
        "recipes_loaded": len(RECIPES),
        "recipe_file_exists": os.path.exists('recipes_data.json'),
        "recipe_file_size": os.path.getsize('recipes_data.json') if os.path.exists('recipes_data.json') else 0
    })

@app.route('/api/recipe-counts')
def recipe_counts():
    cuisines = {}
    diets = {}
    
    for recipe in RECIPES:
        # Count cuisines
        for cuisine in recipe.get('cuisines', []):
            cuisines[cuisine] = cuisines.get(cuisine, 0) + 1
        
        # Count diets
        for diet in recipe.get('diets', []):
            diets[diet] = diets.get(diet, 0) + 1
    
    return jsonify({
        "total": len(RECIPES),
        "by_cuisine": cuisines,
        "by_diet": diets
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
