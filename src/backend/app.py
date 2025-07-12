
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
import os
import time
import sys
import json

# Import modules
from utils.db_utils import check_mongodb_dns, initialize_mongodb, add_seed_data
from routes.recipe_routes import register_recipe_routes
from routes.folder_routes import register_folder_routes
from routes.diagnostic_routes import register_diagnostic_routes

# Print Python version and path for debugging
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Load environment variables from .env file
load_dotenv('../info.env')

# Get MongoDB URI from environment variables
MONGO_URI = os.getenv("MONGO_URI")
MONGO_CONNECT_TIMEOUT_MS = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "5000"))
MONGO_RETRY_COUNT = int(os.getenv("MONGO_RETRY_COUNT", "3"))

if not MONGO_URI:
    print("No MongoDB URI found in environment variables")
    print("Please update the info.env file with your MongoDB URI")
else:
    print(f"Using MongoDB URI from environment variables: {MONGO_URI[:20]}...")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# In-memory storage as fallback if MongoDB is not available
in_memory_recipes = []

# Initialize MongoDB connection
mongo_client, recipes_collection, folders_collection, mongo_available = initialize_mongodb(
                MONGO_URI, 
    MONGO_CONNECT_TIMEOUT_MS, 
    MONGO_RETRY_COUNT
)
    
    # If connection successful, add seed data if needed
    if mongo_available and recipes_collection:
    add_seed_data(recipes_collection)
else:
    print("Using in-memory storage as fallback")

# Register routes
register_recipe_routes(app, recipes_collection, mongo_available, in_memory_recipes)
register_folder_routes(app, folders_collection, recipes_collection, mongo_available)
register_diagnostic_routes(app, mongo_client, recipes_collection, folders_collection, mongo_available, MONGO_URI, check_mongodb_dns)

if __name__ == "__main__":
    print("Starting Flask application...")
    # Run the Flask app on 0.0.0.0 to make it accessible from other devices on the network
    app.run(host='0.0.0.0', debug=True, port=5000)
