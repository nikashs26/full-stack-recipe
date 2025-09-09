from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import re

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["*"])

# Recipe storage - will be populated via uploads
RECIPES = []

def normalize_text(text):
    """Normalize text for better searching"""
    if not text:
        return ""
    return re.sub(r'[^\w\s]', '', str(text).lower())

def search_recipes(recipes, search_term, cuisines=None, diets=None, tags=None):
    """Enhanced search function with proper filtering"""
    if not search_term and not cuisines and not diets and not tags:
        return recipes
    
    filtered = []
    search_lower = normalize_text(search_term) if search_term else ""
    
    for recipe in recipes:
        # Text search
        if search_term:
            searchable_text = f"{recipe.get('title', '')} {recipe.get('description', '')} {recipe.get('tags', '')}"
            if search_lower not in normalize_text(searchable_text):
                continue
        
        # Cuisine filter
        if cuisines:
            recipe_cuisines = recipe.get('cuisines', [])
            if isinstance(recipe_cuisines, str):
                recipe_cuisines = [recipe_cuisines]
            recipe_cuisines = [c.lower() for c in recipe_cuisines]
            if not any(c.lower() in recipe_cuisines for c in cuisines):
                continue
        
        # Diet filter
        if diets:
            recipe_diets = recipe.get('diets', [])
            if isinstance(recipe_diets, str):
                recipe_diets = [recipe_diets]
            recipe_diets = [d.lower() for d in recipe_diets]
            if not any(d.lower() in recipe_diets for d in diets):
                continue
        
        # Tags filter
        if tags:
            recipe_tags = normalize_text(recipe.get('tags', ''))
            if not any(tag.lower() in recipe_tags for tag in tags):
                continue
        
        filtered.append(recipe)
    
    return filtered

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "Recipe app is running"
    })

@app.route('/api/get_recipes', methods=['GET'])
def get_recipes():
    """Get recipes with enhanced filtering"""
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search', '').strip()
        cuisine = request.args.get('cuisine', '').strip()
        diet = request.args.get('diet', '').strip()
        tag = request.args.get('tag', '').strip()
        
        # Parse multiple values
        cuisines = [c.strip() for c in cuisine.split(',')] if cuisine else None
        diets = [d.strip() for d in diet.split(',')] if diet else None
        tags = [t.strip() for t in tag.split(',')] if tag else None
        
        # Filter recipes
        filtered_recipes = search_recipes(RECIPES, search, cuisines, diets, tags)
        
        # Apply pagination
        total = len(filtered_recipes)
        paginated_recipes = filtered_recipes[offset:offset + limit]
        
        return jsonify({
            "results": paginated_recipes,
            "total": total,
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_recipe/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get a specific recipe by ID"""
    try:
        recipe = next((r for r in RECIPES if str(r.get('id', '')) == str(recipe_id)), None)
        if recipe:
            return jsonify(recipe)
        else:
            return jsonify({"error": "Recipe not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_recipe_by_id', methods=['GET'])
def get_recipe_by_id():
    """Get a specific recipe by ID (query parameter) - for frontend compatibility"""
    try:
        recipe_id = request.args.get('id')
        if not recipe_id:
            return jsonify({"error": "Recipe ID required"}), 400
        
        recipe = next((r for r in RECIPES if str(r.get('id', '')) == str(recipe_id)), None)
        if recipe:
            return jsonify(recipe)
        else:
            return jsonify({"error": "Recipe not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search_recipes', methods=['POST'])
def search_recipes_endpoint():
    """Enhanced search recipes with advanced filtering"""
    try:
        data = request.get_json() or {}
        
        search_term = data.get('search', '').strip()
        cuisines = data.get('cuisines', [])
        diets = data.get('diets', [])
        tags = data.get('tags', [])
        limit = data.get('limit', 20)
        offset = data.get('offset', 0)
        
        # Filter recipes
        filtered_recipes = search_recipes(RECIPES, search_term, cuisines, diets, tags)
        
        # Apply pagination
        total = len(filtered_recipes)
        paginated_recipes = filtered_recipes[offset:offset + limit]
        
        return jsonify({
            "results": paginated_recipes,
            "total": total,
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_cuisines', methods=['GET'])
def get_cuisines():
    """Get all available cuisines"""
    try:
        cuisines = set()
        for recipe in RECIPES:
            recipe_cuisines = recipe.get('cuisines', [])
            if isinstance(recipe_cuisines, str):
                recipe_cuisines = [recipe_cuisines]
            cuisines.update(recipe_cuisines)
        
        return jsonify({
            "cuisines": sorted(list(cuisines))
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_diets', methods=['GET'])
def get_diets():
    """Get all available diets"""
    try:
        diets = set()
        for recipe in RECIPES:
            recipe_diets = recipe.get('diets', [])
            if isinstance(recipe_diets, str):
                recipe_diets = [recipe_diets]
            diets.update(recipe_diets)
        
        return jsonify({
            "diets": sorted(list(diets))
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_tags', methods=['GET'])
def get_tags():
    """Get all available tags"""
    try:
        tags = set()
        for recipe in RECIPES:
            recipe_tags = recipe.get('tags', '')
            if recipe_tags:
                # Split tags by common separators
                tag_list = re.split(r'[,;|]', recipe_tags)
                tags.update([tag.strip() for tag in tag_list if tag.strip()])
        
        return jsonify({
            "tags": sorted(list(tags))
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload-recipes', methods=['POST'])
def upload_recipes():
    """Upload multiple recipes in batch"""
    try:
        data = request.get_json()
        if not data or 'recipes' not in data:
            return jsonify({"error": "No recipes provided"}), 400
        
        recipes_to_upload = data['recipes']
        batch_info = data.get('batch_info', {})
        
        uploaded_count = 0
        for recipe in recipes_to_upload:
            # Ensure recipe has required fields
            if 'id' not in recipe:
                recipe['id'] = str(len(RECIPES) + 1)
            
            # Add to recipes list
            RECIPES.append(recipe)
            uploaded_count += 1
        
        return jsonify({
            "message": f"Successfully uploaded {uploaded_count} recipes",
            "uploaded_count": uploaded_count,
            "total_recipes": len(RECIPES),
            "batch_info": batch_info
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/add-recipe', methods=['POST'])
def add_recipe():
    """Add a single recipe"""
    try:
        recipe = request.get_json()
        if not recipe:
            return jsonify({"error": "No recipe provided"}), 400
        
        # Ensure recipe has required fields
        if 'id' not in recipe:
            recipe['id'] = str(len(RECIPES) + 1)
        
        # Add to recipes list
        RECIPES.append(recipe)
        
        return jsonify({
            "message": "Recipe added successfully",
            "recipe_id": recipe['id'],
            "total_recipes": len(RECIPES)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clear-recipes', methods=['POST'])
def clear_recipes():
    """Clear all recipes (for testing)"""
    try:
        global RECIPES
        RECIPES.clear()
        return jsonify({
            "message": "All recipes cleared",
            "total_recipes": len(RECIPES)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Additional endpoints for frontend compatibility
@app.route('/api/reviews/local/<recipe_id>', methods=['GET'])
def get_recipe_reviews(recipe_id):
    """Get reviews for a recipe (placeholder - no reviews stored)"""
    try:
        # Check if recipe exists
        recipe = next((r for r in RECIPES if str(r.get('id', '')) == str(recipe_id)), None)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404
        
        # Return empty reviews for now
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews/local/<recipe_id>', methods=['POST'])
def add_recipe_review(recipe_id):
    """Add a review for a recipe (placeholder)"""
    try:
        # Check if recipe exists
        recipe = next((r for r in RECIPES if str(r.get('id', '')) == str(recipe_id)), None)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404
        
        # Placeholder - reviews not implemented yet
        return jsonify({"message": "Review functionality not implemented yet"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/meal-planner', methods=['POST'])
def meal_planner():
    """Meal planner endpoint (placeholder)"""
    try:
        return jsonify({"message": "Meal planner functionality not implemented yet"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai-meal-planner', methods=['POST'])
def ai_meal_planner():
    """AI meal planner endpoint (placeholder)"""
    try:
        return jsonify({"message": "AI meal planner functionality not implemented yet"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user-preferences', methods=['GET', 'POST', 'PUT'])
def user_preferences():
    """User preferences endpoint (placeholder)"""
    try:
        if request.method == 'GET':
            return jsonify({})
        else:
            return jsonify({"message": "User preferences functionality not implemented yet"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Non-API endpoints for frontend compatibility (without /api prefix)
@app.route('/get_recipe_by_id', methods=['GET'])
def get_recipe_by_id_no_api():
    """Get a specific recipe by ID (query parameter) - for frontend compatibility without /api"""
    try:
        recipe_id = request.args.get('id')
        if not recipe_id:
            return jsonify({"error": "Recipe ID required"}), 400
        
        recipe = next((r for r in RECIPES if str(r.get('id', '')) == str(recipe_id)), None)
        if recipe:
            return jsonify(recipe)
        else:
            return jsonify({"error": "Recipe not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_recipes', methods=['GET'])
def get_recipes_no_api():
    """Get recipes with enhanced filtering - for frontend compatibility without /api"""
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search', '').strip()
        cuisine = request.args.get('cuisine', '').strip()
        diet = request.args.get('diet', '').strip()
        tag = request.args.get('tag', '').strip()
        
        # Parse multiple values
        cuisines = [c.strip() for c in cuisine.split(',')] if cuisine else None
        diets = [d.strip() for d in diet.split(',')] if diet else None
        tags = [t.strip() for t in tag.split(',')] if tag else None
        
        # Filter recipes
        filtered_recipes = search_recipes(RECIPES, search, cuisines, diets, tags)
        
        # Apply pagination
        total = len(filtered_recipes)
        paginated_recipes = filtered_recipes[offset:offset + limit]
        
        return jsonify({
            "results": paginated_recipes,
            "total": total,
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reviews/local/<recipe_id>', methods=['GET', 'POST'])
def get_recipe_reviews_no_api(recipe_id):
    """Get reviews for a recipe (placeholder) - for frontend compatibility without /api"""
    try:
        # Check if recipe exists
        recipe = next((r for r in RECIPES if str(r.get('id', '')) == str(recipe_id)), None)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404
        
        if request.method == 'GET':
            # Return empty reviews for now
            return jsonify([])
        else:
            # Placeholder - reviews not implemented yet
            return jsonify({"message": "Review functionality not implemented yet"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
