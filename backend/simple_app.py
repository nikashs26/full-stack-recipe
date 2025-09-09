from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["*"])

# Sample recipe data
SAMPLE_RECIPES = [
    {
        "id": "52961",
        "title": "Budino Di Ricotta",
        "cuisine": "Italian",
        "cuisines": ["italian"],
        "diets": "vegetarian",
        "ingredients": [
            {"name": "Ricotta", "measure": "500g", "original": "500g Ricotta"},
            {"name": "Eggs", "measure": "4 large", "original": "4 large Eggs"},
            {"name": "Flour", "measure": "3 tbs", "original": "3 tbs Flour"},
            {"name": "Sugar", "measure": "250g", "original": "250g Sugar"},
            {"name": "Cinnamon", "measure": "1 tsp", "original": "1 tsp Cinnamon"},
            {"name": "Grated Zest of 2 Lemons", "measure": "", "original": "Grated Zest of 2 Lemons"},
            {"name": "Dark Rum", "measure": "5 tbs", "original": "5 tbs Dark Rum"},
            {"name": "Icing Sugar", "measure": "sprinkling", "original": "sprinkling Icing Sugar"}
        ],
        "instructions": [
            "Mash the ricotta and beat well with the egg yolks, stir in the flour, sugar, cinnamon, grated lemon rind and the rum and mix well. You can do this in a food processor. Beat the egg whites until stiff, fold in and pour into a buttered and floured 25cm cake tin. Bake in the oven at 180ºC/160ºC fan/gas.",
            "For about.",
            "Minutes, or until it is firm. Serve hot or cold dusted with icing sugar."
        ],
        "calories": 350,
        "protein": 12,
        "carbs": 44,
        "fat": 14,
        "image": "https://www.themealdb.com/images/media/meals/1549542877.jpg"
    },
    {
        "id": "52772",
        "title": "Teriyaki Chicken Casserole",
        "cuisine": "Japanese",
        "cuisines": ["japanese"],
        "diets": "gluten free",
        "ingredients": [
            {"name": "Chicken Thighs", "measure": "6", "original": "6 Chicken Thighs"},
            {"name": "Soy Sauce", "measure": "1/2 cup", "original": "1/2 cup Soy Sauce"},
            {"name": "Brown Sugar", "measure": "1/2 cup", "original": "1/2 cup Brown Sugar"},
            {"name": "Garlic", "measure": "3 cloves", "original": "3 cloves Garlic"},
            {"name": "Ginger", "measure": "1 inch", "original": "1 inch Ginger"},
            {"name": "Rice", "measure": "2 cups", "original": "2 cups Rice"}
        ],
        "instructions": [
            "Preheat oven to 350°F. Place chicken thighs in a baking dish.",
            "Mix soy sauce, brown sugar, garlic, and ginger in a bowl.",
            "Pour sauce over chicken and bake for 45 minutes.",
            "Serve over rice."
        ],
        "calories": 420,
        "protein": 28,
        "carbs": 35,
        "fat": 18,
        "image": "https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg"
    },
    {
        "id": "52773",
        "title": "Beef and Mushroom Stew",
        "cuisine": "American",
        "cuisines": ["american"],
        "diets": "gluten free",
        "ingredients": [
            {"name": "Beef Chuck", "measure": "2 lbs", "original": "2 lbs Beef Chuck"},
            {"name": "Mushrooms", "measure": "1 lb", "original": "1 lb Mushrooms"},
            {"name": "Onions", "measure": "2 large", "original": "2 large Onions"},
            {"name": "Carrots", "measure": "4", "original": "4 Carrots"},
            {"name": "Beef Broth", "measure": "4 cups", "original": "4 cups Beef Broth"},
            {"name": "Red Wine", "measure": "1 cup", "original": "1 cup Red Wine"}
        ],
        "instructions": [
            "Cut beef into 1-inch cubes and season with salt and pepper.",
            "Brown beef in batches in a large pot over medium-high heat.",
            "Add onions and carrots, cook until softened.",
            "Add mushrooms, broth, and wine. Bring to a boil, then simmer for 2 hours.",
            "Serve hot with crusty bread."
        ],
        "calories": 380,
        "protein": 32,
        "carbs": 18,
        "fat": 22,
        "image": "https://www.themealdb.com/images/media/meals/1529444830.jpg"
    }
]

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "message": "Simple app is running"})

@app.route('/api/recipe-counts')
def recipe_counts():
    return jsonify({
        "status": "success",
        "data": {
            "total": len(SAMPLE_RECIPES),
            "valid": len(SAMPLE_RECIPES),
            "expired": 0
        }
    })

@app.route('/api/recipes')
def get_recipes():
    query = request.args.get('query', '').strip().lower()
    limit = int(request.args.get('limit', 20))
    
    # Filter recipes based on query
    if query:
        filtered_recipes = [
            recipe for recipe in SAMPLE_RECIPES
            if query in recipe['title'].lower() or 
               query in recipe['cuisine'].lower() or
               any(query in ing['name'].lower() for ing in recipe['ingredients'])
        ]
    else:
        filtered_recipes = SAMPLE_RECIPES
    
    # Apply limit
    filtered_recipes = filtered_recipes[:limit]
    
    return jsonify({
        "results": filtered_recipes,
        "total": len(filtered_recipes)
    })

@app.route('/api/recipes/cuisines')
def get_cuisines():
    cuisines = list(set(recipe['cuisine'].lower() for recipe in SAMPLE_RECIPES))
    return jsonify({"cuisines": cuisines})

@app.route('/get_recipe_by_id')
def get_recipe_by_id():
    recipe_id = request.args.get('id')
    if not recipe_id:
        return jsonify({"error": "Recipe ID required"}), 400
    
    recipe = next((r for r in SAMPLE_RECIPES if r['id'] == recipe_id), None)
    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404
    
    return jsonify(recipe)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
