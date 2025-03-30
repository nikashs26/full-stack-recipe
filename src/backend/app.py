from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Spoonacular API Key - Replace with your actual key
SPOONACULAR_API_KEY = "01f12ed117584307b5cba262f43a8d49"  # ← Update this!
SPOONACULAR_URL = "https://api.spoonacular.com/recipes/complexSearch"

@app.route("/get_recipes", methods=["GET"])
def get_recipes():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

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

        return jsonify(data)  # Send results to frontend

    except ValueError as e:  # JSON parsing error
        return jsonify({
            "error": "Failed to parse API response as JSON",
            "message": str(e),
            "response_text": response.text[:100] + "..." # Show part of the response
        }), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)