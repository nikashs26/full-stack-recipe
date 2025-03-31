
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import pymongo
import os
import json
from bson.objectid import ObjectId
from bson.json_util import dumps

app = Flask(__name__)
CORS(app)

# Spoonacular API Key - Replace with your actual key
SPOONACULAR_API_KEY = "01f12ed117584307b5cba262f43a8d49"  # ← Update this!
SPOONACULAR_URL = "https://api.spoonacular.com/recipes/complexSearch"

# MongoDB setup
# Make sure to install pymongo: pip install pymongo
try:
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = mongo_client["recipe_db"]
    recipes_collection = db["recipes"]
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection error: {e}")
    # Fallback to memory storage if MongoDB is not available
    in_memory_recipes = []

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

@app.route("/get_recipes", methods=["GET"])
def get_recipes():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # First check if we have recipes in MongoDB that match the query
    try:
        if 'recipes_collection' in globals():
            db_results = list(recipes_collection.find({"title": {"$regex": query, "$options": "i"}}))
            if db_results and len(db_results) > 0:
                print(f"Found {len(db_results)} recipes in database for query: {query}")
                return JSONEncoder().encode({"results": db_results})
    except Exception as e:
        print(f"Error querying MongoDB: {e}")
        # Continue to API if MongoDB query fails

    # If no results in DB or MongoDB not available, call the Spoonacular API
    params = {
        "query": query,
        "apiKey": SPOONACULAR_API_KEY,
        "number": 10,  # Limit to 10 results
        "addRecipeInformation": "true",
    }

    try:
        response = requests.get(SPOONACULAR_URL, params=params)
        
        # Check if content type is JSON
        if 'application/json' not in response.headers.get('Content-Type', ''):
            return jsonify({
                "error": f"API returned non-JSON response. Status: {response.status_code}",
                "message": response.text[:100] + "..." # Show part of the response for debugging
            }), 500
            
        response.raise_for_status()  # Raise an error for HTTP failures
        data = response.json()

        if "results" not in data:
            return jsonify({"error": "Invalid response from Spoonacular"}), 500

        # Store results in MongoDB for future queries
        try:
            if 'recipes_collection' in globals():
                for recipe in data["results"]:
                    # Check if recipe already exists in the database
                    existing = recipes_collection.find_one({"id": recipe["id"]})
                    if not existing:
                        recipes_collection.insert_one(recipe)
                print(f"Stored {len(data['results'])} recipes in MongoDB")
        except Exception as e:
            print(f"Error storing recipes in MongoDB: {e}")

        return jsonify(data)  # Send results to frontend

    except ValueError as e:  # JSON parsing error
        return jsonify({
            "error": "Failed to parse API response as JSON",
            "message": str(e),
            "response_text": response.text[:100] + "..." # Show part of the response
        }), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_recipe_by_id", methods=["GET"])
def get_recipe_by_id():
    recipe_id = request.args.get("id")
    if not recipe_id:
        return jsonify({"error": "Recipe ID is required"}), 400
    
    # First check if we have this recipe in MongoDB
    try:
        if 'recipes_collection' in globals():
            db_recipe = recipes_collection.find_one({"id": int(recipe_id)})
            if db_recipe:
                print(f"Found recipe {recipe_id} in database")
                return JSONEncoder().encode(db_recipe)
    except Exception as e:
        print(f"Error querying MongoDB for recipe {recipe_id}: {e}")
        # Continue to API if MongoDB query fails
    
    # If not in DB or MongoDB not available, call the Spoonacular API
    api_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY}
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Store in MongoDB for future queries
        try:
            if 'recipes_collection' in globals():
                existing = recipes_collection.find_one({"id": data["id"]})
                if not existing:
                    recipes_collection.insert_one(data)
                    print(f"Stored recipe {recipe_id} in MongoDB")
        except Exception as e:
            print(f"Error storing recipe {recipe_id} in MongoDB: {e}")
        
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route("/recipes", methods=["GET"])
def get_all_recipes():
    try:
        if 'recipes_collection' in globals():
            recipes = list(recipes_collection.find({}))
            return JSONEncoder().encode({"results": recipes})
        else:
            return jsonify({"results": in_memory_recipes})
    except Exception as e:
        return jsonify({"error": str(e), "results": []}), 500

@app.route("/recipes", methods=["POST"])
def add_recipe():
    recipe = request.json
    try:
        if 'recipes_collection' in globals():
            result = recipes_collection.insert_one(recipe)
            recipe['_id'] = str(result.inserted_id)
            return jsonify(recipe), 201
        else:
            recipe['_id'] = str(len(in_memory_recipes) + 1)
            in_memory_recipes.append(recipe)
            return jsonify(recipe), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/recipes/<recipe_id>", methods=["DELETE"])
def delete_recipe(recipe_id):
    try:
        if 'recipes_collection' in globals():
            result = recipes_collection.delete_one({"_id": ObjectId(recipe_id)})
            if result.deleted_count > 0:
                return jsonify({"message": "Recipe deleted"}), 200
            else:
                return jsonify({"error": "Recipe not found"}), 404
        else:
            global in_memory_recipes
            in_memory_recipes = [r for r in in_memory_recipes if r.get('_id') != recipe_id]
            return jsonify({"message": "Recipe deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
