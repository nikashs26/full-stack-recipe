
from flask import jsonify, request
import time
from bson import ObjectId
import json
import sys

def register_diagnostic_routes(app, mongo_client, recipes_collection, folders_collection, mongo_available, mongo_uri, check_mongodb_dns):
    # Add a new route for direct testing of MongoDB connection
    @app.route("/test-mongodb", methods=["GET"])
    def test_mongodb():
        if not mongo_available:
            # Try to get more specific connection error information
            error_message = "MongoDB is not available. Check your connection string and make sure MongoDB is accessible."
            error_type = "Connection Error"
            
            # Check DNS resolution for more specific errors
            dns_check = check_mongodb_dns(mongo_uri)
            if not dns_check["success"]:
                error_type = "DNS Resolution Error"
                error_message = f"Could not resolve MongoDB hostname: {dns_check['message']}"
            
            return jsonify({
                "status": "error",
                "connected": False,
                "message": error_message,
                "error_type": error_type,
                "dns_check": dns_check
            }), 503
        
        try:
            # Verify connection by getting server stats
            if mongo_client:
                mongo_client.admin.command('ping')
                recipe_count = recipes_collection.count_documents({}) if recipes_collection else 0
                
                # Check if we can get sample data from the collection
                sample = []
                if recipes_collection and recipe_count > 0:
                    sample = list(recipes_collection.find().limit(3))
                    # Convert ObjectId to string for JSON serialization
                    for doc in sample:
                        if "_id" in doc and isinstance(doc["_id"], ObjectId):
                            doc["_id"] = str(doc["_id"])
                
                return jsonify({
                    "status": "success",
                    "connected": True,
                    "message": f"MongoDB is connected and operational. Found {recipe_count} recipes.",
                    "database": recipes_collection.database.name if recipes_collection else "unknown",
                    "collection": recipes_collection.name if recipes_collection else "unknown",
                    "recipeCount": recipe_count,
                    "sample": sample[:3],  # Just send a few samples to avoid large payloads
                    "connectionInfo": {
                        "host": mongo_client.address[0] if mongo_client.address else "unknown",
                        "port": mongo_client.address[1] if mongo_client.address else "unknown",
                    }
                })
            else:
                return jsonify({
                    "status": "error",
                    "connected": False,
                    "message": "MongoDB client is not initialized."
                }), 500
        
        except Exception as e:
            return jsonify({
                "status": "error",
                "connected": False,
                "message": f"Error testing MongoDB connection: {str(e)}"
            }), 500

    # Add a new route for adding a test recipe
    @app.route("/add-test-recipe", methods=["POST"])
    def add_test_recipe():
        if not mongo_available:
            return jsonify({
                "status": "error",
                "success": False,
                "message": "MongoDB is not available."
            }), 503
        
        try:
            # Create a test recipe with timestamp to ensure uniqueness
            timestamp = int(time.time())
            test_recipe = {
                "id": f"test-{timestamp}",
                "title": f"Test Recipe {timestamp}",
                "name": f"Test Recipe {timestamp}",
                "cuisine": "Test",
                "cuisines": ["Test"],
                "dietaryRestrictions": ["test"],
                "diets": ["test"],
                "ingredients": ["test ingredient 1", "test ingredient 2"],
                "instructions": ["Step 1: Test", "Step 2: Complete"],
                "image": "https://via.placeholder.com/300",
                "ratings": [5],
                "createdAt": timestamp
            }
            
            # Try to insert the recipe
            result = recipes_collection.insert_one(test_recipe)
            
            return jsonify({
                "status": "success",
                "success": True,
                "message": "Test recipe added successfully",
                "recipeId": str(result.inserted_id),
                "recipe": {
                    **test_recipe,
                    "_id": str(result.inserted_id)
                }
            })
        
        except Exception as e:
            return jsonify({
                "status": "error",
                "success": False,
                "message": f"Error adding test recipe: {str(e)}"
            }), 500

    # Add a new route for MongoDB diagnostic information
    @app.route("/mongodb-diagnostics", methods=["GET"])
    def mongodb_diagnostics():
        uri = mongo_uri or "No URI specified"
        
        # Mask password in URI for security
        masked_uri = uri
        if "@" in masked_uri and ":" in masked_uri:
            prefix = masked_uri.split("@")[0]
            if ":" in prefix:
                username = prefix.split(":")[-2].split("/")[-1]
                masked_uri = masked_uri.replace(prefix, f"{username}:****")

        try:
            # Import pymongo for version check
            import pymongo
            pymongo_version = pymongo.__version__
        except ImportError:
            pymongo_version = "Not installed"
            
        # Basic diagnostics
        diagnostics = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mongodb_available": mongo_available,
            "connection_string": {
                "provided": bool(mongo_uri),
                "masked_uri": masked_uri,
                "type": "mongodb+srv" if uri and "mongodb+srv" in uri else "mongodb" if uri and "mongodb://" in uri else "unknown"
            },
            "dns_check": check_mongodb_dns(mongo_uri),
            "pymongo_version": pymongo_version,
            "python_version": sys.version,
            "platform": sys.platform
        }
        
        # Add collection info if available
        if mongo_available and recipes_collection:
            try:
                diagnostics["database_info"] = {
                    "database_name": recipes_collection.database.name,
                    "collection_name": recipes_collection.name,
                    "document_count": recipes_collection.count_documents({}),
                    "indexes": list(recipes_collection.list_indexes())
                }
            except Exception as e:
                diagnostics["database_info"] = {"error": str(e)}
        
        return jsonify(diagnostics)
