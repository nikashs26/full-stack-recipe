
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY", "01f12ed117584307b5cba262f43a8d49")

@app.route("/recipes", methods=["GET"])
def get_recipes():
    query = request.args.get("query", "")
    if not query:
        return jsonify({"results": []})
    
    try:
        url = f"https://api.spoonacular.com/recipes/complexSearch?apiKey={SPOONACULAR_API_KEY}&query={query}&number=6"
        print(f"Calling Spoonacular API: {url}")
        response = requests.get(url)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            error_msg = f"API returned status code {response.status_code}"
            print(error_msg)
            print(response.text)
            return jsonify({"error": error_msg, "results": []}), 500
    except Exception as e:
        print(f"Exception during API call: {str(e)}")
        return jsonify({"error": str(e), "results": []}), 500

if __name__ == "__main__":
    app.run(debug=True)
