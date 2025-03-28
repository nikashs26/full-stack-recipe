from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

@app.route("/recipes", methods=["GET"])
def get_recipes():
    query = request.args.get("query", "")
    url = f"https://api.spoonacular.com/recipes/complexSearch?apiKey=01f12ed117584307b5cba262f43a8d49&query={query}&number=5"
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch recipes"}), 500

if __name__ == "__main__":
    app.run(debug=True)