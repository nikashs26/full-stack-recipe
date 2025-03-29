from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

# Spoonacular API Key (Replace with your actual key)
SPOONACULAR_API_KEY = "01f12ed117584307b5cba262f43a8d49"
SPOONACULAR_URL = "https://api.spoonacular.com/recipes/complexSearch"


@app.route("/get_recipes", methods=["GET"])
def get_recipes():
    
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    params = {
        "query": query,
        "apiKey": SPOONACULAR_API_KEY,
        "number": 10,
        "addRecipeInformation": "true",
    }

    try:
        response = requests.get(SPOONACULAR_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        print("Spoonacular Response:", data)  # Log response for debugging
        
        if "results" not in data:
            return jsonify({"error": "Invalid response from Spoonacular"}), 500

        return jsonify(data)

    except requests.exceptions.RequestException as e:
        print("API Error:", str(e))  # Log error
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)