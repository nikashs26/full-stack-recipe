"""
Simple Recipe App - Just get recipes working
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json

# Simple Flask app
app = Flask(__name__)
CORS(app)

# Simple in-memory recipe storage for testing
SAMPLE_RECIPES = [
    {
        "id": "1",
        "title": "Spaghetti Carbonara",
        "description": "Classic Italian pasta dish with eggs, cheese, and pancetta",
        "ingredients": ["spaghetti", "eggs", "parmesan cheese", "pancetta", "black pepper"],
        "instructions": ["Cook pasta", "Mix eggs and cheese", "Combine with pancetta", "Serve hot"],
        "prepTime": "30 minutes",
        "servings": 4,
        "cuisine": "Italian"
    },
    {
        "id": "2", 
        "title": "Chicken Stir Fry",
        "description": "Quick and healthy chicken with vegetables",
        "ingredients": ["chicken breast", "broccoli", "bell peppers", "soy sauce", "ginger"],
        "instructions": ["Cut chicken", "Heat oil", "Cook chicken", "Add vegetables", "Season and serve"],
        "prepTime": "20 minutes",
        "servings": 3,
        "cuisine": "Asian"
    },
    {
        "id": "3",
        "title": "Caesar Salad",
        "description": "Fresh romaine lettuce with classic Caesar dressing",
        "ingredients": ["romaine lettuce", "croutons", "parmesan cheese", "caesar dressing"],
        "instructions": ["Wash lettuce", "Add dressing", "Top with croutons and cheese"],
        "prepTime": "10 minutes", 
        "servings": 2,
        "cuisine": "American"
    }
]

@app.route('/api/health')
def health():
    return {"status": "healthy", "message": "Simple recipe app running"}

@app.route('/api/recipes')
def get_recipes():
    """Get all recipes"""
    return jsonify({
        "recipes": SAMPLE_RECIPES,
        "total": len(SAMPLE_RECIPES)
    })

@app.route('/api/recipes/<recipe_id>')
def get_recipe(recipe_id):
    """Get a specific recipe"""
    recipe = next((r for r in SAMPLE_RECIPES if r["id"] == recipe_id), None)
    if recipe:
        return jsonify(recipe)
    return jsonify({"error": "Recipe not found"}), 404

@app.route('/api/recipes/search')
def search_recipes():
    """Search recipes by title or ingredient"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({"recipes": SAMPLE_RECIPES})
    
    # Simple search
    filtered_recipes = []
    for recipe in SAMPLE_RECIPES:
        if (query in recipe["title"].lower() or 
            query in recipe["description"].lower() or
            any(query in ingredient.lower() for ingredient in recipe["ingredients"])):
            filtered_recipes.append(recipe)
    
    return jsonify({
        "recipes": filtered_recipes,
        "total": len(filtered_recipes),
        "query": query
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting simple recipe app on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
