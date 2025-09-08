#!/usr/bin/env python3
"""
Minimal Railway App for Testing
"""

from flask import Flask
from flask_cors import CORS
import os

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
cors = CORS(app, 
    origins=["*"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    supports_credentials=True
)

# Basic health check route
@app.route('/api/health')
def health_check():
    return {'status': 'healthy', 'message': 'Railway backend is running'}

# Basic recipes route
@app.route('/get_recipes')
def get_recipes():
    return {
        'recipes': [
            {'id': 1, 'title': 'Test Recipe 1', 'description': 'A test recipe'},
            {'id': 2, 'title': 'Test Recipe 2', 'description': 'Another test recipe'}
        ],
        'total': 2
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
