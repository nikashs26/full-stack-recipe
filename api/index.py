"""
Main Vercel API handler for the recipe app
This is a simplified Flask app wrapper for Vercel serverless functions
"""

import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add backend to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Import your existing Flask app
try:
    from app_railway import app as flask_app
    print("✅ Successfully imported Flask app")
except ImportError as e:
    print(f"❌ Error importing Flask app: {e}")
    # Create a minimal Flask app as fallback
    flask_app = Flask(__name__)
    CORS(flask_app)
    
    @flask_app.route('/')
    def health():
        return jsonify({"status": "error", "message": "Flask app not properly imported"})

# Export the Flask app for Vercel
app = flask_app

# Vercel expects the app to be available
if __name__ == "__main__":
    app.run(debug=True)