from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["*"])

# Simple recipe data for testing
RECIPES = [
    {
        "id": "1",
        "title": "Chicken Curry",
        "cuisine": "indian",
        "cuisines": ["indian"],
        "diets": ["gluten-free"],
        "ingredients": [
            {"name": "Chicken", "amount": "500g"},
            {"name": "Onions", "amount": "2 medium"},
            {"name": "Tomatoes", "amount": "3 medium"},
            {"name": "Ginger", "amount": "1 inch"},
            {"name": "Garlic", "amount": "4 cloves"},
            {"name": "Curry Powder", "amount": "2 tbsp"},
            {"name": "Coconut Milk", "amount": "400ml"},
            {"name": "Oil", "amount": "2 tbsp"},
            {"name": "Salt", "amount": "to taste"}
        ],
        "instructions": [
            "Heat oil in a large pan",
            "Add chopped onions and cook until golden",
            "Add ginger and garlic, cook for 1 minute",
            "Add chicken and cook until browned",
            "Add curry powder and cook for 1 minute",
            "Add tomatoes and cook until soft",
            "Add coconut milk and simmer for 20 minutes",
            "Season with salt and serve"
        ],
        "calories": 350.0,
        "protein": 25.0,
        "carbs": 15.0,
        "fat": 20.0,
        "image": "https://example.com/chicken-curry.jpg",
        "description": "A delicious and aromatic chicken curry"
    },
    {
        "id": "2",
        "title": "Pasta Carbonara",
        "cuisine": "italian",
        "cuisines": ["italian"],
        "diets": ["vegetarian"],
        "ingredients": [
            {"name": "Pasta", "amount": "400g"},
            {"name": "Eggs", "amount": "4 large"},
            {"name": "Parmesan Cheese", "amount": "100g"},
            {"name": "Bacon", "amount": "200g"},
            {"name": "Black Pepper", "amount": "1 tsp"},
            {"name": "Salt", "amount": "to taste"}
        ],
        "instructions": [
            "Cook pasta according to package instructions",
            "Fry bacon until crispy",
            "Beat eggs with parmesan and black pepper",
            "Drain pasta and add to bacon pan",
            "Remove from heat and add egg mixture",
            "Toss quickly to create creamy sauce",
            "Serve immediately"
        ],
        "calories": 450.0,
        "protein": 20.0,
        "carbs": 45.0,
        "fat": 18.0,
        "image": "https://example.com/carbonara.jpg",
        "description": "Classic Italian pasta dish"
    }
]

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "Recipe app is running"
    })

@app.route('/api/get_recipes', methods=['GET'])
def get_recipes():
    """Get recipes with optional filtering"""
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search', '').lower()
        cuisine = request.args.get('cuisine', '').lower()
        diet = request.args.get('diet', '').lower()
        
        # Filter recipes
        filtered_recipes = RECIPES
        
        if search:
            filtered_recipes = [r for r in filtered_recipes if search in r['title'].lower()]
        
        if cuisine:
            filtered_recipes = [r for r in filtered_recipes if cuisine in [c.lower() for c in r['cuisines']]]
        
        if diet:
            filtered_recipes = [r for r in filtered_recipes if diet in [d.lower() for d in r['diets']]]
        
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
        recipe = next((r for r in RECIPES if r['id'] == recipe_id), None)
        if recipe:
            return jsonify(recipe)
        else:
            return jsonify({"error": "Recipe not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search_recipes', methods=['POST'])
def search_recipes():
    """Search recipes with advanced filtering"""
    try:
        data = request.get_json() or {}
        
        search_term = data.get('search', '').lower()
        cuisines = data.get('cuisines', [])
        diets = data.get('diets', [])
        limit = data.get('limit', 20)
        offset = data.get('offset', 0)
        
        # Filter recipes
        filtered_recipes = RECIPES
        
        if search_term:
            filtered_recipes = [r for r in filtered_recipes if search_term in r['title'].lower()]
        
        if cuisines:
            filtered_recipes = [r for r in filtered_recipes if any(c.lower() in [cu.lower() for cu in r['cuisines']] for c in cuisines)]
        
        if diets:
            filtered_recipes = [r for r in filtered_recipes if any(d.lower() in [di.lower() for di in r['diets']] for d in diets)]
        
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)