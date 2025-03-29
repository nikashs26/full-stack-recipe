
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import time

app = Flask(__name__)
CORS(app)

# Get API key from environment variable with fallback
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY", "01f12ed117584307b5cba262f43a8d49")

@app.route("/recipes", methods=["GET"])
def get_recipes():
    query = request.args.get("query", "")
    if not query:
        print("Empty query parameter received")
        return jsonify({"results": []})
    
    try:
        url = f"https://api.spoonacular.com/recipes/complexSearch"
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "query": query,
            "number": 6,
            "addRecipeInformation": "true"  # Get more details
        }
        
        print(f"Calling Spoonacular API with query: {query}")
        
        # Add timeout to prevent hanging
        response = requests.get(url, params=params, timeout=8)
        
        print(f"API status code: {response.status_code}")
        print(f"API response headers: {response.headers}")
        
        # Log rate limit information if available
        if 'X-API-Quota-Used' in response.headers:
            print(f"API quota used: {response.headers['X-API-Quota-Used']}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"API returned {len(response_data.get('results', []))} results")
                
                # If we got valid results, return them
                if 'results' in response_data and response_data['results']:
                    print("Sample recipe name:", response_data['results'][0].get('title', 'No title'))
                    return jsonify(response_data)
                else:
                    # No results found in a valid response
                    print("API returned valid response but no results")
                    return jsonify({"results": []})
            except json.JSONDecodeError:
                print("API returned invalid JSON")
                print(f"Response content: {response.text[:500]}...")  # Log first 500 chars
                return jsonify({"error": "Invalid response from external API", "results": []}), 500
        
        elif response.status_code == 401 or response.status_code == 403:
            print("API key error or authentication issue")
            return jsonify({
                "error": "API key error. You may need to update your Spoonacular API key.", 
                "results": []
            }), response.status_code
        
        elif response.status_code == 429:
            print("API rate limit exceeded")
            return jsonify({
                "error": "API rate limit exceeded. Try again later.",
                "results": []
            }), 429
            
        else:
            error_msg = f"API returned unexpected status code {response.status_code}"
            print(error_msg)
            print(f"Response preview: {response.text[:200]}...")
            return jsonify({"error": error_msg, "results": []}), response.status_code
    
    except requests.exceptions.Timeout:
        print("API request timed out")
        return jsonify({"error": "External API request timed out", "results": []}), 504
    
    except requests.exceptions.ConnectionError:
        print("Connection error to external API")
        return jsonify({"error": "Could not connect to external recipe service", "results": []}), 502
    
    except Exception as e:
        print(f"Unexpected exception during API call: {str(e)}")
        return jsonify({"error": str(e), "results": []}), 500

if __name__ == "__main__":
    # Set debug=False for production
    app.run(debug=True)
