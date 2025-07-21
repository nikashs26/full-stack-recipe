from flask import Blueprint, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create blueprint
health_bp = Blueprint('health', __name__)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('MONGO_DB_NAME', 'recipe_app')

@health_bp.route('/api/health/mongodb', methods=['GET'])
def check_mongodb():
    """Check MongoDB connection status"""
    try:
        # Try to connect to MongoDB
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # The ismaster command is cheap and does not require auth
        client.admin.command('ismaster')
        
        # If we got here, connection was successful
        return jsonify({
            'status': 'success',
            'message': 'MongoDB connection successful',
            'mongodb': {
                'connected': True,
                'database': DB_NAME,
                'server': MONGO_URI
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'MongoDB connection failed',
            'error': str(e),
            'mongodb': {
                'connected': False,
                'database': DB_NAME,
                'server': MONGO_URI
            }
        }), 500

@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """General health check endpoint"""
    return jsonify({
        'status': 'up',
        'services': {
            'mongodb': '/api/health/mongodb'
        }
    }), 200
